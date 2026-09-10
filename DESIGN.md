# Treefolk Skills design

## Product map

The product map has three categories: `think` → `make` → `share`. Choose from the user's immediate goal; users invoke a skill directly without choosing a category first.

| Category | User job | Current skills |
| --- | --- | --- |
| `think` | Decide what to do and reconnect with a project's current progress | `todo`, `human-in-the-loop` |
| `make` | Create or improve a usable artifact | `code-craft`, `context-shrink`, `ui-to-desc`, `to-mmd`, `seo`, `geo` |
| `share` | Deliver work to a repository or running environment | `repo`, `push`, `pr`, `deploy` |

The earlier `core` mixed generality with workflow outcomes; its code and diagram skills now belong to `make`, and Git delivery belongs to `share`. The earlier `learn` emphasized evidence retention, while the user's immediate job is reconnecting with a project; `human-in-the-loop` therefore belongs to `think`. These changes simplify discovery without merging skills or changing their workflows. Each skill defines its own completion boundary.

### Classification axes

| Axis | Question it answers | Current examples |
| --- | --- | --- |
| Category | Where does this outcome belong in the user's AI workflow? | `think`, `make`, `share` |
| Domain | What subject, system, or artifact does it operate on? | `git`, `project-planning`, `project-progress`, `format`, `ui-design`, `source-code`, `hosting`, `discoverability` |
| Kind | What form of work does the skill perform? | `workflow`, `triage`, `transform`, `synthesis` |
| Invocation tier | How may the host select it? This is policy, not taxonomy. | P0 explicit, P1 implicit-capable, P2 disabled |

### Current classification

| Skill | Category | Domain | Kind | Primary user outcome |
| --- | --- | --- | --- | --- |
| `todo` | `think` | `project-planning` | `triage` | Choose one source-backed next action from the current project's task documents |
| `human-in-the-loop` | `think` | `project-progress` | `workflow` | Reconnect with one selected project through a readable record shared by humans and AI, preserving verified progress and human judgment |
| `code-craft` | `make` | `source-code` | `workflow` | Build one scoped code outcome with readable boundaries, explicit failure behavior, and success/failure verification across languages and frameworks |
| `context-shrink` | `make` | `source-code` | `workflow` | Reduce the maintenance context of one bounded source-code scope without changing external behavior |
| `ui-to-desc` | `make` | `ui-design` | `synthesis` | Turn multi-turn UI evidence into one reviewable component design description |
| `to-mmd` | `make` | `format` | `transform` | Produce faithful, editable Mermaid source |
| `seo` | `make` | `discoverability` | `workflow` | Improve search discovery, crawl and index readiness, result presentation, and platform metadata with verified local changes or a read-only audit |
| `geo` | `make` | `discoverability` | `workflow` | Improve answer accuracy and source support in controlled content, distinguishing content verification from observed generative-search citations |
| `repo` | `share` | `git` | `workflow` | Initialize and publish a repository safely, reusing or creating its intended remote |
| `push` | `share` | `git` | `workflow` | Deliver one reviewed change to its intended remote |
| `pr` | `share` | `git` | `workflow` | Publish work as exactly one verified pull request |
| `deploy` | `share` | `hosting` | `workflow` | Deploy one reviewed source state or artifact to one existing hosting target and verify the live result |

## Product intent

Treefolk Skills is the evolving product layer for a personal AI workflow. It turns recurring user goals into named, maintainable workflows so the user can ask for an outcome naturally, trust the decisions made along the way, and improve the process once for future agents and hosts.

The library is not a catalog of everything an agent can do. It should contain the smallest coherent set of workflows that noticeably reduces repeated explanation, decision effort, and execution risk.

“Verifiable” is a design property: the result can be checked from a produced artifact or authoritative state. It is not a claim that every skill has an automated end-to-end test.

## Category design

Choose a category from the user's primary reason for invoking the skill, not from the tools or intermediate steps it happens to use.

- `think` helps the user understand, decide or reconnect with work. A plan or evidence record may be its artifact; writing a document alone does not make the outcome `make`.
- `make` owns creation and transformation of the artifact. Publishing or distributing that artifact belongs to `share` unless publication is inseparable from the natural outcome.
- `share` owns observable communication, publication, distribution, adoption, or growth. Creating collateral alone remains `make`.

