# Treefolk Skills

Treefolk Skills is Treefolk AI's evolving system for building a personal AI workflow. It turns recurring jobs into reusable skills with clear outcomes, useful defaults, safety boundaries, and checks that make the result inspectable.

The goal is simple: tell an AI agent what you want to accomplish, reuse a well-designed workflow, and improve that workflow in one place instead of rebuilding the process in every conversation.

## What lives here

A Treefolk skill is more than a prompt snippet or command alias. It owns a complete user goal: when to use it, what information it needs, which decisions it may make, when it must stop, and how to verify the outcome.

The current library combines a small `core` foundation with the first `make` workflow for design knowledge:

| Skill | Helps you | Stops short of |
| --- | --- | --- |
| `$repo` | Prepare a local project on `main`, connect an existing remote, and make the first safe push | Creating a hosted repository or configuring authentication |
| `$push` | Review, commit, and safely push one coherent change | Initializing a repository, rewriting history, or opening a pull request |
| `$pr` | Publish the intended work and create or reuse one verified pull request | Guessing through ambiguous branch, remote, provider, or pull-request state |
| `$to-mmd` | Turn text, processes, or relationships into editable Mermaid source | Rendering PNG or SVG output |
| `$ui-to-desc` | Accumulate UI evidence across multiple turns into one reviewable component design description | Implementing the component or inventing missing design values |

A typical repository workflow is `$repo` once, `$push` for each coherent change, and `$pr` when work is ready for review. `$to-mmd` turns an idea or system into an editable diagram. `$ui-to-desc` stays with a component across a multi-turn design handoff, then produces one specification when the user marks it complete.

The library will grow around recurring parts of the personal AI workflow, not around every available command. See [DESIGN.md](DESIGN.md) for the product map and classification model.

## Use a skill

In Codex, mention `$repo`, `$push`, or `$pr` explicitly before running those side-effecting workflows. `$to-mmd` and `$ui-to-desc` may be invoked explicitly or selected from their descriptions. The current selection convention is documented in [Skill 调用参与层级与启用策略](docs/skill-priority.md).

Each skill's `SKILL.md` is its complete workflow and source of truth.

## Install

The bootstrap stores the source checkout at `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`, validates it, and then activates its public skills.

Install the moving `main` channel for Codex-oriented use:

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh | bash -s -- --host codex
```

Use `--host grok` for Grok-oriented use. For a reproducible release, replace `main` in the URL with an existing immutable tag and pass the same tag through `--ref`.

To review the installer before running it:

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh -o treefolk-install.sh
less treefolk-install.sh
bash treefolk-install.sh --host codex
```

From an existing checkout, preview activation before changing anything:

```sh
./setup --host codex --dry-run
./setup --host codex
```

`setup` refuses to overwrite existing files, directories, or unrelated links.

## Verify activation

For a bootstrap installation, rerun the acquired setup as a dry-run:

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/setup" --host codex --dry-run
```

A clean result reports every public skill as already linked with no conflicts. This verifies filesystem activation, not whether a host has discovered or successfully invoked every workflow.

## Host support

The `codex` and `grok` selectors currently activate the same links in `${HOME}/.agents/skills` and use the same ownership-safe uninstall behavior. The repository includes statically checked Codex invocation metadata for the Git skills; it does not yet include a Grok-specific invocation-policy adapter or live-host compatibility tests. Other hosts are not currently claimed as supported.

## Update and uninstall

The bootstrap is first-install only and refuses an existing source directory. Until a reviewed updater exists, update the source checkout explicitly rather than rerunning the bootstrap as an in-place update.

Preview and remove only links owned by that checkout:

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex --dry-run
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex
```

Run `uninstall` before deleting the source checkout. From a local checkout, use `./uninstall` with the same options.

## Safety and trust

Installation uses HTTPS, requires no `sudo`, validates acquired source before activation, and refuses overwrite conflicts. Local setup and uninstall support true dry-runs, do not access the network, and remove links only after proving ownership.

Side-effecting skills inspect state before acting, stop on ambiguity or overwrite risk, and verify authoritative state before reporting success. Repository checks validate package structure and installer behavior; they are not a substitute for per-run verification or live-host testing.

## Shape the workflow

Want to improve an existing workflow or add a recurring one? Read [DESIGN.md](DESIGN.md) for the product and classification model, then [AGENTS.md](AGENTS.md) for the AI-assisted design and maintenance process.

## License

MIT. See [LICENSE](LICENSE).
