# 报告数据格式

本文件定义 UTF-8 JSON 输入和共享记录协议；完整工作流在 `SKILL.md`。

## 文件位置

默认目录由 `storage.py` 按技能 Inputs 创建：新目录 `0700`、新数据文件 `0600`，保留既有内容及权限。父路径别名解析为实际路径；Treefolk 根目录及 `insights/` 本身拒绝符号链接。`collect.py` 返回 `output`、`report_dir`；分析写同目录，`render.py` 默认在旁生成 `report.html`。

## usage.json

由采集器生成，模型只读。保持 `schema_version: 1`、`host: "codex"`。

| 字段 | 含义 |
| --- | --- |
| `generated_at` | 本次生成时间，也是新用法抽样种子 |
| `period` | 含首尾的 `since`、`until` 及 `timezone` |
| `activity` | 按日期/项目聚合的请求、外层工具调用、显式失败、命令族和 `$name` 技能请求 |
| `sessions` | 会话与源文件索引；`cwd` 供本地项目归属，网页移除源路径 |
| `evidence` | 每会话至多 6 个均匀分布的用户摘录、3 个失败、3 个命令样例 |
| `coverage` | 去重、子代理、格式、读取、坏行和限额等覆盖情况 |
| `status` | `COLLECTED` 正常；`PARTIAL` 有数据但不完整；`NO-DATA` 可读范围为空；`BLOCKED` 无可用结果且存在读取等缺口 |

限额为最近修改的 2000 个文件、每文件 32 MiB、每行 1 MiB，只读取打开时已有字节。触限意味着部分覆盖。用户消息优先 `event_msg.user_message`；文件没有该类型时回退 `response_item.message` 的 user 角色，并排除常见注入上下文。会话 ID 去重文件，同一文件的 `call_id` 去重工具调用；未知分叉可能重复。复合命令只计一条，包装器内部调用可能不可见；显式失败不等于完整失败率。

证据 ID 如 `session-id:L12`，通过 `sessions[].source` 定位源文件及行号，不拼成命令。网页保留项目名、会话 ID 和脱敏摘录，仍属私人材料。

### Token

`activity[].tokens` 按行计量，`token_usage` 为同口径全期汇总；旧报告缺字段显示缺失。

| 字段 | 含义 |
| --- | --- |
| `input_tokens` / `output_tokens` | 输入已含缓存；输出已含推理 |
| `cached_input_tokens` | 缓存已知区间的缓存输入 |
| `cache_eligible_input_tokens` | 上述区间对应的全部输入 |
| `used_tokens` | 缓存已知区间的 `input − cached + output` |
| `sessions` | 有可计算区间的会话 ID |
| `coverage` | `snapshots`、`measured`、`cache_known`、`duplicates` 及缺口计数 |

- input/output 可计算才累加；缓存未知时保留输入/输出，但不累加 cached、eligible、used。没有可计算区间为 `null`，不能补零。汇总 `cache_hit_rate = cached / eligible`，零分母为 `null`；部分覆盖下 Used 仅代表已知部分。
- 从 `event_msg.token_count.info.total_token_usage` 累计快照取差值，同次读取保留窗口前基线，按当前快照时间归属日期。首值只有等于 `last_token_usage` 的输入/输出或为零时才能从零计入；否则记 `unknown_baseline`。
- 重复快照不累加；计数回退记 `counter_resets` 并重建基线。其余缺口包括 `missing_usage`、`invalid_usage`、`out_of_order`。仅计主会话；缺失可能低估，未知分叉可能重复。
- 筛选共用日期/项目范围。长时间段合并相邻日期，缓存率按合并后的 token 数计算，不平均百分比。数据不代表完整账单或本次报告的生成成本。

### 历史与资料

采集器一次遍历最多 200 份旧报告、每个 JSON 16 MiB、200 项精确去重建议，只读普通文件。跳过示例、残缺及不可追溯报告；不读取 HTML 正文或递归导入复制的历史。

- `history.items[]`：`id`、`topic_id`、`title`、`action`、`first_seen`、`last_seen`、`sources[]`。来源含 `report_id`、`date`、`origin`（`report` / `user_confirmation`）和原报告相对 `url`。仅导入实际展示的原始建议，按归一化动作精确去重。
- 历史跨日期但按项目过滤；用旧 `cwd` 或当前同 ID 会话定位，归属不明时不混入单项目报告。`history.coverage` 保留未导入数量。
- `knowledge[]`：`id`、官方 `source`、`source_date`、事实摘要 `text`；可带 `quick_reference[]`，行字段为 `host`、`platform`、`keys`、`action`、`when`。`host` 为 `app/cli`，平台为 `all/macos/windows/linux`。文档按资料日期及报告时间合并，网页只嵌入速查、日期和来源。
- `context.py --history` 分别分页返回历史与已知建议，每页 20 项，含总数和 `feedback_status`；`--offset` 翻页。`--ids` 读取指定文档，不传则列资料目录。

### 已知记录

