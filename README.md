# Treefolk Skills

Treefolk AI 的个人 AI 工作流库，把反复出现的用户目标沉淀为有明确结果、安全默认值和验证方式的可复用 Skill。

## 产品方向

按你现在想完成的事，分为 `think → make → share` 三类。

| 方向 | 负责什么 | 当前能力 |
| --- | --- | --- |
| `think` 理清与接续 | 决定现在做什么，找回项目进展 | [`$todo`](skills/todo/SKILL.md) 从任务文档选出一个下一步；[`$human-in-the-loop`](skills/human-in-the-loop/SKILL.md) 用人和 AI 共用的证据接上项目，保留真实进展与人工反馈 |
| `make` 制作与改进 | 把成果做出来，或者改好 | [`$code-craft`](skills/code-craft/SKILL.md) 构建可读、可维护的代码；[`$context-shrink`](skills/context-shrink/SKILL.md) 保持行为并简化源码；[`$ui-to-desc`](skills/ui-to-desc/SKILL.md) 整理组件设计描述；[`$to-mmd`](skills/to-mmd/SKILL.md) 生成 Mermaid 源码；[`$seo`](skills/seo/SKILL.md) 改善搜索发现；[`$geo`](skills/geo/SKILL.md) 改善生成式回答的内容与证据 |
| `share` 交付与发布 | 把成果交付到仓库或运行环境 | [`$repo`](skills/repo/SKILL.md) 首次发布仓库；[`$push`](skills/push/SKILL.md) 交付一次完整改动；[`$pr`](skills/pr/SKILL.md) 创建或复用已验证的 PR；[`$deploy`](skills/deploy/SKILL.md) 部署到既有目标并验证线上结果 |

分类只用于理解产品地图，不影响 Skill 的安装和调用。每个 Skill 的完整工作流以对应的 `SKILL.md` 为准。

## 使用

在 Codex 中直接输入 `$skill-name`。会改变 Git、远端或部署状态的 `$repo`、`$push`、`$pr`、`$deploy` 必须显式调用；边界明确的 `$code-craft`、`$todo`、`$human-in-the-loop`、`$to-mmd`、`$ui-to-desc`、`$context-shrink`、`$seo`、`$geo` 也可以由 AI 根据描述选择。`$code-craft` 从实现开始约束一个明确代码结果，不套用固定语言或框架架构；`$context-shrink` 只在用户明确要求缩小维护上下文并给出仓库内目录后重组已有源码。二者都不会自动提交或推送。`$seo` 处理搜索发现与元信息，`$geo` 处理生成式回答的内容与引用证据；分别加 `audit` 可只读审查。两者可独立使用，不自动公开仓库、应用远端设置或发布。详见 [Skill 调用参与层级与启用策略](docs/skill-priority.md)。

忘了做到哪里、准备暂停或想保留反馈时，调用 `$human-in-the-loop`。项目根目录的 `evidence.md` 用四个字段保存目标、验证结果、未决问题和下一次验证，不限定行数。你可以只看或随手记一句，AI 核对整理、保留你的判断，继续已授权的工作。`$todo` 只负责从当前项目的任务中选下一步。下次可说“读取 evidence.md，帮我接上这个项目”；明确要求时才在 `AGENTS.md` 留入口，不保证宿主自动读取。完整规则见[技能说明](skills/human-in-the-loop/SKILL.md)。

想让外部 AI 更准确地介绍项目，使用 `$geo` 核实已有 README、公开文档和相关 `AGENTS.md` 中的答案与来源。按实际问题补足用途、用法或验证信息，不强制新建文件；内部证据不自动公开，内容改进也不等于已获得 AI 引用。

## 安装

安装持续更新的 `main` 版本：

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh | bash -s -- --host codex
```

源码默认保存在 `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`，其中的 `skills/` 子目录保存各 Skill 包；宿主链接仍按名称平铺在 `${HOME}/.agents/skills`。安装器只负责首次安装，并拒绝覆盖已有源码目录。

从已有源码目录激活前，可先预览：

```sh
./setup --host codex --dry-run
./setup --host codex
```

从旧版根目录布局更新源码后，重新运行 `setup` 会迁移能证明属于当前源码目录的旧链接，保留名称与调用方式；外部链接和真实目录不会被覆盖。已有的 Codex 旧安装位置也会检查并迁移这类链接，具体改动先看 `--dry-run`。

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

## 仓库结构

```text
skills/       所有 Skill 包，直接按名称平铺
docs/         使用与维护说明
scripts/      仓库校验脚本
templates/    新 Skill 的公共模板
README.md     产品入口与安装说明
AGENTS.md     AI 维护规则
DESIGN.md     产品地图与设计决策
```

每个包的完整工作流位于 `skills/<name>/SKILL.md`，配套脚本、模板和参考资料跟随该包。分类只存在于元数据中，不再增加分类子目录；根目录的 `install.sh`、`setup` 和 `uninstall` 负责源码获取、激活与卸载。

产品设计见 [DESIGN.md](DESIGN.md)，维护规则见 [AGENTS.md](AGENTS.md)。

MIT License，见 [LICENSE](LICENSE)。
