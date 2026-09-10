# Skill 调用参与层级与启用策略

## 结论

Codex 没有公开的数字型 skill 优先级字段。Treefolk 使用 P0、P1、P2 作为维护约定，描述一个 skill 是否参与选择，以及它在启用时是否允许隐式匹配，而不是声明它比另一个 skill “更重要”。

- **P0：已启用，仅显式调用。** 用户必须写出 `$skill-name`。适合会提交代码、推送远端、创建仓库、发起 Pull Request 或部署到外部运行环境的高影响工作流。
- **P1：已启用，允许隐式匹配。** 用户没有点名 skill 时，Codex 可以根据 `name` 和 `description` 判断是否使用。适合风险可控、边界清楚且无需额外授权的只读、转换或有界本地工作流；本地写入必须由当前请求覆盖，并具备明确范围、停止条件和验证。
- **P2：由 host 配置禁用。** Skill 可以保留在本地并继续由仓库 installer 建立链接，但不参与显式或隐式选择。适合低频、暂时不用或与其他 skill 高度重叠的能力。

P0、P1、P2 不是 Codex 配置字段，也不属于 `treefolk-category`、`treefolk-domain` 或 `treefolk-kind`。这些 `treefolk-*` 值只负责分类，不控制安装或调用。

> **P0 用户须知：** 安装或启用 P0 skill，不代表它会参与基于描述的自动语义匹配。普通自然语言请求不会让模型自动选中它；用户必须输入准确命令。P0 skill 仍可出现在宿主的 skill 列表或命令补全中。当前 Codex adapter 使用 `$repo`、`$push`、`$pr` 和 `$deploy`。未来单独实现并验证 Claude Code adapter 后，对应命令将是 `/repo`、`/push`、`/pr` 和 `/deploy`；当前 `setup` 尚不支持 Claude Code。

P0 不禁止组合。一个被用户显式调用的 P0 工作流可以组合多个内部步骤，但它必须为完整结果统一承担授权、安全检查、停止条件、验证与报告。它不能依赖基于描述的自动匹配去发现并串联另一个 P0 工作流。

## Codex 如何选择 skill

Codex 选择 skill 时先使用可用 skill 的名称和描述，只在选中 skill 后加载完整的 `SKILL.md`。显式 `$skill-name` 调用最确定；没有显式点名时，只有允许隐式调用的 skill 才进入语义匹配。

```mermaid
flowchart TD
    request["收到用户请求"] --> enabled{"Skill 是否已启用？"}
    enabled -- "否：P2" --> skip["不参与本次选择"]
    enabled -- "是" --> explicit{"用户是否显式写出 $skill-name？"}
    explicit -- "是" --> load["加载目标 Skill 的完整 SKILL.md"]
    explicit -- "否" --> implicit{"是否允许隐式调用？"}
    implicit -- "否：P0" --> wait["不进入语义匹配；本次不加载"]
    implicit -- "是：P1" --> match["根据 name 与 description 语义匹配"]
    match --> selected{"是否明确匹配用户目标？"}
    selected -- "是" --> load
    selected -- "否" --> skip
```

这张流程图表达调用与启用关系，不表示多个 P1 skill 之间存在稳定的数值排序。多个描述同时匹配时，不应依赖未公开的选择顺序，而应收紧描述边界或改成 P0。

## 当前分层

