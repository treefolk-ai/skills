# GitHub 与包注册表

用于 GitHub 仓库或已存在的包发布入口。以下规则核对于 2026-09-09；使用时按目标平台核实可能变化的部分。这里提供决策依据，流程以 `../SKILL.md` 为准。

| 对象 | 有用的判断 | 边界与来源 |
| --- | --- | --- |
| 可见性 | 核实匿名用户能否读取项目内容与入口 | 私有内容不是公开搜索入口；已有授权的登录态访问不证明公众可见。[仓库搜索](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories) |
| 名称 / About | 名称表达项目，描述说清用途、用户与真实能力 | GitHub 普通仓库搜索默认搜名称、描述、Topics；README 需 `in:readme`。不以拉长名称代替清晰描述。[搜索规则](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories) |
| Topics | 选择真实主题和生态，交付完整候选值 | 最多 20 个，不需要填满；Topics 名称本身始终公开，即使关联仓库私有。不要把内部代号放进去。[Topics 规则](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics) |
| README | 简介说明项目身份；可见文本、标题、链接、图片 alt 支撑实际使用 | 不强制更换默认语言、居中、加徽章或 FAQ。现有视觉展示值得保留。[README](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) |
| 页面元信息 | 使用 GitHub 提供的仓库字段和分享设置 | README 不是 HTML head；GitHub 清理脚本等内容，JSON-LD 不能作为 README 内脚本生效。[Markup](https://github.com/github/markup) |
| Git tag / Release | 沿用项目真实版本策略，描述实际变化、用法与验证范围 | Tag 标记历史点，Release 基于 tag；不作为主题关键词。[Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) |
| 改名 | 仅在确有品牌或识别问题时提出具体候选 | 先检查 remote、raw URL、安装器、包 repository、文档、Pages、Actions 引用；平台重定向不能替代依赖检查。[改名](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository) |
| Social preview | 用真实产品视觉、名称和一句用途提高分享辨识度 | GitHub 建议 1280 × 640、PNG/JPG/GIF、小于 1 MB；实际上传后检查卡片，不宣称提升排名。[分享预览](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview) |
| npm | 核对 `description`、`keywords`、`homepage`、`repository`、`bugs` 和包 README | 搜索元数据在发布后才进入注册表；沿用包名、版本和发布策略。其他注册表使用其原生字段。[package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/) |

占位域名、计划中的包名、未上线命令要明确标注；有真实可用路径才提供替代入口。未选定许可证时保留事实，不擅自添加许可声明。

远端建议写成能直接审阅的字段和值，例如 `description: ...`、`topics: [...]`，不用只有“增加关键词”之类的抽象建议。已有工具可只读取得仓库元信息；认证失败时保留未知，不创建替代仓库。

同一仓库的本地预览站与 github.com 页面分别判断。修改本地 `index.html` 的 meta 标签不会配置 GitHub 仓库页面；安装脚本重定向 URL 也不能充当可浏览的项目主页。
