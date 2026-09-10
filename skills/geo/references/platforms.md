# 平台规则与观测边界

规则核对于 2026-09-09。此文件提供条件分支与来源，完整工作流在 `../SKILL.md`。执行时只查目标平台当前规则，不把一个引擎的说明外推到全部 AI 产品。

## Google Search

[生成式搜索指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)（更新于 2026-07-10）将 AI 搜索视为既有搜索基础的延伸，强调对读者有实际价值、包含一手经验的内容。Google 不要求 `llms.txt`、特制 Markdown、专用 schema 或把内容切成小块；写作选择依据实际读者需求。这不等于其他服务都不使用这些文件。

[内容质量自查](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)关注原创信息、清楚来源、一手经验和恰当作者背景；不能据此虚构资历或把 E-E-A-T 当作可量化的单一排名分。证据与来源检查是内容质量工作，不是平台承诺的引用算法。

涉及资格时，核实索引及摘要资格，并在有权限时查看 [Search generative AI control](https://support.google.com/webmasters/answer/16908024) 的实际纳入/排除与继承状态。默认纳入，子属性可能继承父级选择；不能凭默认值断言某个站点当前纳入。此控制不影响一般 Search 的排名/纳入信号，也不控制 AI 训练；不把“优化”解释为允许改变现有内容使用偏好。

观测优先查看实际账户可用的 [Generative AI performance report](https://support.google.com/webmasters/answer/16984139)。当前 Search 报表涵盖 AI Overviews 与 AI Mode 的展示数据（impressions），可按页面、国家、日期、设备查看，不提供逐条提示词、答案引用、点击或排名。数据也计入总体 Web 表现报表；新报表是独立视图，未替代总体报表。报表不存在或无数据不证明内容从未被引用；核实可用性和数据量限制，不沿用旧文档假定所有 AI 数据只能看合并的 Web 报表。

版本注意：[旧 AI features 页面](https://developers.google.com/search/docs/appearance/ai-features)仍可检索到“没有额外要求”的概述。以现行控制和报表帮助页为准：技术资格仍基于索引/摘要资格，另外核实站点所有者的纳入选择。控制作用于说明列出的 Search 生成式功能（含部分 Discover 功能），不等于全部 Google AI 产品；独立 Search 报表与 Discover 报表也不是同一报表。

## Bing / Copilot

[AI Performance 官方介绍](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview)提供引用次数、引用页面、grounding queries 和趋势，覆盖 Microsoft Copilot、Bing 的 AI 摘要及部分合作体验。它也建议证据、准确事实和跨文字/图片/视频的一致性；这支持内容核验工作，不构成引用保证。

上述官方介绍将 grounding queries 定义为检索短语样本，并说明聚合指标不反映排名、权威度或每页在单次回答中的角色。结合当前账户核实可用字段，不能把样本当完整用户提示词或逐次回答日志，也不能用引用趋势证明一次内容改动的因果。仅有 Bing 数据不代表已测其他 AI 平台。

## 其他引擎与未指定平台

有明确目标时查询该提供方对搜索访问、训练用途、内容控制和可用测量的现行官方说明。查不到可靠规则则保留未知，继续可核实的内容工作；不以营销文章代替平台契约，不额外安装另一项 skill 才能继续。

未指定引擎可完成答案与证据审查；不假装已经测试任一平台。自动化客户端或模型只有实际连接目标服务并保留响应证据时，才算该目标上的观测。

## 观察记录的最小内容

需要对比时沿用同一组真实或明确标注假设的问题，保存日期、服务/模式、语言、目标 URL、响应或报表来源，以及提及/事实准确/引用/引用支持关系。保留未命中样本。样本数量和观察窗口写清楚，变化属于该范围的观察；不输出未经定义的通用 GEO 分数。