Activate or rename a category only when real recurring skills make it improve discovery or roadmap decisions. Do not create one category per tool, customer, content type, or implementation technology. Evidence and feedback can improve every stage without requiring their own category.

## Package layout

All public packages live directly under `skills/<name>/`, separate from repository-level `docs/`, `scripts/` and `templates/`. Each package owns its complete `SKILL.md` and supporting scripts, references, examples, templates and host adapters. Category metadata does not create subdirectories; reclassification must not move a package or change its invocation name.

`setup`, `uninstall`, source acquisition and package validation discover `skills/*/SKILL.md` independently of classification. Host links remain flat at the selected activation directory, such as `~/.agents/skills/<name>`. The checkout path and package directory are separate: a default checkout at `~/.treefolk/skills` contains its packages at `~/.treefolk/skills/skills/<name>`.

Moving packages from the old repository root must preserve existing installations through ownership-checked link migration. `setup` may retarget an exact link to this checkout's absent former package path, including existing links in the legacy Codex directory. It must preserve unrelated links, real files and directories, and any former source path that has been reused. Dry-run reports planned changes without writing; `uninstall` can remove a proven old link directly. Changing the source layout does not itself run installation, change global configuration or prove that a host has refreshed discovery.

## Convenience model

A skill is convenient when the user can express the desired outcome without orchestrating implementation details.

- Prefer one entry point that owns the natural outcome over a chain of small public commands.
- Use short, goal-oriented names and triggering descriptions that distinguish nearby choices.
- Default the common safe path and make no-op behavior successful and explicit.
- Ask only for information that materially changes the result, authorization, or safety.
- Keep high-impact or overlapping workflows explicit; allow implicit matching only when the workflow is focused, uniquely described, authorized by the current request, and keeps risk controlled through a bounded scope, stop conditions, and verification.
- Make partial completion useful: preserve completed safe work, identify the exact boundary, and say what remains.
- Do not require users to know category, domain, kind, host adapter, or internal composition in order to invoke a skill.

Convenience does not mean hiding consequential behavior. It means placing decisions at the right level: the skill handles routine judgment, while the user retains control over irreversible, ambiguous, or externally visible choices.

## Capability boundaries

| Concept | Product role |
| --- | --- |
| Skill | A user-invokable workflow that owns a complete, observable outcome |
| Step | One operation inside that workflow |
| Script | Deterministic implementation or verification support |
| Resource | A template, reference, schema, or example used by a workflow |

For example, `git add` is a step; “review, commit, push, and verify this change” may be a skill. Reuse alone does not make a step, script, or resource a public product entry.

## Public skill admission

Before adding a public skill, require clear answers to all of these questions:

1. Would a user naturally request this outcome directly and repeatedly?
2. Can the result be checked independently of the agent's completion claim?
3. Does the workflow contain meaningful judgment, safety boundaries, or branching?
4. Is an existing skill an equally natural and more convenient owner?
5. Is the proposed name distinct enough to deserve space in the user's mental model?

A new skill should normally pass questions 1–3 and 5, with question 4 answered no. Otherwise keep the capability as a step, script, resource, private workflow, or addition to an existing skill until real use proves a separate entry point.

## Scope and composition

Compose capabilities inside the natural user outcome before splitting them into public entries. A selected skill may use commands, scripts, resources, or host capabilities, but it remains responsible for authorization, stopping, verification, and reporting across the complete outcome.

`repo` owns first publication end to end. After resolving one unambiguous hosted-repository identity, it queries the provider and may create exactly one empty repository when absence is confirmed. Creation defaults to private; public visibility requires an explicit instruction in the current invocation. Reusing an existing repository never changes its visibility implicitly.

`deploy` owns deployment after a project is prepared. When the user does not name a provider and project evidence does not conflict, it defaults provider selection to Cloudflare—but not to Pages or Workers, an account, a project, an environment, or production. Its normal path updates one exact existing target and verifies authoritative provider state plus the applicable live endpoint; an explicitly named non-Cloudflare provider is supported only through a complete existing project-owned deployment and verification path. Provisioning, Git publication, routing, domains, secrets, migrations, retries after an indeterminate result, rollback, and deletion remain separate explicit work. The `$deploy plan` modifier performs static local inspection only, with no build, network access, file change, or external mutation.