`feedback` 从报告根目录的 `known.md` 读取：`status` 为 `ready/missing/unavailable`，`path` 为原文件绝对路径；可用时附 `store_id` 和 `entries[]`（`id`、`label`、布尔 `known`）。仅有会话且文件缺失时新建；上限 512 KiB，拒绝非普通文件、符号链接、损坏格式和重复 ID，失败保留原件及覆盖缺口。

文件首行为 `<!-- treefolk-insights-known:v1:<32 位十六进制标识> -->`；条目为 `- [x] 具体用法 <!-- insights:advice-<16 位十六进制标识> -->`。动作 ID 取归一化动作 SHA-256 前 16 位；编辑 `[x]/[ ]` 时保留标识和其他文字。

网页的 checkbox 数据由渲染器生成，嵌入路径、文件标识及已知 ID 快照。阅读模式隐藏逐条控件；“整理建议”进入选择模式，选择只保存在当前页面，点击保存后才申请权限并把全部更改放在一次独占写入中。句柄缓存仅供复用授权；浏览器不能核对绝对路径，同标识副本不会同步回采集路径。每次保存先重读，再只改选择涉及的条目，保留笔记，关闭写入流成功才确认；取消丢弃页面草稿，失败保留草稿和原文件。不保证与外部编辑器并发修改的事务安全。

支持及授权依据：[文件访问](https://developer.chrome.com/docs/capabilities/web-apis/file-system-access)、[权限延续](https://developer.chrome.com/blog/persistent-permissions-for-the-file-system-access-api)。不支持或失败时保留阅读并提示未保存，不自动下载副本。

## analysis.json

由模型编写，字符串按纯文本显示；数组允许为空。下例展示结构：

```json
{
  "summary": "本期有依据的结论",
  "reviewed_sessions": ["实际深入阅读的会话 ID"],
  "findings": [{
    "topic_id": "stable-topic",
    "title": "行动建议",
    "observation": "观察事实",
    "interpretation": "原因推测",
    "action": "下一次做法",
    "check": "下次如何观察效果，本次不执行",
    "confidence": "medium",
    "refs": ["真实证据 ID"]
  }],
  "features": [{
    "topic_id": "specific-usage",
    "title": "用法",
    "why": "与用户需要的关系",
    "when": "宿主、平台及触发条件",
    "benefit": "具体收益",
    "command": "具体操作",
    "availability": "reference",
    "version": "本机支持未知",
    "checked_at": "2026-09-15",
    "source": {"title": "资料名称", "url": "官方 HTTPS 页面"},
    "refs": ["真实证据 ID"]
  }],
  "latest": {
    "enabled": false,
    "status": "off",
    "checked_at": null,
    "sources": [],
    "note": "本次未联网"
  },
  "limitations": ["覆盖、抽样或来源缺口"]
}
```

- `confidence` 为 `high/medium/low`，表示判断把握，不是个人评分。
- `availability`：`local` 为当前上下文已有本机确认；`official` 为实际已读官方依据；`reference` 为本地官方摘要；`unverified` 为待核实。`features[].checked_at` 是资料日期；未核实用法用本次整理日期，并在来源标题明示待核实。
- `latest.status`：`checked/partial` 须填查询日期及实际官方来源；`unavailable/off` 的日期为 `null`、来源为空。`enabled` 与是否 `off` 对应。
- 来源使用 OpenAI 官方域名或 `github.com/openai/codex` 下的 HTTPS 页面，不带私人记录、查询词或凭据；本机材料无 URL 时保留标题，用 `null` 表示缺失。
- `reviewed_sessions` 只计实际深入阅读，不计仅看概览或短摘录。
- 新采集结果带 `suggestion_selection: "random-v1"`：渲染器对功能候选排除已知动作并去重，按 `SHA-256(generated_at + advice_id)` 排序取至多 3 项；行动只排除已知动作，顺序不变。重渲染和历史导入均用原快照恢复展示；旧报告无标记时保持原展示。

### 可选分析字段

有 `history` 的新采集结果要求每条建议带稳定 `topic_id`，用法另需 `when/benefit`；ID 不受资料目录限制。

| 字段 | 数据与约束 |
| --- | --- |
| `new_detail` | 与历史主题/动作重合时必填，说明新增操作、场景或限制；非空不等于语义上确实新颖 |
| `history_groups[]` | `topic_id/title/action/items`；items 引用原建议 ID，每项最多一组，日期/来源由脚本保留 |
| `confirmed_advice[]` | 当前用户明确回忆的旧意见：`topic_id/title/action/confirmed_at/note`，可选绝对项目路径 `projects`；无原报告时标“用户确认” |
| `knowledge_refs` | 文档 ID 数组；来源 URL 及资料日期须与引用一致 |
| `knowledge_updates[]` | 与 knowledge 文档同结构，至多 20 项；日期等于本次查询日期，URL 在实际查询来源中，仅 `checked/partial` 可写 |

旧 `known_topics` 忽略、不导入；已知状态取 `feedback.entries`，不自动持久化模型推断。原始建议、确认及资料更新各写一次；统计、来源与日期由脚本保留。旧 schema-v1 报告兼容缺失的扩展字段。

渲染器内置校验证据、日期、状态、计数及来源，并拒绝覆盖；这些保护不证明分析、查询和阅读声明真实。
