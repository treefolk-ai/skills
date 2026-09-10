> 生产力的提升，会改变你能够遇见的问题，进而改变你能够理解的需求。
>
> [阅读完整思考：生产力如何改变需求](docs/productivity-and-needs.md)

# Treefolk Skills

Treefolk AI 的个人 AI 工作流库，把反复出现的任务整理成可直接调用的技能。

## 技能

| 技能 | 用途 |
| --- | --- |
| [`$todo`](skills/todo/SKILL.md) | 从项目任务中选出下一步 |
| [`$human-in-the-loop`](skills/human-in-the-loop/SKILL.md) | 记录验证结果与验收反馈 |
| [`$build`](skills/build/SKILL.md) | 实现功能并验证结果 |
| [`$context-shrink`](skills/context-shrink/SKILL.md) | 简化指定目录的源码，保持行为不变 |
| [`$loop`](skills/loop/SKILL.md) | 按验收标准持续改进一项任务 |
| [`$ui-to-desc`](skills/ui-to-desc/SKILL.md) | 整理组件设计说明 |
| [`$to-mmd`](skills/to-mmd/SKILL.md) | 把流程或结构转为 Mermaid 图 |
| [`$seo`](skills/seo/SKILL.md) | 改善网站与仓库的搜索可发现性 |
| [`$geo`](skills/geo/SKILL.md) | 帮助 AI 更准确地介绍项目 |
| [`$repo`](skills/repo/SKILL.md) | 首次发布 Git 仓库 |
| [`$push`](skills/push/SKILL.md) | 检查、提交并推送改动 |
| [`$pr`](skills/pr/SKILL.md) | 创建或复用 Pull Request |
| [`$deploy`](skills/deploy/SKILL.md) | 部署到已有目标并验证结果 |

## 使用

在 Codex 对话中输入技能名和需求：

```text
$todo
$build 给设置页增加语言选择，刷新后保留选择
$loop 5 可读性>=9：优化这篇文档
```

`$repo`、`$push`、`$pr`、`$deploy`、`$loop` 需要明确输入技能名。其他技能也可由 AI 根据需求选择。详细用法见上表链接。

## 安装

安装固定版本 `v0.1.0`（Codex）：

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/v0.1.0/install.sh | bash -s -- --host codex --ref v0.1.0
```

开发版使用持续更新的 `main`：将命令中的两处 `v0.1.0` 都替换为 `main`。

源码默认存放在 `~/.treefolk/skills`，技能链接位于 `~/.agents/skills`。安装器拒绝覆盖已有源码。

已有源码时，在仓库目录运行 `./setup --host codex`。安装与卸载命令均支持 `--dry-run` 预览。

Grok 可改用 `--host grok`；目前仅通过本地安装与卸载检查，尚未验证真实宿主调用。

## 卸载

先预览，确认后移除 `--dry-run` 执行。卸载后再删除源码目录。

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex --dry-run
```

[调用规则](docs/skill-priority.md) · [产品设计](DESIGN.md) · [维护指南](AGENTS.md) · [MIT License](LICENSE)
