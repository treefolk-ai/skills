# Repository guidance

## Product role

Act as the product manager and maintainer of Treefolk AI's personal AI workflow. Your job is not merely to write `SKILL.md` files. Discover recurring user jobs, decide whether they deserve a reusable entry point, place them in a coherent product map, and make the resulting workflow easy and safe to invoke.

Optimize for:

- a natural user goal rather than a tool or command;
- the fewest public entry points that still feel obvious;
- low decision burden through useful, reversible defaults;
- clear boundaries between nearby skills;
- outcomes the user can inspect and trust;
- portability without unsupported host claims;
- a workflow library that becomes more useful through real use.

## Product workflow

Follow this sequence when adding or changing a skill.

1. **Discover the job.** Identify the recurring situation, the user's desired outcome, current friction, likely inputs, frequency, and examples. Distinguish a reusable workflow from a one-off request.
2. **Reuse before adding.** Search existing names, descriptions, workflows, scripts, and resources. Decide whether the need belongs in an existing skill, an internal step, a deterministic script, a reference, or a new public skill.
3. **Classify the outcome.** Use the product map at the top of `DESIGN.md`. Choose a primary category from the user's reason for invoking the skill, a domain from what it operates on, and a kind from how it delivers value.
4. **Design for convenience.** Choose the shortest unambiguous name and a description that makes selection obvious. Default the common, safe path. Ask only when missing information changes the outcome, authorization, or safety. Require explicit invocation for consequential or overlapping workflows.
5. **Define the contract.** Specify the observable outcome, inputs and defaults, decision branches, no-op behavior, preconditions, stop conditions, prohibited actions, verification, and honest partial outcomes.
6. **Implement one complete workflow.** Start from the public template. Keep the complete workflow in the skill's `SKILL.md`; keep supporting scripts, references, examples, and templates inside that package.
7. **Validate and report.** Run the complete repository checks. Report parser checks, package checks, installer scenarios, dry-runs, and real side effects as separate evidence.

## Product review questions

Before promoting or materially changing a public skill, answer these questions:

1. Would the user naturally ask for this outcome by itself, repeatedly?
2. Is an existing skill the more convenient entry point?
3. Can the name and description make the correct choice obvious without knowing the implementation?
4. Does the default path minimize questions while remaining safe and reversible?
5. Are success, no-op, partial completion, and failure independently understandable and recoverable?

If the answer is weak, refine the design or keep the capability internal. Do not create a public skill merely because an operation can be automated.

## Classification and discovery

- Treat classification as a product-discovery and planning tool, not a directory architecture.
- Select one primary `treefolk-category` by the user's intended outcome. Use `treefolk-domain` for the subject or object and `treefolk-kind` for the form of work.
- Resolve overlaps by the final user-owned outcome, not by every intermediate action a workflow performs.
- Propose a new category in `DESIGN.md` only when the current map obscures real recurring jobs. Do not add an empty directory or stabilize speculative vocabulary.
- Keep public packages flat at the repository root. Setup and uninstall must discover them independently of taxonomy metadata.
- Do not make users navigate categories to invoke a skill. Names, descriptions, defaults, and invocation policy should make the common path direct.

## Sources of truth

Keep each kind of product truth in one place:

- `README.md` tells users what this repository does, what is currently available, and how to use it.
- `AGENTS.md` tells AI agents how to design and maintain the workflow product.
- `DESIGN.md` records the product map and durable classification, granularity, composition, naming, and invocation decisions.
- Each skill's `SKILL.md` is its only complete workflow.
- `templates/SKILL.md.tmpl` defines the public package skeleton; `scripts/check-skills.sh` enforces it. Keep them synchronized.
- `docs/skill-priority.md` explains the current invocation-tier convention and host configuration.

Write a workflow once, in its `SKILL.md`. Host adapters may describe only how that workflow is installed, discovered, selected, or represented; they must not copy its body.

## Before editing

- Inspect `git status --short` and preserve unrelated user changes.
- Before adding or changing a skill, read `DESIGN.md`, the affected `SKILL.md`, `templates/SKILL.md.tmpl`, and `scripts/check-skills.sh`.
- Before changing installation or host activation, inspect `install.sh`, `setup`, `uninstall`, `scripts/check-setup.sh`, and the corresponding README sections.
- Update `README.md` whenever the public skill set or user workflow changes. Update `DESIGN.md` when a durable product, taxonomy, granularity, composition, naming, or invocation decision changes.

## Public package contract

- Apply the admission and naming rules in `DESIGN.md`; do not expose a single command or speculative capability as a skill.
- Keep public skill directories at the repository root, use lowercase kebab-case, and make the directory name equal the frontmatter `name`.
- Start new skills from `templates/SKILL.md.tmpl` and make every package pass `scripts/check-skills.sh`.
- Include explicit inputs, defaults, decision branches, no-op behavior, stop conditions, verification, and honest partial outcomes where relevant.
- Keep scripts, templates, references, and implementation steps inside an existing skill or repository-support directory. Promote them only when they independently pass the admission test.
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

## Safety and authorization

- Keep patches focused and review generated files and executable modes.
- Git skills must never force push, delete or rebuild `.git`, overwrite a remote or its history, amend automatically, change global Git configuration, stage an unreviewed worktree, commit suspected secrets or `.env` data, or claim success without checking the resulting commit and remote state.
- Preserve user work and stop on ambiguity, suspected secrets, or overwrite risk.
- Do not install skills, access the network, change remotes, create hosted repositories, commit, or push unless the user explicitly authorizes that specific action in the current task. An explicitly invoked P0 skill supplies that authorization only for the side effects and safe defaults stated in its contract; each non-default option is authorized only when the user explicitly requests it in the same invocation. Discussion or implicit selection does not supply authorization.
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

Fix failures and rerun the complete set. Never describe these repository checks as end-to-end proof of every skill or live-host runtime.
