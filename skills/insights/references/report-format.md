# 报告数据格式

UTF-8 JSON 输入；完整工作流在 `SKILL.md`。

## 文件位置

默认目录由 `storage.py` 按技能 Inputs 创建：新目录 `0700`、新数据文件 `0600`，保留既有内容及权限。父路径别名解析为实际路径；Treefolk 根目录及 `insights/` 本身拒绝符号链接。`collect.py` 返回 `output`、`report_dir`；分析写同目录，`render.py` 默认在旁生成 `report.html`。

## usage.json

由采集器生成，模型只读。保持 `schema_version: 1`、`host: "codex"`。

| 字段 | 含义 |
| --- | --- |
| `generated_at` | 本次生成时间 |
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

### 生成上下文

`history.items[]` 仅供避免重复，含 `id/topic_id/title/action/last_seen/report_id`；不嵌入网页。最多读取 200 份旧报告、每个 JSON 16 MiB，保留最近 200 项去重建议。只导入实际展示过的原建议，跳过示例、残缺和不可追溯记录，不递归导入历史清单。跨日期但按项目归属过滤；缺口保留在 `history.coverage`。

`knowledge[]` 为本地官方摘要：`id/source/source_date/text`，来源为 `title/url`。按资料日期复用随包或旧报告的新摘要。`context.py --history` 每页给 20 条旧建议，`--offset` 翻页；不传则列资料目录，`--ids` 返回指定正文。

## analysis.json

模型只写本文件，统计沿用采集结果。所有文字作为纯文本显示；`suggestions` 合计 **0–3 项**，按价值排序。

```json
{
  "summary": "一句话概括本次值得注意的事",
  "reviewed_sessions": ["实际深入阅读的会话 ID"],
  "suggestions": [{
    "topic_id": "specific-usage",
    "title": "简短标题",
    "why": "与本次记录的联系；推测须明示",
    "action": "具体建议，允许只是意见",
    "refs": ["真实证据 ID"],
    "try": {
      "where": "仅在什么条件成立时，复制到哪里使用",
      "text": "可直接复制的命令或提示词",
      "expect": "试用后可以观察到的结果"
    },
    "knowledge_refs": ["所依据的本地文档 ID"]
  }],
  "latest": {
    "enabled": false,
    "status": "off",
    "checked_at": null,
    "sources": [],
    "note": "本次未查询最新资料"
  },
  "limitations": ["实际存在的覆盖或分析限制"]
}
```

- `try` **可省略**。任务可能已经结束；没有现实适用条件、无需操作或无法给出可复制内容时，只保留意见。复制不会执行命令，也不记录使用状态。
- `knowledge_refs` 可省略；具体产品用法引用对应官方摘要，渲染器附资料日期与来源。工作方法的推测不需要伪造产品资料。
- `topic_id` 为开放的稳定标识。同主题或同动作重现时必须有 `new_detail` 解释新增价值；非空字段不能代替语义判断。
- `latest.status` 为 `off/checked/partial/unavailable`。只有实际查询成功或部分成功才填 `checked_at`、官方 `sources`；其他状态日期为空、来源为空。
- 可选 `knowledge_updates[]` 与 knowledge 文档同结构，至多 20 项；仅 `checked/partial` 可写，日期与 URL 必须匹配本次实际查询。网页只嵌入被引用的来源及日期。

新分析只使用 `suggestions`。旧 HTML 保持原样；旧 `findings/features` 只在导入历史时还原实际展示项。无需迁移或重写旧报告，旧 `known.md` 保留且不读写。

内置校验拒绝超额建议、重复动作、伪造证据 ID、无效日期/来源及覆盖写入。转义防止文本成为脚本；这些保护不能证明建议有效或任务仍在进行。
