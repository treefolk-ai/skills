> 生产力的提升，会改变你能够遇见的问题，进而改变你能够理解的需求。
>
> [阅读完整思考：生产力如何改变需求](docs/productivity-and-needs.md)

# Treefolk Skills

Treefolk AI 的个人 AI 工作流库，把反复出现的用户目标沉淀为有明确结果、安全默认值和验证方式的可复用 Skill。

## 产品方向

按你现在想完成的事，分为 `think → make → share` 三类。

| 方向 | 负责什么 | 当前能力 |
| --- | --- | --- |
| `think` 理清与判断 | 决定现在做什么，判断成果是否符合目标 | [`$todo`](skills/todo/SKILL.md) 从当前项目的任务文档选出一个下一步；[`$human-in-the-loop`](skills/human-in-the-loop/SKILL.md) 用简短证据看清 AI 的实际结果与可信边界，让人的纠正影响后续工作 |
| `make` 制作与改进 | 把成果做出来，或者改好 | [`$loop`](skills/loop/SKILL.md) 按验收标准持续迭代一个任务；[`$build`](skills/build/SKILL.md) 根据明确需求构建功能并验证；[`$context-shrink`](skills/context-shrink/SKILL.md) 保持行为并简化源码；[`$ui-to-desc`](skills/ui-to-desc/SKILL.md) 整理组件设计描述；[`$to-mmd`](skills/to-mmd/SKILL.md) 生成 Mermaid 源码；[`$seo`](skills/seo/SKILL.md) 改善搜索发现；[`$geo`](skills/geo/SKILL.md) 改善生成式回答的内容与证据 |
| `share` 交付与发布 | 把成果交付到仓库或运行环境 | [`$repo`](skills/repo/SKILL.md) 首次发布仓库；[`$push`](skills/push/SKILL.md) 交付一次完整改动；[`$pr`](skills/pr/SKILL.md) 创建或复用已验证的 PR；[`$deploy`](skills/deploy/SKILL.md) 部署到既有目标并验证线上结果 |

分类只用于理解产品地图，不影响 Skill 的安装和调用。每个 Skill 的完整工作流以对应的 `SKILL.md` 为准。

## 使用

在 Codex 中直接输入 `$skill-name`。会改变 Git、远端或部署状态的 `$repo`、`$push`、`$pr`、`$deploy` 必须显式调用；边界明确的 `$build`、`$todo`、`$human-in-the-loop`、`$to-mmd`、`$ui-to-desc`、`$context-shrink`、`$seo`、`$geo` 也可以由 AI 根据描述选择。`$context-shrink` 只在用户明确要求缩小维护上下文并给出仓库内目录后重组已有源码。`$seo` 处理搜索发现与元信息，`$geo` 处理生成式回答的内容与引用证据；分别加 `audit` 可只读审查。两者可独立使用，不自动公开仓库、应用远端设置或发布。详见 [Skill 调用参与层级与启用策略](docs/skill-priority.md)。

想新增功能、改变既有行为，或把已确定的接口与设计规格做成代码，用 [`$build`](skills/build/SKILL.md)（原 `code-craft`）。这里的 build 表示构建功能，单独运行编译或打包命令无需调用它。开始实现前会结合当前需求、项目约束与可用且相关的用户记忆和习惯；只询问上下文无法确定、会实质改变结果、兼容性、交付或授权的问题，无需每次确认开工。当前明确选择覆盖旧习惯，与项目约束冲突时先处理；记忆不可用不阻塞任务，也不假称已读取。

最高实现准则是**可读性优先、异常优先**：先识别真实失败路径，明确拒绝、传播、恢复与资源清理，再展开正常流程；不凭空制造异常或要求每层 `try/catch`。用户体验、只引入必要复杂性、易局部移除或替换、避免过早抽象都服务于这两条个人准则，并遵守既定需求、正确性、兼容与授权约束。不为可删除性预建接口或插件层，也不把仅外观相似的不同业务规则合并成抽象。