An intermediate artifact can qualify as a skill when users request it directly, producing it requires semantic judgment, and it passes the same admission test. `to-mmd` qualifies because selecting a diagram model and preserving relationships is more than renaming or mechanically converting a file.

`context-shrink` owns behavior-preserving context reduction inside one user-selected repository directory. It must establish protected behavior and a baseline, scan and classify findings, complete a MAP before mutation, verify every item, and verify the final result. Missing scope, performance tuning, type or architecture redesign, business-behavior changes, Git delivery, and external side effects remain outside its boundary. An empty MAP is a successful no-op, while failed or unavailable critical verification is an honest partial result rather than DONE.

`code-craft` owns implementation of one user-defined code outcome from boundary discovery through success and failure verification. It is a language- and framework-neutral decision standard, not a universal folder layout: project idioms determine syntax and structure, while readability, explicit failure behavior, cohesive change boundaries, separation of pure logic from side effects, and evidence-backed completion remain invariant. It may perform the narrow restructuring required to keep a new change coherent, but broad post-hoc behavior-preserving context reduction belongs to `context-shrink`; read-only review, architecture planning, Git delivery, dependency acquisition, deployment, and external mutations remain outside its boundary.

`human-in-the-loop` owns reconnecting with one already-selected project, preserving what can actually be trusted, and carrying human judgment into the next action. Its source is the user's excerpt from a ChatGPT scheduled daily briefing, proposing four lines in a root `evidence.md`, then continuing existing development. Subsequent design discussion makes it a shared human and AI record: four stable fields with readable spacing, not four physical lines. Value is tested by whether a later session can reconnect more easily and the human can regain understanding without a new maintenance task. These are product requirements, not findings attributed to the studies named in the briefing.

The public name stays `human-in-the-loop` because the user already recognizes that entry point and its intended human role; `evidence.md` is its artifact, not a second skill. `todo` selects a task; this skill reconnects with and records the selected one. It qualifies independently through repeated return, pause and feedback situations, a reviewable record, and decisions about evidence freshness, unresolved acceptance and next verification. Its primary category is `think`: the user regains understanding of the current project and where to continue. Actual observations and corrections remain useful after the chat ends. Returning to a project is a branch of this workflow, not another public mode or command.

The four fields reduce different burdens: `Current goal` restores the intended result and its meaningful constraints; `Last verified result` makes real progress visible; `Known failure` keeps uncertainty and human rejection from disappearing; `Next verification` provides one startable action with an observable decision. AI maintains the record; humans may read, contribute rough fragments, correct it, or decline to participate. Polishing must preserve meaning and distinguish intention, observation and uncertainty. User experience and tradeoffs cannot be erased merely because tests pass. Human takeover is reserved for decisions that actually require a person; no ritual approval, activity tracking or artificial handoff is required. Existing permission to continue development remains in force across a checkpoint.

Each project has one root record, with no dated copies, backups or expanding history. It contains only the selected goal and relevant unresolved work, not a second TODO list. An explicit task switch reuses it without another confirmation and preserves applicable constraints. Rough current-task notes can be organized; unrelated archives and protected original text remain intact. Unchanged, readable records do not get rewritten or receive fresh verification dates. A completed goal does not require a replacement task. P1 discovery applies to clear reconnecting, handoff or record-maintenance requests, not every coding task. The complete workflow, field rules and recovery branches live only in `skills/human-in-the-loop/SKILL.md`.

When explicitly requested, minimal project integration may add a local `AGENTS.md` pointer to `evidence.md` while preserving existing guidance. This makes the record easier to find without duplicating the skill's workflow or creating a mandatory onboarding document. General Agent environment preparation has no demonstrated separate recurring job here and does not justify another public skill. A pointer is not proof that every host or later session will load it.

Attention benefits are design hypotheses, not measured clinical or productivity outcomes. Evaluation checks whether the user can understand the current result without rereading a chat, whether a next action is concrete, whether corrections change subsequent behavior, and whether the record avoids unnecessary questions and upkeep. Diagnostic labels are not stored in project evidence. Installation provides discovery, not monitoring, scheduled reminders or guaranteed loading in every future session.

