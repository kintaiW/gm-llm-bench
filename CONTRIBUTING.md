# Contributing to GM-Bench

## 版本发布纪律

本项目遵循 [SemVer 2.0](https://semver.org/lang/zh-CN/)。**当前处于 `0.x` 阶段**，`minor` bump 允许引入破坏性变更，但必须在 `CHANGELOG.md` 的 `### Breaking` 段显式列出。

### Bump 规则

| 改动类型 | Bump | 示例 |
|---|---|---|
| bug fix、文案、日志、内部重构（用户行为无变化） | **patch** | 0.2.0 → 0.2.1 |
| 新增 CLI flag、新评测类别、评测输出追加字段 | **minor** | 0.2.0 → 0.3.0 |
| 删除 CLI flag、改已有评分逻辑、结果格式向后不兼容 | **major** | 0.2.0 → 1.0.0 |

### PR 标签约定

- `bump:patch` — 自动触发 patch release
- `bump:minor` — 自动触发 minor release
- `bump:major` — 人工确认后触发 major release

### 发布流程

1. 在 `CHANGELOG.md` 填写本次变更内容（`## [x.y.z] - YYYY-MM-DD` 段）
2. 合入 PR 到 `main`
3. 打 tag：`git tag v0.2.0 && git push --tags`
4. GitHub Actions `release.yml` 自动：回写 `pyproject.toml` 版本 → 构建 wheel → 版本自检（`gm-bench --version`）→ 发 GitHub Release

### 题库贡献

- 新题必须通过 `python scripts/validate_questions.py` 零错误
- `id` 续编不复用旧号
- C3 场景需覆盖 8 类等保三级系统之一
- 新标准条款题目需在 PR 描述中注明标准编号和章节

### 贡献要求

- Python 代码遵循 PEP 8，所有函数带 type annotation
- 提交信息格式：`fix: 修复 X`、`feat: 新增 Y`、`data: 新增 N 道题（类别）`
