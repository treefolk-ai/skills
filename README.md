> 生产力的提升，会改变你能够遇见的问题，进而改变你能够理解的需求。
>
> [阅读完整思考：生产力如何改变需求](docs/productivity-and-needs.md)

# Treefolk Skills

Treefolk AI 的个人 AI 工作流库，把真实使用中反复出现的需求，整理成少数清楚、可直接调用的技能。每个入口围绕一个完整的用户目标，帮助人减少重复解释、作出取舍，并看清 AI 实际交付了什么。

工作流按用户希望得到的结果组织为 **`think` → `make` → `share`**：

- **think · 想清楚：** 判断什么值得做、下一步做什么，以及已有结果是否符合目标。
- **make · 做出来：** 把明确的意图变成可使用、可验证的代码、内容、设计说明或图表。
- **share · 交付出去：** 把成果送到目标仓库或运行环境，并核对实际交付状态。

分类取决于最终目标。同样是写文档，帮助人判断结果的证据记录属于 `think`，产出组件设计说明属于 `make`。这些阶段可以往返，每个技能都能直接调用。

工作流库随着使用成长：当生产力提高、项目增多，新的协调和判断需求会逐渐浮现。先看清具体摩擦，再决定它值得一个独立入口，还是由已有工作流承担。

## 技能

| 分类 | 技能 | 希望得到的结果 |
| --- | --- | --- |
| `think` | [`$grill`](skills/grill/SKILL.md) | 逐题盘问想法，检验需求、复杂度和替代方案，形成有依据的取舍 |
| `think` | [`$todo`](skills/todo/SKILL.md) | 从当前项目的任务文档中选出一个有出处、可着手的下一步 |
| `think` | [`$human-in-the-loop`](skills/human-in-the-loop/SKILL.md) | 留下简短证据与验收反馈，让人看清结果是否可信，并让纠正影响后续工作 |
| `make` | [`$build`](skills/build/SKILL.md) | 把明确需求实现为可运行、经过验证的代码，优先可读性和真实失败处理 |
| `make` | [`$context-shrink`](skills/context-shrink/SKILL.md) | 在保持行为不变的前提下，减少指定源码范围的重复、中转与维护负担 |
| `make` | [`$loop`](skills/loop/SKILL.md) | 按约定验收条件持续观察和改进一项产物，在轮次预算内交付结果与证据 |
| `make` | [`$ui-to-desc`](skills/ui-to-desc/SKILL.md) | 将多轮提供的组件设计信息整理为一份可审阅的实现规格 |
| `make` | [`$to-mmd`](skills/to-mmd/SKILL.md) | 将流程、结构或数据关系转换为忠实、可编辑的 Mermaid 图 |
| `make` | [`$seo`](skills/seo/SKILL.md) | 改善网站、仓库及已有包入口的搜索可发现性，并验证相关改动 |
| `make` | [`$geo`](skills/geo/SKILL.md) | 改善内容的答案准确性与来源支持，区分内容验证和实际 AI 引用 |
| `share` | [`$repo`](skills/repo/SKILL.md) | 完成 Git 仓库的首次发布，确认目标远端并验证发布状态 |
| `share` | [`$push`](skills/push/SKILL.md) | 检查、提交并推送本次改动，核对提交和远端状态 |
| `share` | [`$pr`](skills/pr/SKILL.md) | 将工作交付为一个经过核对的 Pull Request，按目标创建或复用 |
| `share` | [`$deploy`](skills/deploy/SKILL.md) | 将选定源码或产物部署到已有目标，并验证实际运行结果 |

分类帮助发现能力；领域和工作形式用于进一步说明每个技能处理什么、如何交付价值，完整划分见 [产品设计](DESIGN.md)。上表对应当前源码，固定版本的技能以该版本内容为准。

## 使用

在 Codex 对话中输入技能名和需求：

```text
$grill 退出会话时自动关闭启动的终端，值得加吗？
$todo
$build 给设置页增加语言选择，刷新后保留选择
$loop 5 可读性>=9：优化这篇文档
```

`$grill`、`$repo`、`$push`、`$pr`、`$deploy`、`$loop` 需要明确输入技能名。其他技能也可由 AI 根据需求选择。详细用法见上表链接。

`$grill` 一次追问一个关键问题，帮助你决定做、缩小、先验证或暂缓。讨论默认在对话中完成；记忆整理交给宿主，不自动生成文档或修改全局规则。

## 安装与更新

**复制到 Codex（推荐）：** 打开 Codex，把下面整段发给它：

```text
帮我安装 Treefolk Skills：从 https://github.com/treefolk-ai/skills.git 克隆 main 分支到 ~/.treefolk/skills，进入该目录运行 ./setup --host codex，并核对安装结果。若已有本仓库的源码或安装，先核对来源后复用；遇到目录或链接冲突时保留现场并说明。
```

上面的指令使用持续更新的 `main`，由 Codex 完成获取源码、安装和检查。自动检查、提醒与更新尚未实现。

<details>
<summary>终端安装、手动更新与固定版本</summary>

首次 Git 安装，复制整条命令到终端：

```sh
git clone --branch main https://github.com/treefolk-ai/skills.git ~/.treefolk/skills && cd ~/.treefolk/skills && ./setup
```

已有源码直接在仓库目录运行 `./setup`。以后保存好本地改动，在跟踪远端的工作分支上更新：

```sh
git pull --ff-only && ./setup
```

`--ff-only` 只接受快进更新，拉取成功后才运行 `setup` 补齐链接；`setup` 自身不下载源码。

**固定版本：** 通过安装器获取 `v0.1.0`：

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/v0.1.0/install.sh | bash -s -- --host codex --ref v0.1.0
```

源码压缩包默认解压到 `~/.treefolk/skills`，验证后激活。它**没有 `.git`，不能 `git pull`**；安装器只负责首次安装，拒绝覆盖已有目录，暂无原地更新命令。获取开发版时，将命令中的两处 `v0.1.0` 都替换为 `main`。

</details>

`./setup` 默认使用 Codex。技能链接位于 `~/.agents/skills`，因此需保留源码目录；正确链接会跳过，已支持的迁移按归属检查处理，并保留其他来源的链接和真实目录。

安装、`setup` 和卸载均支持 `--dry-run` 预览。Grok 使用 `--host grok`，目前仅通过本地安装与卸载检查，尚未验证真实宿主调用。

**自有域名（TODO）：** 以下 `example.com` 链接仅为示意，尚不可安装；域名只简化地址。

- [ ] 接通 [固定版本入口](https://example.com/v0.1.0/install)，保持 URL、安装脚本和 `--ref` 版本一致。
- [ ] 接通 [开发版入口](https://example.com/install)，跟随 `main`。

## 卸载

在当前激活技能所用的源码目录中先预览，确认后移除 `--dry-run` 执行。卸载仅移除能确认归属该源码的链接，完成后再删除源码目录。

```sh
./uninstall --host codex --dry-run
```

[调用规则](docs/skill-priority.md) · [产品设计](DESIGN.md) · [维护指南](AGENTS.md) · [MIT License](LICENSE)