`seo` and `geo` are separate public workflows because users independently ask for search discovery and for accurate, supported answers in generative search. `seo` owns search intent, crawl/index readiness, result presentation, and repository or package metadata. `geo` owns question-to-claim evidence, entity and version clarity, corrections to controlled content, and observed citation support. This is a product boundary, not a claim that search providers use wholly separate ranking systems. Neither skill requires the other to be installed or run.

Public `AGENTS.md` content belongs in `geo` when it helps answer the target reader's questions, alongside existing README and documentation sources. Purpose, installation, running, verification and limits are optional content perspectives, not a required file or five-field template. Reuse authoritative facts without duplicating their maintenance; preserve development instructions and authorization boundaries. Listing a command does not prove execution, and a filename does not prove ranking or citation gains. Internal `evidence.md` may inform fact checking but is not automatically published or treated as a publicly accessible source. Full Agent environment setup remains outside this outcome.

When both are requested, share the project facts and access observations, assign technical and metadata changes to `seo`, and assign answer-evidence changes to `geo`. Merge edits to shared prose once and verify the combined result. Explicit targets override inference from the current project; there is no universal GitHub-first default. Both are `make / discoverability / workflow` and P1 because their default deliverable is a verified local artifact or read-only audit, with concrete remote recommendations. Skill selection does not authorize public exposure, remote mutations, Git delivery, deployment, publication, or outreach; an already authorized action retains its original scope.

Split an existing skill only when users repeatedly want the sub-outcomes independently, the resulting names are clearer than the original, and neither entry requires the user to reconstruct the old workflow manually.

## Workflow contract

Every public skill must define:

- one observable outcome;
- natural use and non-use cases;
- required inputs, optional inputs, and defaults;
- preconditions and ordered decision branches;
- successful no-op behavior;
- stop conditions and prohibited actions;
- verification against the artifact or authoritative state;
- a completion report that distinguishes success, partial completion, warnings, and untouched work.

Any workflow that changes files, history, remote state, or an external system must inspect before acting and verify afterward. Never infer success from a command exit code alone.

Keep evidence levels distinct:

- Package validation proves structure and required metadata.
- Installer tests prove only the scenarios exercised in temporary filesystems.
- Per-run verification proves the observed outcome of that execution.
- End-to-end or live-host compatibility requires separate behavioral evidence.

## Invocation ownership

Invocation policy decides how a host may select a skill; it does not determine category or workflow scope.

- P0 requires explicit invocation for consequential or substantially overlapping workflows.
- P1 allows explicit or description-based selection for focused workflows whose outcome is already authorized by the current request and whose risk is controlled through a bounded scope, stop conditions, and verification.
- P2 disables a workflow through host configuration when it should not participate in selection.

The Git workflows `repo`, `push`, and `pr` and the deployment workflow `deploy` are P0. `code-craft`, `todo`, `human-in-the-loop`, `to-mmd`, `ui-to-desc`, `context-shrink`, `seo`, and `geo` are P1. The full convention and host configuration live in `docs/skill-priority.md`.

Once selected, one entry point owns its complete outcome. A side-effecting skill must not depend on a host implicitly discovering and chaining another side-effecting skill to finish authorization, safety checks, verification, or reporting.

## Naming and evolution

- Use lowercase kebab-case and match the directory name to frontmatter `name`.
- Prefer a short verb or goal the user would naturally remember.
- Name the outcome, not the implementation command or every internal step.
- Check names and descriptions together for search collisions and ambiguous triggering.
- Treat renames, category activation, category migration, and invocation changes as product decisions. Update the metadata, README, DESIGN, adapters, and checks that express them in the same change.
- Let repeated use expose missing boundaries. Do not pre-create placeholder skills or empty category directories.

## Anti-patterns

- A public wrapper for one command or one trivial parameter choice.
- Many atomic skills that make the user orchestrate the original workflow.
- A general-purpose category that becomes a dumping ground for unrelated outcomes.
- Categories based on tools rather than user outcomes.
- Empty categories, speculative packages, or placeholder resource trees.
- Copies of one workflow body for different hosts.
- Taxonomy encoded as nested installation paths or activation filters.
- Side effects without preflight checks, stop conditions, and post-action verification.
- A default that saves a question by silently increasing risk.
- Empty commits, forced work for an already-correct state, or no-op results reported as failures.
- Claims of compatibility, validation, or delivery that were not actually verified.
