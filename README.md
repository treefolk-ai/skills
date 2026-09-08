# Treefolk Skills

Treefolk AI 的个人 AI 工作流库，把反复出现的用户目标沉淀为有明确结果、安全默认值和验证方式的可复用 Skill。

## 产品方向

`core` 支撑整个工作流；产品主循环是 `think → make → share → learn`。

| 方向 | 负责什么 | 当前能力 |
| --- | --- | --- |
| `core` 基础 | 提供跨环节复用的基础工作流与通用工具 | [`$code-craft`](code-craft/SKILL.md) 以跨语言的可读性、失败路径和模块边界规范构建代码；[`$repo`](repo/SKILL.md) 完成项目仓库的首次安全发布；[`$push`](push/SKILL.md) 交付一次完整改动；[`$pr`](pr/SKILL.md) 创建或复用已验证的 PR；[`$to-mmd`](to-mmd/SKILL.md) 转换为可编辑的 Mermaid 源码 |
| `think` 思考 | 把信息和不确定性变成可审阅的决定或计划 | [`$todo`](todo/SKILL.md) 从本地任务文档中选出一个有文档依据的下一步 |
| `make` 制作 | 把意图变成可使用、可检查的成果 | [`$ui-to-desc`](ui-to-desc/SKILL.md) 把多轮 UI 证据整理成组件设计描述；[`$context-shrink`](context-shrink/SKILL.md) 在保持行为不变的前提下缩小指定源码范围的维护上下文；[`$seo`](seo/SKILL.md) 优化搜索入口、抓取索引与元信息；[`$geo`](geo/SKILL.md) 核实 AI 回答所需的事实、来源与引用，改善可控内容 |
| `share` 分享 | 让完成的成果到达目标用户或环境，并产生可观察结果 | [`$deploy`](deploy/SKILL.md) 部署到一个明确的既有托管目标并验证线上结果 |
| `learn` 学习 | 把结果与反馈沉淀为以后可复用的知识 | 产品方向，暂无公开 Skill |

分类只用于理解产品地图，不影响 Skill 的安装和调用。每个 Skill 的完整工作流以对应的 `SKILL.md` 为准。

## 使用

在 Codex 中直接输入 `$skill-name`。会改变 Git、远端或部署状态的 `$repo`、`$push`、`$pr`、`$deploy` 必须显式调用；边界明确的 `$code-craft`、`$todo`、`$to-mmd`、`$ui-to-desc`、`$context-shrink`、`$seo`、`$geo` 也可以由 AI 根据描述选择。`$code-craft` 从实现开始约束一个明确代码结果，不套用固定语言或框架架构；`$context-shrink` 只在用户明确要求缩小维护上下文并给出仓库内目录后重组已有源码。二者都不会自动提交或推送。`$seo` 处理搜索发现与元信息，`$geo` 处理生成式回答的内容与引用证据；分别加 `audit` 可只读审查。两者可独立使用，不自动公开仓库、应用远端设置或发布。详见 [Skill 调用参与层级与启用策略](docs/skill-priority.md)。

## 安装

安装持续更新的 `main` 版本：

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh | bash -s -- --host codex
```

源码默认保存在 `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`，各 Skill 默认激活到 `${HOME}/.agents/skills`。安装器只负责首次安装，并拒绝覆盖已有源码目录。

从已有源码目录激活前，可先预览：

```sh
./setup --host codex --dry-run
./setup --host codex
```

删除源码目录前请先运行 `uninstall`。卸载前同样先预览；确认后移除 `--dry-run`：

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex --dry-run
```

使用 Grok 时改为 `--host grok`；它与 Codex 激活同一共享目录。目前仅 Codex 的高影响 Skill 调用元数据经过静态检查，尚无 Grok 专用适配器或真实宿主测试。其他宿主暂不声明支持。

## 安全与维护

- 安装使用 HTTPS，不需要 `sudo`，并在激活前校验源码。
- `setup` 与 `uninstall` 支持 dry-run，不覆盖冲突项，只移除能证明归属的链接。
- 有副作用的 Skill 会先检查状态，在歧义或覆盖风险下停止，并在完成后验证真实结果。
- 仓库检查证明包结构和安装场景，不等于所有 Skill 都通过了端到端或真实宿主测试。

产品设计见 [DESIGN.md](DESIGN.md)，维护规则见 [AGENTS.md](AGENTS.md)。

MIT License，见 [LICENSE](LICENSE)。
