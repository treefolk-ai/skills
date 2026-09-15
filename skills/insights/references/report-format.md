# 报告数据格式

生成网页时阅读。本文件只定义数据接口；完整分析流程在 `SKILL.md`。两个输入均为 UTF-8 JSON。

## 文件位置

默认根目录是 `${TREEFOLK_HOME:-~/.treefolk}/insights/`，独立于工作目录、技能源码和 Codex 会话根目录。`storage.py` 创建 `YYYY-MM-DD_HHMMSS-<唯一后缀>/`，新建目录权限为 `0700`，报告数据文件为 `0600`；不覆盖已有内容或更改已有目录权限。父路径别名（如 macOS 的 `/var`）解析为实际路径；Treefolk 根目录与其 `insights/` 目录本身若为符号链接则报错。

`collect.py` 省略 `--output` 时创建本次目录，并在输出 JSON 中给出 `output` 和 `report_dir`。将 `analysis.json` 写在同目录；`render.py` 省略 `--output` 时生成同目录的 `report.html`。`demo.py` 的默认示例也采用同一根目录；维护测试用显式输出路径或隔离的 `TREEFOLK_HOME`，不向用户真实目录写入测试数据。

每次报告的中间数据和验证产物都留在自己的文件夹里，交付时给出网页与文件夹入口；整夹移除即可清理一份报告。当前没有自动清理或后台索引，不更改技能卸载逻辑。

## usage.json

由 `scripts/collect.py` 生成，不由模型补写或更改统计。`period` 给出含首尾的日期和时区；`activity` 按日期与项目聚合用户请求、外层工具调用、显式失败、命令族和以 `$name` 开头的技能请求；`sessions` 是会话与源文件索引；`evidence` 是每会话至多 6 个均匀分布的用户摘录、3 个失败和 3 个命令样例。

`coverage` 记录重复会话、子代理、未识别格式、无法读取、坏行及限额。`status` 区分正常采集 `COLLECTED`、有缺口但有可用数据 `PARTIAL`、可读范围内没有数据 `NO-DATA`，以及缺口导致无可用结果 `BLOCKED`。默认最多读取最近修改的 2000 个文件、每文件 32 MiB、每行 1 MiB；触及限额须报告样本偏差和部分覆盖，不能称为全量审计。每次只读打开时已有的字节，不追随写入中的会话。

用户消息优先取 `event_msg.user_message`；一个文件没有该类型时，才从 `response_item.message` 的 user 角色回退，并排除常见的注入上下文。用同一文件的 `call_id` 去重工具调用，以会话 ID 去重文件；无法辨认的分叉副本仍可能重复计入。复合 shell 命令只计为一条复合命令，不执行或猜测其内部语句。包装器内部的工具调用可能不可见。显式失败数不等于完整失败率。

证据 ID 形如 `session-id:L12`，用 `sessions[].source` 找到采集根目录下的对应文件，再按行回看；不得把 ID 拼接成 shell 命令。自动截断及脱敏不保证匿名化。网页去掉源文件路径，但保留必要的项目名、会话 ID 和已审阅摘录；它仍是私人报告。

## analysis.json

模型根据实际记录编写以下字段。数组可以为空；没有证据时不凑建议。字符串以纯文本显示，不接受 Markdown/HTML 渲染。

```json
{
  "summary": "这一期间最有依据的一句结论；仅有统计时直接说明。",
  "reviewed_sessions": ["实际深入回看的会话 ID"],
  "findings": [
    {
      "title": "建议或值得保留的做法",
      "observation": "记录里具体看到了什么",
      "interpretation": "可能原因，保留其他解释",
      "action": "下一次的一个具体做法",
      "check": "下次如何观察是否有帮助",
      "confidence": "medium",
      "refs": ["来自 usage.json 的真实证据 ID"]
    }
  ],
  "features": [
    {
      "title": "与实际需要相关的功能",
      "why": "为什么值得这个用户尝试",
      "command": "已核实的命令，或明确标为待核实的用法",
      "availability": "local",
      "version": "本机实际版本，或本机支持情况未知",
      "checked_at": "2026-09-15",
      "source": {"title": "实际执行的帮助命令或读取的官方页面", "url": null},
      "refs": ["来自 usage.json 的真实证据 ID"]
    }
  ],
  "latest": {
    "enabled": false,
    "status": "off",
    "checked_at": null,
    "sources": [],
    "note": "本次关闭最新功能查询；推荐只依据本机可验证能力。"
  },
  "limitations": ["影响本次判断的覆盖、抽样、版本或验证限制"]
}
```

- `confidence`：`high` / `medium` / `low`，为模型判断的置信度，不是个人评分。`findings` 按建议优先级排序，通常不超过 3 项；保留有益做法也可作为行动。
- `availability`：`local` 表示本机帮助/能力已确认；`official` 表示官方文档确认但本机未确认；`unverified` 表示用法仍待核实。不能将“官方有这个功能”标成本机可用。
- `latest.status`：`checked` 为已完成相关官方查询；`partial` 为只完成部分；`unavailable` 为开启但无法查询；`off` 为主动关闭。前两种必须填写查询日期和实际读取的官方 URL。`enabled` 与 `off` 须一致；默认开启并不预设成功。
- 官方链接限 OpenAI 官方域名或 `github.com/openai/codex` 下的 HTTPS 页面。禁止将私人记录、查询词或凭据放进链接。没有远程 URL 的本机帮助来源保留 `title`，不伪造网页链接。
- `reviewed_sessions` 只记录实际深入阅读的会话；看到统计或短摘录不算全文审核。它决定网页展示的阅读样本量，不改动采集统计。
- 示例数据由 `scripts/demo.py` 在独立目录生成，并强制标记为合成示例；不能当成用户的真实分析。

`render.py` 检查证据引用、日期范围、状态一致性、计数类型和来源 URL，拒绝覆盖输出文件。结构检查不能证明模型推断、官方查询或阅读声明真实，仍须由执行代理核实。
