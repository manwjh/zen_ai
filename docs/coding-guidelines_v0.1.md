# ZenAi Coding Guidelines v0.1

## 1. Configuration Management

### 1.1 Strict Configuration Principle

**Core Rule**: All configuration parameters MUST be explicitly defined in their designated configuration sources. No hardcoded values, no default values, no fallback mechanisms.

### 1.2 Configuration Sources

1. **config.yml**: System behavior parameters (paths, thresholds, rules)
2. **Environment variables**: Secrets and deployment-specific settings (API keys, URLs)

### 1.3 Implementation Rules

#### DO NOT: Use default values or fallbacks

```python
# BAD: Using default values
@dataclass
class Config:
    max_tokens: int = 100  # ❌ No default values

# BAD: Using fallback parameters
value = data.get("key", "default")  # ❌ No fallbacks
```

#### DO: Fail immediately on missing parameters

```python
# GOOD: No default values
@dataclass
class Config:
    max_tokens: int  # ✅ Required parameter

# GOOD: Strict access with immediate failure
value = data["key"]  # ✅ KeyError if missing

# GOOD: Explicit validation
if "key" not in data:
    raise KeyError(f"Missing required parameter: key")
value = data["key"]
```

### 1.4 Configuration Loading Pattern

**Reference Implementation**: `src/llm/config.py` and `src/config/loader.py`

```python
def load_config(config_path: str) -> Config:
    """
    Load configuration strictly.
    
    Raises:
        FileNotFoundError: If config file does not exist
        KeyError: If required section is missing
        TypeError: If required parameter is missing
    """
    # 1. Check file existence
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # 2. Load YAML
    with open(config_path) as f:
        data = yaml.safe_load(f)
    
    if data is None:
        raise ValueError("Configuration file is empty")
    
    # 3. Check required sections
    required_sections = ["paths", "scheduler", "initial_policy"]
    missing = [s for s in required_sections if s not in data]
    if missing:
        raise KeyError(f"Missing required sections: {missing}")
    
    # 4. Build config objects strictly
    return Config(
        paths=_load_paths(data["paths"]),  # No fallback
        scheduler=_load_scheduler(data["scheduler"]),
        # ...
    )

def _load_paths(data: dict) -> PathConfig:
    """Load path configuration strictly"""
    # Check all required parameters
    required = ["data_dir", "database", "reports_dir"]
    missing = [p for p in required if p not in data]
    if missing:
        raise TypeError(f"Missing required parameters in 'paths': {missing}")
    
    # Access directly without fallbacks
    return PathConfig(
        data_dir=data["data_dir"],
        database=data["database"],
        reports_dir=data["reports_dir"],
    )
```

### 1.5 Error Messages

Error messages MUST be clear and actionable:

```python
# GOOD: Clear error message
raise FileNotFoundError(
    f"Configuration file not found: {config_path}. "
    "All configuration must be explicitly defined in config.yml."
)

# GOOD: Specific missing parameters
raise TypeError(
    f"Missing required parameters in 'scheduler' section: "
    f"{', '.join(missing)}. "
    "All parameters must be explicitly defined in config.yml."
)
```

## 2. Architecture Principles

### 2.1 Fail Fast

- Validate all inputs at system boundaries
- Fail immediately on invalid state or missing requirements
- Never silently ignore errors or use fallback values

### 2.2 Explicit Over Implicit

- Make all assumptions explicit
- No magic defaults
- No implicit conversions or coercions
- Configuration must be complete and visible

### 2.3 Happy Path First

- Design for the normal, successful execution path
- Handle edge cases explicitly only when necessary
- Don't add complexity for "just in case" scenarios

## 3. Code Style

### 3.1 Language

- All code, comments, documentation: English only
- Use clear, explicit naming over abbreviations
- Keep tone concise and engineering-focused

### 3.2 Error Handling

```python
# GOOD: Explicit error handling
try:
    config = load_config("config.yml")
except FileNotFoundError as e:
    logger.error(f"Failed to load config: {e}")
    sys.exit(1)

# BAD: Silent fallback
try:
    config = load_config("config.yml")
except FileNotFoundError:
    config = get_default_config()  # ❌ No fallbacks
```

### 3.3 Type Annotations

- Use type hints for all function signatures
- Use dataclasses for configuration objects
- Mark configuration objects as `frozen=True` for immutability

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # ✅ Immutable
class Config:
    max_tokens: int  # ✅ No default
    temperature: float
    
def load_config(path: str) -> Config:  # ✅ Type hints
    ...
```

## 4. Testing

### 4.1 Configuration Tests

- Test that missing config file raises FileNotFoundError
- Test that missing sections raise KeyError
- Test that missing parameters raise TypeError
- Test that valid config loads successfully

```python
def test_missing_config_file():
    with pytest.raises(FileNotFoundError, match="not found"):
        load_config("nonexistent.yml")

def test_missing_required_parameter():
    # Create config missing a required parameter
    with pytest.raises(TypeError, match="Missing required parameters"):
        _load_paths({"data_dir": "data"})  # Missing database, reports_dir
```

## 5. Documentation

### 5.1 Docstrings

Include information about failure modes:

```python
def load_config(config_path: str) -> Config:
    """
    Load configuration from YAML file strictly.
    
    Args:
        config_path: Path to config.yml file
    
    Returns:
        Config object with all parameters
        
    Raises:
        FileNotFoundError: If config file does not exist
        KeyError: If required section is missing
        TypeError: If required parameter is missing
    """
```

### 5.2 Configuration Documentation

- Document all configuration parameters in config.yml with comments
- Specify valid ranges and types
- Provide examples but not defaults in code

## 6. Migration Strategy

When refactoring existing code to follow these guidelines:

1. **Remove default values** from dataclass definitions
2. **Replace `data.get(key, default)`** with strict `data["key"]` access
3. **Add parameter validation** before creating config objects
4. **Update error handling** to expect and handle config exceptions
5. **Update tests** to verify strict behavior
6. **Update documentation** to reflect new behavior

## 7. Summary

**Configuration Philosophy**: 
- Explicit configuration is better than implicit defaults
- Fast failure is better than silent fallback
- Clear errors are better than mysterious behavior
- Complete configuration is better than partial with defaults

This ensures:
- **Predictability**: System behavior is always explicit
- **Debuggability**: Missing config immediately identified
- **Maintainability**: No hidden defaults to discover
- **Reliability**: No silent fallbacks masking issues