| Skill | 层级 | 调用方式 | 原因 |
| --- | --- | --- | --- |
| `code-craft` | P1 | 显式调用或语义匹配 | 在用户已授权的明确代码范围内完成实现并验证成功与失败路径；不提交、不推送、不部署，也不把通用规范变成固定框架架构 |
| `repo` | P0 | `$repo` | 会初始化仓库、查询并可能创建托管仓库、创建提交并推送远端 |
| `push` | P0 | `$push` | 会暂存、提交并推送当前任务改动 |
| `pr` | P0 | `$pr` | 会创建分支、提交、推送并创建或复用 Pull Request |
| `deploy` | P0 | `$deploy` | 普通模式可能把源码或构建产物部署到外部运行环境，provider 在项目证据不冲突时默认 Cloudflare；`$deploy plan` 仍须显式调用，但只做本地静态检查 |
| `todo` | P1 | 显式调用或语义匹配 | 只读查询当前项目的任务文档并推荐一个可审阅的下一步；`$todo adhd` 仅压缩输出，不增加副作用 |
| `human-in-the-loop` | P1 | 显式调用或语义匹配 | 在明确的接续、交接或记录请求中维护人和 AI 共用的四字段 `evidence.md`，接受随手简记；仅为必要判断提问，不自动给所有开发任务加检查点；项目接入指引需明确要求 |
| `to-mmd` | P1 | 显式调用或语义匹配 | 只生成可审阅的 Mermaid 文本；未设置策略时，隐式调用默认为开启 |
| `ui-to-desc` | P1 | 显式调用或语义匹配 | 低风险地整理组件设计证据；只有路径和写入意图明确后才落盘 |
| `context-shrink` | P1 | 显式调用或语义匹配 | 只在用户明确要求缩小维护上下文并给出仓库内目录后修改该范围；先 MAP、逐项验证，不提交或推送 |
| `seo` | P1 | 显式调用或语义匹配 | 在请求范围内修复搜索发现、抓取索引与元信息；`audit` 只读，不自动应用远端设置或发布 |
| `geo` | P1 | 显式调用或语义匹配 | 在请求范围内核实答案与来源、修正可控内容；`audit` 只读，不把内容验证当作 AI 引用或自动发布 |

## 配置 P0

在源码包内添加 `skills/<name>/agents/openai.yaml`。字符串保持引号，`default_prompt` 必须显式包含该 skill 的 `$name`：

```yaml
interface:
  display_name: "PR"
  short_description: "Safely create and verify pull requests"
  default_prompt: "Use $pr to publish the current work as a verified pull request."

policy:
  allow_implicit_invocation: false
```

在 skill 已启用的前提下，`allow_implicit_invocation: false` 只关闭隐式触发；用户仍然可以显式调用 `$pr`。

## 配置 P2

在 `~/.codex/config.toml` 中按 `SKILL.md` 路径禁用 skill：

```toml
[[skills.config]]
path = "/absolute/path/to/skill/SKILL.md"
enabled = false
```

P2 是 host 层的禁用状态，不是安装过滤器；仓库 `setup` 仍然通过 `skills/*/SKILL.md` 发现全部公开包，并在宿主目录中按名称平铺链接。分类不参与安装或调用策略。修改全局配置后重启 Codex。重新启用时将 `enabled` 改为 `true`，或者删除对应配置项。

若配置直接引用了旧版源码根目录下的 `SKILL.md`，迁移后需改为对应的 `skills/<name>/SKILL.md` 路径。安装器只迁移能证明归属的链接，不改写宿主全局配置；指向宿主安装链接的路径无需因本次源码移动而改变。

## 维护原则

1. 把会修改 Git 历史、远端状态或外部系统的工作流默认归为 P0。
2. 仅让高频、风险可控且触发边界清楚的工作流保持 P1；若会本地写入，当前请求必须已覆盖该结果，且范围、停止条件和验证都必须明确。
3. 把只适用于单个仓库的 skill 放在仓库级 `.agents/skills`，不要全部安装到全局。
4. 保持 skill 名称唯一。相同名称不会自动合并，也不要依赖目录层级覆盖另一个 skill。
5. 在 `description` 开头写最重要的用户目标和触发词，并说明相邻但不应触发的场景。Skill 很多时，Codex 可能先缩短描述，再从初始列表中省略部分条目。
6. 当两个 P1 skill 经常同时匹配时，优先拆清职责和重写描述；仍有歧义时，把高影响的一方改成 P0。
7. 让仓库 validator 强制检查每个 P0 adapter，拒绝缺失文件、非布尔 `false`，以及未包含准确 `$skill-name` 的默认提示。

Codex 的显式与隐式调用、描述预算、启用配置及 `allow_implicit_invocation` 行为以官方 [Build skills](https://learn.chatgpt.com/docs/build-skills) 文档为准。
