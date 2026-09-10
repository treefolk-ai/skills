# 社区 GEO 方法审查

2026-09-09 核实当前维护的 GitHub 内容；使用固定提交链接，避免将搜索摘要中的旧版本当作现行规则。这里保留方法启发与排除理由，不把社区结论写成平台承诺。

## marketingskills

[ai-seo 2.5.0](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/ai-seo/SKILL.md)，当时 HEAD 提交日期 2026-09-05。

采用：与传统 SEO 分开触发；复用项目上下文；先确定目标问题及现有观察，再检查引用落点和内容缺口。

不采用：统一的 40–60 词回答块、schema 带来固定可见性增长、非 Google 平台普遍解析 `llms.txt`，以及把训练爬虫当成搜索引用开关。文件仍写 Google 没有 AI 专用报表，与本包现行官方来源冲突。即使同一文件包含正确的 Google 提醒，其余平台表和数字也需要独立验证。

[格式波动参考](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/ai-seo/references/format-volatility.md)启发固定观察条件、保留样本数与未命中结果。具体模型偏好、格式效果及小样本变化不能转为长期规则或因果证明。

## aaron-marketing-skills

[GEO 工作流](https://github.com/aaron-he-zhu/aaron-marketing-skills/blob/91701e62ef4c6dd41201ca2fcc035e8116f040b6/seo-geo/implement/geo-content-optimizer/SKILL.md)，当时 HEAD 提交日期 2026-09-08。旧 `seo-geo-claude-skills` 已指向这个新仓库。

[引用模式参考](https://github.com/aaron-he-zhu/aaron-marketing-skills/blob/91701e62ef4c6dd41201ca2fcc035e8116f040b6/seo-geo/implement/geo-content-optimizer/references/ai-citation-patterns.md)中有用的做法：按平台核实内容控制，记录语言、时间、账号状态、引用 URL 与段落，拒绝统一字数与结构保证。但其中 Google 概述也需用现行控制和报表文档补充，不能因自称重新核实就整表采信。

[测量协议](https://github.com/aaron-he-zhu/aaron-marketing-skills/blob/91701e62ef4c6dd41201ca2fcc035e8116f040b6/references/measurement-protocol.md)启发区分访问检查、提供 URL 的理解探测、自然搜索引用与流量结果；记录实测、用户提供、估计和未知。模拟 user agent 不证明真实爬虫可以访问，需结合提供方身份规则及实际日志。

不采用整套评分框架或记忆写入流程；它们增加本任务之外的维护成本。主 skill 仍要求固定回答词数，个别爬虫表与其引用参考相互矛盾，不能导入为本站默认规则。

## 转化为本 skill 的检查

内容依据、公开可读取性、目标引擎响应、引文支持关系与业务流量各自留证。数据缺失标为未知，不是零。先修复已证实的错误或证据缺口；没有观察条件时交付可靠内容，不生产看似精确的“GEO 分数”。
