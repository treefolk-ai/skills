# Repository guidance

## Scope and source ownership

This repository contains Treefolk AI's reusable agent skills. Every public skill must define an observable outcome, safety boundaries, and the checks required before reporting success. This is a design requirement, not a claim that every workflow has an automated end-to-end test.

Keep each kind of truth in one place:

- `AGENTS.md` defines repository maintenance rules.
- `DESIGN.md` defines stable skill-design and granularity decisions.
- Each skill's `SKILL.md` is its only complete workflow.
- `README.md` describes the current public surface and user workflows.
- `templates/SKILL.md.tmpl` defines the public package skeleton; `scripts/check-skills.sh` enforces it. Keep them synchronized.
- `docs/skill-priority.md` explains the current invocation-tier convention and host configuration.

Host adapters may contain installation, discovery, invocation-policy, or metadata differences, but must not duplicate a skill workflow.

## Before editing

- Inspect `git status --short` and preserve unrelated user changes.
- Before adding or changing a skill, read `DESIGN.md`, the affected `SKILL.md`, `templates/SKILL.md.tmpl`, and `scripts/check-skills.sh`.
- Before changing installation or host activation, inspect `install.sh`, `setup`, `uninstall`, `scripts/check-setup.sh`, and the corresponding README sections.
- Update `README.md` whenever the public skill set or user workflow changes. Update `DESIGN.md` only when a stable design, granularity, invocation, or taxonomy decision changes.

## Public package contract

- Apply the admission and naming rules in `DESIGN.md`; do not expose a single command or speculative capability as a skill.
- Keep public skill directories at the repository root, use lowercase kebab-case, and make the directory name equal the frontmatter `name`.
- Start new skills from `templates/SKILL.md.tmpl` and make every package pass `scripts/check-skills.sh`.
- Include explicit inputs, defaults, decision branches, no-op behavior, stop conditions, verification, and honest partial outcomes where relevant.
- Keep scripts, templates, references, and implementation steps inside an existing skill or repository-support directory. Promote them to a top-level skill only when they independently pass the admission test.
- Do not add empty skill or category directories.

## Installer and host contract

- `setup` and `uninstall` must discover every top-level `*/SKILL.md` package independently of category metadata.
- Keep source acquisition separate from activation. `install.sh` acquires source at `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`; the acquired checkout's `setup` is the only activation implementation.
- New user-level installations activate in `${HOME}/.agents/skills`. Preserve existing `${CODEX_HOME}/skills` or `${HOME}/.codex/skills` links; uninstall may remove shared or legacy links only after proving ownership.
- Keep the curl bootstrap self-contained and compatible with macOS Bash 3.2. It must use HTTPS, require no `sudo`, and refuse to overwrite an existing source directory.
- A downloaded `install.sh --dry-run` must perform no network access or filesystem mutation. Validate acquired source before activation.
- Use immutable refs for release channels. Documentation and implementation must use the same release tag for the installer URL and `--ref`; identify `main` as a moving channel.
- Maintenance tests must exercise the local installer and must never execute a `curl | bash` pipeline.
- Describe host compatibility by capability: acquisition, activation, discovery, invocation policy, and uninstall. Claim only capabilities that have been implemented and tested, and label partial support explicitly.

## Safety and change discipline

- Keep patches focused and review generated files and executable modes.
- Git skills must never force push, delete or rebuild `.git`, overwrite a remote or its history, amend automatically, change global Git configuration, stage an unreviewed worktree, commit suspected secrets or `.env` data, or claim success without checking the resulting commit and remote state.
- Preserve user work and stop on ambiguity, suspected secrets, or overwrite risk.
- Do not install skills, access the network, change remotes, create hosted repositories, commit, or push unless the user explicitly authorizes that specific action in the current task.
- Do not weaken checks merely to make validation pass.

## Validation

After any change, run the complete local validation set:

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

Fix failures and rerun the complete set. Report parser checks, static package checks, installer regression tests, dry-runs, and real side effects as separate evidence. Never describe these repository checks as end-to-end proof of every skill or live host runtime.
