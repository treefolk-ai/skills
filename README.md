# Treefolk Skills

Reusable agent workflows with explicit outcomes, safety boundaries, and per-run verification steps.

## Skills

| Invoke | Use for | Important boundary |
| --- | --- | --- |
| `$repo` | Initialize a local Git repository on `main`, connect an existing remote, and make the first safe push | Does not create a hosted repository or configure authentication |
| `$push` | Review, commit, and safely push one coherent change | Does not initialize repositories, rewrite history, or create pull requests |
| `$pr` | Publish current work on a safe source branch and create or reuse one pull request | Stops when branch, remote, provider, or existing-PR state is ambiguous |
| `$to-mmd` | Convert text, processes, or relationships into editable Mermaid source | Produces Mermaid text, not a rendered image |

In Codex, select or mention `$repo`, `$push`, or `$pr` explicitly before running those side-effecting workflows. `$to-mmd` may also be selected from its description. See [Skill 调用参与层级与启用策略](docs/skill-priority.md) for the current invocation convention.

Each `SKILL.md` is the authoritative workflow for its skill.

## Host capability status

`install.sh`, `setup`, and `uninstall` accept `codex` and `grok` as selectors. Both selectors currently activate the same links in `${HOME}/.agents/skills` and use the same ownership-safe uninstall behavior.

The repository includes and statically validates Codex invocation-policy metadata for the side-effecting Git skills. It does not include a Grok-specific invocation-policy adapter or a live-host test suite. Filesystem activation tests therefore do not, by themselves, prove that a host discovered or successfully invoked a skill.

Other hosts are not currently claimed as supported.

## Install

The bootstrap installs source into `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`, validates it, and delegates activation to that checkout's `setup`.

Install the moving `main` channel for Codex-oriented automation:

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh | bash -s -- --host codex
```

Use `--host grok` for Grok-oriented automation. Both selectors activate the same shared directory. Because `main` moves, use an existing immutable release tag in both the installer URL and `--ref` when reproducibility matters.

To review the installer before running it:

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh -o treefolk-install.sh
less treefolk-install.sh
bash treefolk-install.sh --host codex
```

From an existing checkout, preview before activating:

```sh
./setup --host codex --dry-run
./setup --host codex
```

`setup` refuses existing files, directories, and unrelated links instead of overwriting them. New links are created only in the shared target; existing legacy Codex links are preserved.

## Verify activation

For a bootstrap installation, rerun the acquired setup without mutation:

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/setup" --host codex --dry-run
```

A successful activation check reports every public skill as already linked and no conflicts. This verifies the checkout's link state, not live host discovery or the behavior of every skill.

## Update and uninstall

The bootstrap is first-install only and refuses an existing source directory. Until a reviewed updater exists, update the source checkout explicitly rather than rerunning the bootstrap as an in-place update.

Use the same source checkout to preview and remove only links it can prove it owns:

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex --dry-run
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex
```

Run `uninstall` before deleting the source checkout. From a local checkout, use `./uninstall` with the same options. The `codex` and `grok` selectors remove the same owned shared and legacy links.

## Safety

The bootstrap uses HTTPS, requires no `sudo`, validates downloaded source before activation, and refuses to overwrite an existing source installation. Local `setup` and `uninstall` do not access the network, support true dry-runs, refuse conflicts, and remove links only after verifying ownership.

The Git skills inspect local and remote state, stop on ambiguity or overwrite risk, and prohibit force pushes, automatic history reconciliation, remote replacement, automatic amend, global Git configuration changes, and committing suspected secrets. Their complete rules live in their respective `SKILL.md` files.

## Contributing and validation

Read [DESIGN.md](DESIGN.md), [AGENTS.md](AGENTS.md), and [templates/SKILL.md.tmpl](templates/SKILL.md.tmpl) before changing the public surface. `AGENTS.md` contains the canonical validation matrix.

Repository validation covers Bash parsing, public-package structure, required Codex adapters, installer regression scenarios, and non-mutating install/setup/uninstall plans. It does not execute every skill against live remotes or providers, validate Mermaid semantics end to end, or prove Codex/Grok runtime compatibility.

## License

MIT. See [LICENSE](LICENSE).