默认少增实体，比较现有能力、成熟生态方案与局部实现的总维护成本；VueUse、Tailwind CSS 等可按任务纳入候选，不因能手写就排除，也不强制引入。沿用项目工具链，没有既定包管理器和适用用户偏好且环境兼容的 JavaScript/TypeScript 项目才默认 pnpm。它完成实现和适用验证，偏好不提供安装、联网或迁移授权，也不自动提交或发布。

```text
$build 给现有 CLI 增加 CSV 导出，空数据只输出表头，写入失败时返回非零退出码
$build 按已确定的接口协议实现分页查询，复用项目现有请求层
$build 给设置页增加语言选择，保存后刷新仍保留选择
```

想留证据或写回目标、验收、取舍反馈时，用 `$human-in-the-loop` 让你用少量注意力判断 AI 结果是否符合目标。根目录 `evidence.md` 默认以四字段呈现目标、验证结果、未决问题、下一次验证；你可随手写，AI 整理，无变化不改。普通开发、问进度或恢复 AI 上下文不触发写入。见[技能说明](skills/human-in-the-loop/SKILL.md)。

想让外部 AI 更准确地介绍项目，使用 `$geo` 核实已有 README、公开文档和相关 `AGENTS.md` 中的答案与来源。按实际问题补足用途、用法或验证信息，不强制新建文件；内部证据不自动公开，内容改进也不等于已获得 AI 引用。

想按目标持续改进代码、内容、设计或数据，显式调用 [`$loop`](skills/loop/SKILL.md)。用“轮次 + 验收条件 + 任务”声明期望状态，AI 根据实际差距决定下一步；数字表示最多执行的轮次，省略时最多 10 轮，达标即可停止。未给条件时按任务选择少量适用验收，不统一套用高分要求。

```text
$loop help
$loop help 优化这篇新手指南
$loop 10 可读性>=9 可测试性>=9
$loop 5 普通文本对比度>=4.5:1：调整当前落地页的正文配色
```

这些是对话输入。省略任务时沿用当前明确的工作对象，也接受“可读性至少 9”等自然表达。`help` 只帮助选择标准并生成可复制的调用，不检查或修改项目，不自动执行建议。`$loop help 评分标准` 可展开 [10 个跨行业评价术语](skills/loop/references/criteria.md)；原生指标保留单位，主观评分须有具体依据。

由 AI 按技能说明在当前会话组织迭代，无需配置文件；无可验证进展时会停止并说明剩余问题，运行中可要求查看进度或停止。不自动提交或发布，也不提供宿主强制续跑、后台运行或跨会话自动恢复。

## 安装

当前整体版本为 [`v0.1.0`](https://github.com/treefolk-ai/skills/tree/v0.1.0)。版本标签固定整个技能库的同一次提交，包含全部 Skill、安装器和文档。

安装固定版本：

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/v0.1.0/install.sh | bash -s -- --host codex --ref v0.1.0
```

`main` 是持续变化的开发分支。需要安装最新源码时使用：

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

`code-craft` 已改名为 `build`。更新源码后，`setup` 会在共享目录激活 `build`，确认成功后再清理共享目录和已有 Codex 旧安装位置中、能证明指向本 checkout 已不存在的旧包路径的 `code-craft` 链接。旧名称不保留为第二个技能；旧路径被重用、无关链接及真实目录会保留，新名称冲突时不清理旧链接。`uninstall` 也能直接识别这些旧链接。若个人配置直接引用了旧名称或源码路径，需要同步调整；安装器不改写个人配置。

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
docs/         使用、维护说明与心得
scripts/      仓库校验脚本
templates/    新 Skill 的公共模板
README.md     产品入口与安装说明
AGENTS.md     AI 维护规则
DESIGN.md     产品地图与设计决策
```

每个包的完整工作流位于 `skills/<name>/SKILL.md`，配套脚本、模板和参考资料跟随该包。分类只存在于元数据中，不再增加分类子目录；根目录的 `install.sh`、`setup` 和 `uninstall` 负责源码获取、激活与卸载。

产品设计见 [DESIGN.md](DESIGN.md)，维护规则见 [AGENTS.md](AGENTS.md)。

MIT License，见 [LICENSE](LICENSE)。
