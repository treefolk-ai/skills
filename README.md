# Treefolk Skills

A lightweight repository of reusable, verifiable workflows for AI agents.

## Why this repository exists

Agent skills are most useful when they capture a complete user goal, including judgment, safety boundaries, no-op behavior, and verification. Treefolk Skills keeps those workflows portable and maintainable without turning every shell command into another public entry point.

## Design philosophy

The repository favors complete user workflows over command wrappers. A public skill must be a natural request, produce an independently verifiable outcome, and contain enough reusable judgment to justify a name users must remember. Implementation steps stay inside the workflow until independent demand proves otherwise.

Skill bodies live only in `SKILL.md`. Taxonomy lives in metadata and exists primarily to explain the skill set to users and help maintainers classify it. It never determines an installation path or filters which skills are activated: installed skills remain flat, and host adapters treat every top-level public skill uniformly.

## Current skills

| Skill | Category | Domain | Kind | Purpose |
| --- | --- | --- | --- | --- |
| `setup-repo` | core | git | workflow | Safely initialize and perform the first remote push |
| `commit-push` | core | git | workflow | Review, commit, and push daily changes |
| `to-mmd` | core | format | transform | Convert structured information into Mermaid |

## Workflow examples

- “Set up this local project on `main`, connect it to this existing remote, and publish it safely.”
- “Review the changes for this task, commit only those files, and push the current branch.”
- “Turn these service interactions into a Mermaid sequence diagram.”

Each skill defines its own inputs, stop conditions, safety rules, verification, and completion report.

## Installation

The first adapter supports Codex through symlinks. Installation has two layers: the bootstrap acquires a source checkout at `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`, then that checkout's local `setup` activates every top-level public skill for the selected host with safe symlinks.

### Quick install

For the published repository, this command installs the current `main` branch for Codex:

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh | bash -s -- --host codex
```

This is the moving-main channel: rerunning it at a later date may acquire different source. The command is provided for use once the repository is published at that location; it is not a claim that the URL is currently available.

When a pinned release such as `v0.1.0` is available, use the same tag in both the raw installer URL and `--ref`:

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/v0.1.0/install.sh | bash -s -- --host codex --ref v0.1.0
```

That example is for a future published tag; it does not claim that `v0.1.0` currently exists. Keeping the two references identical prevents a moving installer from selecting different source.

To inspect the moving-main installer before running it, download it first:

```sh
curl -fsSL https://raw.githubusercontent.com/treefolk-ai/skills/main/install.sh -o treefolk-install.sh
less treefolk-install.sh
bash treefolk-install.sh --host codex
```

### Local checkout

From an existing local checkout, preview activation before making changes:

```sh
./setup --host codex --dry-run
./setup --host codex
```

The activation destination is selected from `TREEFOLK_SKILLS_DIR`, then `${CODEX_HOME}/skills` when `CODEX_HOME` is set, then `${HOME}/.codex/skills`. `setup` activates every top-level directory containing `SKILL.md`, regardless of taxonomy. Existing files, directories, and unrelated links are never overwritten.

### Verify

After a bootstrap install, verify the source checkout and activation with a non-mutating rerun:

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/setup" --host codex --dry-run
```

A fully activated checkout reports each public skill as already linked and reports no conflicts. For a local checkout, run the same command as `./setup --host codex --dry-run` from its root.

### Update policy

The v0.1 bootstrap refuses to continue when its source installation directory already exists. It never silently replaces or merges a checkout. Updates remain an explicit, user-reviewed operation until a safe updater exists; do not treat rerunning the bootstrap as an in-place update.

### Uninstall

Use the source checkout to preview and remove only the symlinks it owns:

```sh
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex --dry-run
"${TREEFOLK_HOME:-$HOME/.treefolk}/skills/uninstall" --host codex
```

Run `uninstall` before optionally removing the source checkout, because ownership is verified against that checkout.

From an existing local checkout, the equivalent preview and removal commands are:

```sh
./uninstall --host codex --dry-run
./uninstall --host codex
```

No broad cross-agent compatibility claim is made yet. Additional hosts require an implemented and tested adapter.

## Validation

Run the repository checks without installing anything:

```sh
bash -n install.sh
bash -n setup
bash -n uninstall
bash -n scripts/check-skills.sh
./scripts/check-skills.sh
./install.sh --host codex --dry-run
./setup --host codex --dry-run
./uninstall --host codex --dry-run
```

## Adding a skill

Read `DESIGN.md`, `AGENTS.md`, and `templates/SKILL.md.tmpl` first. Apply the granularity test, create one top-level lowercase kebab-case directory whose name matches its frontmatter, fill every required section, and update this README and `DESIGN.md`. Then run the complete validation set.

Do not add a public skill when the capability is only an internal step, a deterministic script, or a speculative future need.

## Safety

The Git workflows inspect repository state and candidate diffs before changing history or remote state. They prohibit force pushes, implicit history reconciliation, remote replacement, automatic amend, global Git configuration changes, and committing suspected secrets. A workflow stops when it cannot prove that the next action is non-destructive.

The bootstrap uses the network to acquire the installer and source over HTTPS. It refuses to overwrite its source installation directory and does not use `sudo` or edit Codex configuration. The local `setup` and `uninstall` adapters use safe symlinks, refuse conflicts, support true dry-runs, and do not access the network.

## Project status

Version 0.1 is intentionally small. Only `core` is active. `make` is planned, while the future category for communication, distribution, adoption, and growth has no final English name. This taxonomy is not yet a stable API and never controls installation or activation.

## License

MIT. See `LICENSE`.
