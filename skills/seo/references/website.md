# 网站搜索规则与证据

仅在目标包含既有网站时读取。规则于 2026-09-09 核对；平台行为可能变化，按本轮需要查官方更新。完整工作流在 `../SKILL.md`。

## 搜索意图与结果表达

从真实受众和内容形成查询候选，有站长数据时优先使用。用户用词可以不同，但不必枚举每个变体、追求关键词密度或把词组变成重复页面。内容应有实际用途，不能为了搜索而编造能力。[Google SEO 基础](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)

标题和描述应准确、具体、区分不同页面，沿用现有框架元信息能力。搜索引擎会选择或改写结果标题与摘要；meta description 不保证逐字展示，也不是直接可控的排名开关。没有通用的固定字符验收值，不能以截断预测替代实际内容判断。[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[摘要](https://developers.google.com/search/docs/appearance/snippet)

## 抓取、索引与页面内容

先判断目标 URL 是生产、预览、私有页面还是脚本下载，再看状态码、重定向、认证、主要文本和链接。源码中有文本不证明响应中存在；用户浏览器能看到也不证明某个爬虫已经读取。[SEO 基础](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)

`robots.txt` 控制抓取，不是访问控制或可靠的去索引机制。被禁抓 URL 仍可能出现在搜索结果；`noindex` 必须能被爬虫读取才能生效。检查 HTML meta 和适用的 HTTP 头，不能用 `Disallow` 隐藏私有内容或把保护预览目录当作缺陷。[robots.txt](https://developers.google.com/search/docs/crawling-indexing/robots/intro)、[noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing)

JavaScript 页面分开检查初始响应与渲染后的 DOM。Google 能处理许多 JavaScript 内容，不能仅凭首个响应没有正文断言未收录；也不能由此推断所有爬虫都能执行脚本。核对主内容是否依赖点击或登录、链接是否可发现、canonical 是否冲突，以及初始 `noindex` 是否阻止后续渲染。使用已有生成能力解决已证实的问题，不默认重写为 SSR。[JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)

## URL、语言与内容关系

- canonical 应表达等价内容的首选 URL，不把各个独立页面都指向首页。它是信号，不保证搜索引擎采用。已有重定向、canonical、内链和 sitemap 不应互相矛盾。[canonical](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- 多语言页面按实际语言维护 URL 和互链，适用时配置对应的 `hreflang`；不把所有译文 canonical 到一种语言。`hreflang` 是可用的语言版本标注方式，缺少它不直接证明页面无法收录。[多语言页面](https://developers.google.com/search/docs/specialty/international/localized-versions)
- 站点地图不是所有站点的强制文件；已有生成器就改配置，不创建重复列表。内链应能通向用户需要的主要页面。[SEO 基础](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)

## 结构化数据与验证

仅在页面类型和内容适用时使用受目标平台支持的结构化数据；与可见事实一致，不能编造评分、价格或 FAQ。合法标记不保证富结果。[结构化数据](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)

优先补充真实经验、实测过程或项目独有信息，而不是摘要式拼凑资料。没有官方的目标字数要求，不靠刷新日期伪装新内容。避免批量生成主要用于操纵排名的低价值页面或不真实提及。[内容质量](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)

本地静态检查、生成 HTML、浏览器渲染、生产响应、站长平台索引记录各自证明不同层面。单次 `site:` 查询未命中不能独立证明未收录。分析排名或流量时保存观察条件，不以一次搜索结果断言改动因果。
