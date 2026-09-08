# 已审查的 GitHub 实现

2026-09-09 只读核实以下 4 个维护中项目的默认分支与相关文件。日期是当时 HEAD 的提交日期，不代表每个文件当天修改。链接固定到已审阅提交；这些是实现证据或社区实践，不是搜索排名契约，也不要求安装项目。

| 项目与版本快照 | 采用的判断 | 需要防止的误用 |
| --- | --- | --- |
| [marketingskills SEO audit](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/seo-audit/SKILL.md)，HEAD 2026-09-05 | 先读项目上下文，发现关联证据、具体修正和优先级；SEO 与 AI 回答优化分开 | 词数、标题长度、单个 H1 或 x-default 不应一律作为 Google 强制规则 |
| [aaron-marketing-skills technical SEO](https://github.com/aaron-he-zhu/aaron-marketing-skills/blob/91701e62ef4c6dd41201ca2fcc035e8116f040b6/seo-geo/tune/technical-seo-checker/SKILL.md)，HEAD 2026-09-08 | 抽查代表性路由模板；区分原始响应、渲染 DOM、测量值与估计 | 不能把文本抽取后的 JSON-LD 缺失判为页面没有标记，也不沿用“所有 AI 爬虫不执行 JS”等断言 |
| [Lighthouse crawlability](https://github.com/GoogleChrome/lighthouse/blob/74d982bd211c5fb12c4b2c18c4a1fc8bc17f6b6c/core/audits/seo/is-crawlable.js)，HEAD 2026-09-02 | 同时查看 meta robots、响应头和按 user agent 解释的 robots.txt | 该实现只在所有已知及通用 bot 被阻止时判失败；总项通过仍可能警告 Googlebot 被禁，不能宣称 Google 可索引 |
| [Unhead canonical 插件](https://github.com/unjs/unhead/blob/984add08ae32bf7e50a25b86a18009e21f8102d3/packages/unhead/src/plugins/canonical.ts)，HEAD 2026-09-04 | 核对实际生成的绝对 URL、尾斜线、页面参数与社交图片地址 | 该版本 `queryWhitelist` 默认空列表，删除 canonical / og:url 的所有查询参数；先判断分页、版本或语言参数是否改变内容，不机械照搬默认值 |

[Lighthouse structured-data](https://github.com/GoogleChrome/lighthouse/blob/74d982bd211c5fb12c4b2c18c4a1fc8bc17f6b6c/core/audits/seo/manual/structured-data.js) 是人工审计项。Lighthouse 分数不能证明 schema 正确或获得富结果。

[Unhead 对应测试](https://github.com/unjs/unhead/blob/984add08ae32bf7e50a25b86a18009e21f8102d3/packages/unhead/test/unit/plugins/canonical.test.ts)可用于理解该版本的 URL 处理预期；实际项目仍须检查自身依赖版本、配置和渲染输出。跟踪参数与改变内容的参数不能使用同一删除规则，图片变换参数也应保留其作用。

旧 `aaron-he-zhu/seo-geo-claude-skills` 已成为迁移指引；当前代码在上表的 `aaron-marketing-skills`。使用社区资料前检查现行仓库、具体文件和版本，不能只凭搜索摘要或星数判定质量。
