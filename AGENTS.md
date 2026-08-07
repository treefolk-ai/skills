# Repository guidance

## Repository purpose

This is Treefolk AI's portable repository of reusable agent skills. Maintain it as a small system of complete, verifiable workflows for multiple AI-agent environments, without claiming host compatibility that has not been implemented and tested.

## Canonical sources

- `AGENTS.md` defines repository maintenance rules.
- `DESIGN.md` defines skill design principles and granularity.
- Each skill's `SKILL.md` is the only canonical body for that skill.
- `README.md` is the user-facing entry point.

Do not duplicate skill bodies into `CLAUDE.md`, `CODEX.md`, `GEMINI.md`, `PI.md`, or other host-specific versions. Keep host differences in installers or small adapters.

## Required reading

Before adding or changing a skill, read:

1. `DESIGN.md`
2. The affected `SKILL.md`, when it exists
3. `templates/SKILL.md.tmpl`

Also inspect `README.md` and the validator before changing the public surface or schema.

## Public skill rules

- Represent a natural user goal with an independently verifiable outcome; do not wrap a single command as a public skill.
- Apply the granularity test in `DESIGN.md`. Do not split workflows without evidence of independent user demand.
- Do not add empty skill or category directories.
- Keep public skill directories at the repository root; store taxonomy in metadata, not paths.
- Do not copy a skill for different hosts.
- Update both `README.md` and `DESIGN.md` when adding or removing a public skill.
- Keep implementation steps, private scripts, templates, and references non-public unless they independently earn promotion.

## Installation architecture

- Treat taxonomy as user-facing explanation and maintainer classification only. Host activation must be category-agnostic and activate every top-level public skill; category metadata must never become an installation path or filter.
- Keep acquisition separate from host activation. `install.sh` acquires source at `${TREEFOLK_HOME:-$HOME/.treefolk}/skills`; the acquired checkout's local `setup` is the sole implementation of host activation, even when the bootstrap invokes it.
- Activate new user-level installations in `${HOME}/.agents/skills` so Codex and Grok share one flat discovery target. Preserve existing `${CODEX_HOME}/skills` or `${HOME}/.codex/skills` links during setup; uninstall must inspect both shared and legacy locations and remove only links whose ownership it proves.
- Keep the curl bootstrap self-contained and compatible with the Bash 3.2 shipped by macOS. It must fetch only over HTTPS, never require `sudo`, and refuse to overwrite an existing source installation directory.
- A downloaded `install.sh --dry-run` must perform no network access or filesystem mutation. Validate acquired source before invoking `setup`, and never activate source that fails validation.
- Use pinned, immutable refs for release channels. Documentation and implementation must use the same release tag for acquiring `install.sh` and for its `--ref`; label `main` as a moving channel.
- Maintenance tests must exercise a local installer and must never execute a `curl | bash` pipeline.

## Naming

- Use lowercase kebab-case.
- Make the directory name equal the frontmatter `name`.
- Prefer a short but unambiguous name.
- Describe user intent rather than implementation commands.

## Required sections

Every public `SKILL.md` must have YAML frontmatter with `name`, a clear triggering `description`, and `metadata` values for `treefolk-category`, `treefolk-domain`, and `treefolk-kind`. Its body must contain:

- `Outcome`
- `Use when`
- `Do not use when`
- `Inputs`
- `Preconditions`
- `Workflow`
- `Stop conditions`
- `Safety`
- `Verification`
- `Completion report`

Keep instructions concise and include defaults, branches, no-op behavior, and honest partial outcomes where relevant.

## Safety

Git skills must never force push, delete or rebuild `.git`, overwrite a remote, overwrite remote history, amend automatically, change global Git configuration, stage an unreviewed working tree, commit suspected secrets or `.env` data, or claim success without checking the resulting commit and remote state. Preserve user work and stop on ambiguity or overwrite risk.

Repository maintenance must not perform a real skill installation, modify remotes, create hosted repositories, commit, push, or access the network unless a later user request explicitly authorizes that exact action.

## Validation

After a change, run:

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
```

If the current directory is a Git repository, also run:

```sh
git diff --check
git status --short
```

Fix failures and rerun the complete set. Report what actually ran and distinguish parser validation, static checks, dry-runs, and real side effects.

## Change discipline

- Inspect the working tree before editing and preserve unrelated user changes.
- Keep patches focused and review generated files and executable modes.
- Do not commit or push automatically.
- Do not add, remove, or rewrite remotes during repository maintenance.
- Do not silently weaken checks to make validation pass.
- Report every validation honestly, including no-ops, skipped checks, warnings, and remaining decisions.
