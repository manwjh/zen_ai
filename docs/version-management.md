# Version Management Guide / 版本管理指南

## Overview / 概述

ZenAi now has a comprehensive version management system that tracks both:
1. **Software versions** (e.g., 0.1.0) - Overall system releases
2. **Prompt versions** (e.g., v1, v2, v3) - Internal prompt evolution

ZenAi 现在有完善的版本管理系统，追踪两种版本：
1. **软件版本**（如 0.1.0）- 整体系统发布版本
2. **提示词版本**（如 v1, v2, v3）- 内部提示词演化版本

---

## Software Versioning / 软件版本管理

### Version Format / 版本格式

We follow [Semantic Versioning 2.0.0](https://semver.org/):

我们遵循[语义化版本 2.0.0](https://semver.org/lang/zh-CN/)规范：

```
MAJOR.MINOR.PATCH
主版本号.次版本号.修订号
```

- **MAJOR** (主版本号): Incompatible API changes / 不兼容的 API 变更
- **MINOR** (次版本号): New features, backward compatible / 新功能，向后兼容
- **PATCH** (修订号): Bug fixes, backward compatible / Bug 修复，向后兼容

### Current Version / 当前版本

The current software version is defined in `src/__init__.py`:

当前软件版本定义在 `src/__init__.py` 中：

```python
__version__ = "0.1.0"
```

### Version Files / 版本文件

- **`src/__init__.py`** - Python package version definition  
  Python 包版本定义
- **`pyproject.toml`** - Project metadata and build configuration  
  项目元数据和构建配置
- **`CHANGELOG.md`** - Detailed version history  
  详细的版本历史

---

## Checking Version / 查看版本

### In Python Code / 在 Python 代码中

```python
from src import __version__
print(f"ZenAi version: {__version__}")
```

### Via API / 通过 API

```bash
# Root endpoint
curl http://localhost:8000/
# Returns: {"service": "ZenAi Orator API", "version": "0.1.0", ...}

# Health endpoint
curl http://localhost:8000/health
# Returns: {"status": "healthy", "version": "0.1.0", ...}

# Status endpoint
curl http://localhost:8000/status
# Returns: {"system_version": "0.1.0", "prompt_version": 1, ...}
```

### Via Admin Tool / 通过管理工具

```bash
python -m src.admin status
# Displays:
# System Version: 0.1.0
# Prompt Version: 1
# ...
```

---

## Updating Version / 更新版本

### When to Bump Version / 何时更新版本

**PATCH** (修订号 0.1.X):
- Bug fixes / Bug 修复
- Performance improvements / 性能改进
- Documentation updates / 文档更新
- Minor refactoring / 小型重构

**MINOR** (次版本号 0.X.0):
- New features / 新功能
- New API endpoints / 新 API 端点
- New metrics or algorithms / 新指标或算法
- Deprecations (with backward compatibility) / 弃用功能（保持向后兼容）

**MAJOR** (主版本号 X.0.0):
- Breaking API changes / 破坏性 API 变更
- Major architecture changes / 主要架构变更
- Incompatible database schema changes / 不兼容的数据库模式变更
- Removal of deprecated features / 移除已弃用的功能

### Update Process / 更新流程

1. **Update version in `src/__init__.py`**:
   ```python
   __version__ = "0.2.0"  # New version
   ```

2. **Update version in `pyproject.toml`**:
   ```toml
   [project]
   version = "0.2.0"
   ```

3. **Update `CHANGELOG.md`**:
   ```markdown
   ## [0.2.0] - 2026-01-XX
   
   ### Added
   - New feature X
   - New endpoint Y
   
   ### Fixed
   - Bug fix Z
   ```

4. **Update `README.md`** (if needed):
   ```markdown
   **Current Version**: `0.2.0`
   ```

5. **Commit changes**:
   ```bash
   git add src/__init__.py pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 0.2.0"
   ```

6. **Create Git tag**:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

---

## Prompt Versioning / 提示词版本管理

### Overview / 概述

Separate from software versions, ZenAi tracks **prompt versions** internally.
Each time the system evolves its prompt, a new version is created.

与软件版本分开，ZenAi 在内部追踪**提示词版本**。
每次系统演化提示词时，都会创建一个新版本。

### Viewing Prompt History / 查看提示词历史

```bash
# View all prompt versions
python -m src.admin prompts

# View iteration history with prompt versions
python -m src.admin history --limit 10
```

### Rollback / 回滚

```bash
# Rollback to previous prompt version
python -m src.admin rollback

# Rollback to specific prompt version
python -m src.admin rollback --version 5
```

---

## Release Process / 发布流程

### Pre-release Checklist / 发布前检查清单

- [ ] All tests pass / 所有测试通过
- [ ] Documentation updated / 文档已更新
- [ ] CHANGELOG.md updated / 更新日志已更新
- [ ] Version bumped in all files / 所有文件中的版本已更新
- [ ] No linter errors / 无 linter 错误

### Creating a Release / 创建发布

1. **Prepare release branch**:
   ```bash
   git checkout -b release/0.2.0
   ```

2. **Update version** (see "Update Process" above)

3. **Test thoroughly**:
   ```bash
   cd zen_ai
   python -m pytest tests/
   ./run_full_test.sh
   ```

4. **Merge to main**:
   ```bash
   git checkout main
   git merge release/0.2.0
   ```

5. **Tag release**:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0: [Brief description]"
   git push origin main --tags
   ```

6. **Deploy** (if applicable):
   ```bash
   ./deploy-backend.sh [server-ip]
   ```

---

## Version History / 版本历史

See [CHANGELOG.md](../CHANGELOG.md) for complete version history.

查看 [CHANGELOG.md](../CHANGELOG.md) 了解完整的版本历史。

---

## Best Practices / 最佳实践

### For Developers / 给开发者

1. **Always update CHANGELOG.md** when making changes  
   修改代码时务必更新 CHANGELOG.md

2. **Follow semantic versioning** strictly  
   严格遵循语义化版本规范

3. **Test before bumping version**  
   更新版本前进行测试

4. **Tag releases** in Git  
   在 Git 中标记发布版本

5. **Keep version files synchronized**  
   保持版本文件同步

### For Users / 给用户

1. **Check version compatibility** before updating  
   更新前检查版本兼容性

2. **Read CHANGELOG.md** to understand what changed  
   阅读 CHANGELOG.md 了解变更内容

3. **Backup database** before major version upgrades  
   主版本升级前备份数据库

4. **Use version-specific documentation**  
   使用对应版本的文档

---

## FAQ / 常见问题

### Q: What's the difference between software version and prompt version?

**A:** Software version (e.g., 0.1.0) tracks the overall system code releases.
Prompt version (e.g., v1, v2) tracks the internal prompt evolution within a running system.

软件版本（如 0.1.0）追踪整体系统代码发布。
提示词版本（如 v1, v2）追踪运行系统内部的提示词演化。

### Q: How often should we bump the version?

**A:** Bump PATCH for every bug fix or minor improvement. Bump MINOR for new features.
Bump MAJOR only when there are breaking changes.

每次 bug 修复或小改进更新 PATCH 版本。新功能更新 MINOR 版本。
只有破坏性变更才更新 MAJOR 版本。

### Q: Can I check version from the API?

**A:** Yes! All API endpoints include version information:
- `/` - Root endpoint shows version
- `/health` - Health check shows version
- `/status` - Status endpoint shows both system and prompt version

可以！所有 API 端点都包含版本信息。

### Q: What happens to prompt versions during rollback?

**A:** Prompt versions are preserved in history. Rollback changes the "current" version
but doesn't delete history. You can always view all past versions.

提示词版本历史会被保留。回滚改变"当前"版本但不删除历史。
你可以随时查看所有过去的版本。

---

## Related Documentation / 相关文档

- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [README.md](../README.md) - Main documentation
- [Design Specification](design-spec_v0.1.md) - System design
- [Admin Tool Guide](user-guide_v0.1.md) - Admin commands

---

**Last Updated**: 2026-01-19  
**Document Version**: 1.0
