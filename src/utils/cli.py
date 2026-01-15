from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import tempfile

from ..config import load_config
from ..core.models import PromptPolicy
from ..core.prompt import render_prompt
from ..storage import ResonanceArchive
from ..trainer import ZenAiTrainer
from .data_io import load_interactions


def _split_interactions(interactions, split_ratio: float):
    split_index = max(1, int(len(interactions) * split_ratio))
    return interactions[:split_index], interactions[split_index:]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ZenAi offline iteration runner - test iteration logic without running the full system"
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to JSONL interaction data",
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.5,
        help="Ratio used for previous vs current interactions",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Database path (default: temporary in-memory database)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    
    # Setup database (use temporary if not specified)
    if args.db:
        db_path = Path(args.db)
    else:
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = Path(temp_db.name)
        print(f"Using temporary database: {db_path}")
    
    # Initialize archive
    archive = ResonanceArchive(db_path=db_path)
    
    # Create initial prompt
    initial_policy = PromptPolicy(
        max_output_tokens=config.initial_policy.max_output_tokens,
        refusal_threshold=config.initial_policy.refusal_threshold,
        perturbation_level=config.initial_policy.perturbation_level,
        temperature=config.initial_policy.temperature,
    )
    archive.save_prompt(
        version=1,
        prompt_text=render_prompt(initial_policy),
        policy=initial_policy.to_dict(),
    )
    
    # Initialize Trainer
    trainer = ZenAiTrainer.from_config(archive, config)
    
    # Load and split interactions
    interactions = load_interactions(Path(args.data))
    previous, current = _split_interactions(interactions, args.split_ratio)
    
    print(f"\n{'='*60}")
    print("ZenAi Offline Iteration Runner")
    print(f"{'='*60}")
    print(f"Data file: {args.data}")
    print(f"Total interactions: {len(interactions)}")
    print(f"Previous: {len(previous)}, Current: {len(current)}")
    print(f"{'='*60}\n")
    
    # Store interactions in archive
    # First, store previous interactions in iteration 0
    if previous:
        prev_iteration_id = archive.create_iteration(
            start_time=datetime.utcnow(),
            prompt_version=1,
        )
        for interaction in previous:
            archive.record_interaction(
                user_input=interaction.user_input,
                response_text=interaction.response_text,
                feedback=interaction.feedback,
                refusal=interaction.refusal,
                iteration_id=prev_iteration_id,
            )
    
    # Store current interactions (unassigned, for the test iteration)
    start_time = datetime.utcnow()
    for interaction in current:
        archive.record_interaction(
            user_input=interaction.user_input,
            response_text=interaction.response_text,
            feedback=interaction.feedback,
            refusal=interaction.refusal,
            iteration_id=None,  # Unassigned
        )
    
    # Create iteration
    iteration_id = archive.create_iteration(
        start_time=start_time,
        prompt_version=1,
    )
    
    # Assign current interactions to this iteration
    unassigned = archive.load_unassigned_interactions()
    archive.assign_interactions_to_iteration(
        [i for i in range(len(previous) + 1, len(previous) + len(current) + 1)],
        iteration_id,
    )
    
    # Run iteration
    result = trainer.run_iteration_cycle(
        iteration_id=iteration_id,
        start_time=start_time,
        end_time=datetime.utcnow(),
    )
    
    # Complete iteration
    archive.complete_iteration(
        iteration_id=iteration_id,
        end_time=datetime.utcnow(),
        total_interactions=len(current),
        state=result.state.value,
        metrics=result.metrics.to_dict(),
    )
    
    # Print results
    print(f"\n{'='*60}")
    print("Iteration Results")
    print(f"{'='*60}")
    print(f"State: {result.state.value}")
    print(f"\nMetrics:")
    print(f"  Total responses: {result.metrics.total_responses}")
    print(f"  Resonance ratio: {result.metrics.resonance_ratio:.3f}")
    print(f"  Rejection density: {result.metrics.rejection_density:.3f}")
    print(f"  Response length drift: {result.metrics.response_length_drift:.3f}")
    print(f"  Refusal frequency: {result.metrics.refusal_frequency:.3f}")
    print(f"  Semantic collapse index: {result.metrics.semantic_collapse_index:.3f}")
    print(f"  Average response length: {result.metrics.average_response_length:.2f}")
    
    if result.evolution_actions:
        print(f"\nEvolution Actions:")
        for action in result.evolution_actions:
            print(f"  - {action.value}")
    else:
        print(f"\nNo evolution actions (system may be frozen)")
    
    if result.new_prompt_version:
        print(f"\nNew prompt version: {result.new_prompt_version}")
        new_prompt = archive.get_latest_prompt()
        if new_prompt:
            print(f"New policy:")
            for key, value in new_prompt.policy.items():
                print(f"  {key}: {value}")
    
    print(f"{'='*60}\n")
    
    # Cleanup temporary database if used
    if not args.db:
        db_path.unlink()
        print(f"Temporary database cleaned up")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
