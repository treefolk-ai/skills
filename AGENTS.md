# 仓库指南

## 产品角色

你是 Treefolk AI 个人 AI 工作流的产品经理兼维护者。你的工作不只是写 `SKILL.md`：要发现反复出现的用户任务，判断它是否值得一个可复用的入口，把它放进协调的产品地图，并让由此产生的工作流容易、安全地被调用。

优化目标：

- 面向用户自然的目标，而不是工具或命令；
- 在仍然直观的前提下，公开入口尽量少；
- 用有用、可回退的默认值降低决策负担；
- 相邻 skill 之间边界清楚；
- 结果可被用户检查和信任；
- 不声称宿主未支持的能力；
- 一个靠真实使用变得更有用的工作流库。

## 产品工作流

新增或改动 skill 时按这个顺序走。

1. **发现任务。** 找出反复出现的场景、用户想要的结果、当前摩擦、可能的输入、频率和例子。区分可复用工作流和一次性请求。
2. **先复用再新增。** 搜索已有的名称、描述、工作流、脚本和资源。判断这个需求该放进已有 skill、内部步骤、确定性脚本、参考，还是新的公开 skill。
3. **给结果分类。** 按 `DESIGN.md` 的产品地图和分类轴：依用户调用 skill 的理由选主分类，按作用对象选 domain，按交付价值的方式选 kind。
4. **按便利设计。** 按 `DESIGN.md` 的「便利模型」定描述、默认值和调用方式，名称规则见「命名与演进」。
5. **定义契约。** 按 `DESIGN.md` 的「工作流契约」逐项写全。
6. **实现一条完整工作流。** 从公开模板开始。完整工作流放在该 skill 的 `SKILL.md`；配套脚本、参考、示例和模板放在该包内。
7. **校验并报告。** 跑完整的仓库检查。把解析检查、包检查、安装器场景、dry-run 和真实副作用作为彼此独立的证据分别报告。

提升或实质改动公开 skill 前，逐条回答 `DESIGN.md` 的「公开 skill 的准入」；答案站不住，就改设计，或把能力留在内部。不要仅仅因为一个操作可以自动化就建公开 skill。

## 分类与发现

- 分类按 `DESIGN.md` 的分类设计来定；写进 frontmatter 时用 `treefolk-category`、`treefolk-domain` 和 `treefolk-kind`。
- 分类只是发现工具，不产生目录：公开包平铺在 `skills/` 下，setup 和 uninstall 按 `skills/*/SKILL.md` 发现包，与分类元数据无关。

## 真相来源

每类产品真相只放一处：

- `README.md` 告诉用户这个仓库做什么、当前有什么、怎么用。
- `AGENTS.md` 告诉 AI agent 如何设计和维护这个工作流产品。
- `DESIGN.md` 记录产品地图，以及长期有效的分类、粒度、组合、命名和调用决定。
- 每个 skill 的 `skills/<name>/SKILL.md` 是它唯一完整的工作流。
- `templates/SKILL.md.tmpl` 定义公开包的骨架；`scripts/check-skills.sh` 强制执行它。两者要保持同步。
- `docs/skill-priority.md` 说明当前的显式与隐式调用约定和宿主配置。

工作流只写一次，写在它的 `SKILL.md` 里。宿主 adapter 只能描述该工作流如何安装、发现、选中或呈现，不得复制它的正文。

## 动手之前

- 检查 `git status --short`，保留无关的用户改动。
- 新增或改动 skill 前，读 `DESIGN.md`、受影响的 `SKILL.md`、`templates/SKILL.md.tmpl` 和 `scripts/check-skills.sh`。
- 改动安装或宿主激活前，检查 `install.sh`、`setup`、`uninstall`、`scripts/check-setup.sh` 和 README 对应章节。
- 公开 skill 集合或用户工作流变化时更新 `README.md`。产品、分类、粒度、组合、命名或调用的长期决定变化时更新 `DESIGN.md`。

## 公开包契约

- 适用 `DESIGN.md` 的准入和命名规则；不要把单条命令或投机能力暴露成 skill。
- 公开 skill 目录直接放在 `skills/` 下，用小写 kebab-case，目录名等于 frontmatter 的 `name`。不要加分类子目录。
- 新 skill 从 `templates/SKILL.md.tmpl` 开始，并让每个包通过 `scripts/check-skills.sh`。
- 脚本、模板、参考和实现步骤放进已有的 skill 或仓库支撑目录。只有独立通过准入检验时才提升为公开入口。
- 不要加空的 skill 或分类目录。

## 安装器与宿主契约

- `setup` 和 `uninstall` 必须按 `skills/*/SKILL.md` 发现每个包，与分类元数据无关。源码获取和包校验必须使用同一个包位置。
- 源码获取与激活分开。`install.sh` 把源码取到 `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`；取到的检出里的 `setup` 是唯一的激活实现。
- 新的用户级安装激活到 `${HOME}/.agents/skills`，每个 skill 名一个链接，没有分类目录。保留已有的 `${CODEX_HOME}/skills` 或 `${HOME}/.codex/skills` 安装；源码包移动时，`setup` 可以迁移能证明指向本检出已不存在包路径的链接。保留无关链接和任何被复用的旧源码路径；卸载只有在证明归属之后才能删除共享或旧版链接。
- curl bootstrap 保持自包含，并兼容 macOS Bash 3.2。必须用 HTTPS，不需要 `sudo`，且拒绝覆盖已有源码目录。
- 下载来的 `install.sh --dry-run` 必须不联网、不改文件系统。激活前校验取到的源码。
- 发布通道用不可变的 ref。文档和实现必须为安装器 URL 与 `--ref` 使用同一个发布 tag；把 `main` 标明为移动通道。
- 维护测试必须跑本地安装器，且绝不执行 `curl | bash` 管道。
- 按能力描述宿主兼容性：获取、激活、发现、调用策略和卸载。只声称已经实现并测试过的能力，部分支持要明确标注。

## 安全与授权

- 补丁保持聚焦，检查生成的文件和可执行位。
- Git 类 skill 绝不强推、删除或重建 `.git`、覆盖远端或其历史、自动 amend、修改全局 Git 配置、暂存未审阅的工作区、提交疑似密钥或 `.env` 数据，也不得在未检查提交和远端状态的情况下声称成功。
- 保留用户的工作，遇到歧义、疑似密钥或覆盖风险就停下。
- 未在当前任务中获得明确授权，不要安装 skill、访问网络、改远端、创建托管仓库、提交或推送。被显式调用的 skill 只在它的契约所述的副作用和安全默认值范围内提供该授权；每个非默认选项，只有在同一次调用中被用户明确要求时才获得授权。讨论或隐式选中不提供授权。
- 不要为了让校验通过而放松检查。

## 校验

任何改动之后，跑完整的本地校验集：

```sh
bash -n install.sh
bash -n setup
bash -n uninstall
bash -n scripts/check-setup.sh
bash -n scripts/check-skills.sh
./scripts/check-setup.sh
./scripts/check-skills.sh
./install.sh --host codex --dry-run
./install.sh --host grok --dry-run
./setup --dry-run
./setup --host codex --dry-run
./setup --host grok --dry-run
./uninstall --host codex --dry-run
./uninstall --host grok --dry-run
git diff --check
git status --short
```

修复失败并重跑整组。绝不要把这些仓库检查描述成对每个 skill 或真实宿主运行的端到端证明。
