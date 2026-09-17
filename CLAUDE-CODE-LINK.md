# Claude Code 软链说明

本仓库的 skills 通过**纯软链**暴露给 Claude Code，不改动任何 skill 源文件。
所有 `<name>` 都是指向 `本仓库/skills/<name>/` 的软链。

## 链接位置

| 目标 | 路径 | 生效环境 |
|---|---|---|
| 日常 Claude Code | `~/.claude/skills/<name>` | 常规 `claude` 会话 |
| DeepSeek 会话 | `~/.claude-ds/skills/<name>` | `claude-deepseek` 启动的会话 |

## 使用脚本（推荐）

直接运行仓库根目录下的 `link-claude.sh`（从任何目录执行都行）：

```bash
./link-claude.sh                    # 链接全部 skill 到两个目标（幂等，可重复跑）
./link-claude.sh --only claude      # 只链接 ~/.claude/skills
./link-claude.sh --only ds          # 只链接 ~/.claude-ds/skills
./link-claude.sh --unlink           # 删除指向本仓库的软链（可加 --only 只删一边）
./link-claude.sh --dry-run          # 预览将要执行的动作，不实际改动
```

仓库更新新增 skill 后，重跑一次即可：已存在的自动跳过，新增的自动补上。

## 不用脚本的话

等价的最小命令（在仓库根目录执行）：

```bash
REPO="$(pwd)"
SRC="$REPO/skills"
for side in ~/.claude/skills ~/.claude-ds/skills; do
  mkdir -p "$side"
  for d in "$SRC"/*/; do
    name=$(basename "$d")
    [ -e "$side/$name" ] || [ -L "$side/$name" ] || ln -s "$d" "$side/$name"
  done
done
```

删除软链（只删指向本仓库的）：

```bash
REPO="$(pwd)"
for side in ~/.claude/skills ~/.claude-ds/skills; do
  for l in "$side"/*; do
    [ -L "$l" ] && case "$(readlink "$l")" in
      "$REPO"/*) rm "$l" ;;
    esac
  done
done
```

## 注意事项

- 改的只是软链，本仓库文件始终不被修改；删除软链不影响源 skill。
- 个别 skill（如 `insights`、`human-in-the-loop`）正文引用了 Codex 专属的 `$` 命令或 Codex 使用记录，在 Claude Code 里可以加载，但相关步骤需要模型自行适配。
- skill 在会话启动时加载：新建/删除软链后，新会话生效。
