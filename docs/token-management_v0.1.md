Token Management v0.1 / 令牌管理 v0.1

## Purpose / 目的

This project stores LLM credentials in environment variables and loads them at runtime.  
本项目使用环境变量保存 LLM 凭证，并在运行时读取。

No tokens are stored in source control or documentation.  
源码与文档中不保存任何令牌。

## Environment Variables / 环境变量

- `ZENAI_LLM_PROVIDER`: LLM provider identifier (example: `perfxcloud`).  
  `ZENAI_LLM_PROVIDER`：LLM 供应商标识（示例：`perfxcloud`）。
- `ZENAI_LLM_API_KEY`: API token for the provider.  
  `ZENAI_LLM_API_KEY`：供应商的 API 令牌。
- `ZENAI_LLM_BASE_URL`: Base URL for the provider API.  
  `ZENAI_LLM_BASE_URL`：供应商 API 的基础地址。
- `ZENAI_LLM_MODEL`: Model name or path.  
  `ZENAI_LLM_MODEL`：模型名称或路径。
- `ZENAI_LLM_MAX_CONTEXT_TOKENS`: Max context length (integer).  
  `ZENAI_LLM_MAX_CONTEXT_TOKENS`：最大上下文长度（整数）。

## Runtime Loading / 运行时读取

The runtime configuration loader reads these variables at startup and fails fast if any are missing or invalid.  
运行时配置加载器在启动时读取这些变量，缺失或无效会直接报错。

The loader implementation is in `src/llm_config.py`.  
加载器实现位于 `src/llm_config.py`。

## Developer Setup / 开发者设置

- Copy `env.example` to your local `.env` or set the variables in your shell.  
  将 `env.example` 复制为本地 `.env`，或在 shell 中设置这些变量。
- Never commit real tokens into the repository or documents.  
  不要将真实令牌提交到仓库或文档中。
