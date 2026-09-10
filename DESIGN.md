# Treefolk Skills design

## Product map

The product map has three categories: `think` → `make` → `share`. Choose from the user's immediate goal; users invoke a skill directly without choosing a category first.

| Category | User job | Current skills |
| --- | --- | --- |
| `think` | Decide what to do and assess whether results meet the user's goals | `todo`, `human-in-the-loop` |
| `make` | Create or improve a usable artifact | `loop`, `code-craft`, `context-shrink`, `ui-to-desc`, `to-mmd`, `seo`, `geo` |
| `share` | Deliver work to a repository or running environment | `repo`, `push`, `pr`, `deploy` |

The earlier `core` mixed generality with workflow outcomes; its code and diagram skills now belong to `make`, and Git delivery belongs to `share`. The earlier `learn` emphasized evidence retention, while the user's immediate job is judging AI's results against their goals; `human-in-the-loop` therefore belongs to `think`. These changes simplify discovery without merging skills or changing their workflows. Each skill defines its own completion boundary.

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
| `human-in-the-loop` | `think` | `project-progress` | `workflow` | Let the user assess AI's actual results and evidence limits with little attention, and carry their corrections into subsequent work |
| `loop` | `make` | `artifact-quality` | `workflow` | Declare a scoped outcome and reconcile observed gaps within a finite iteration budget, with verifiable acceptance and a clear stopping result |
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

- `think` helps the user understand, decide and assess work against their goals. A plan or evidence record may be its artifact; writing a document alone does not make the outcome `make`.
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

`loop` is an explicitly requested, independent entry point for sustained iteration across artifact types. Its recurring job is to finish a bounded task without requiring the user to prompt every round. The design combines [Ralph Wiggum](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) iteration with the desired-state and reconciliation concepts of [Kubernetes controllers](https://kubernetes.io/docs/concepts/architecture/controller/); it does not require another skill or inherit one domain's workflow. The short name reflects the user's recurring invocation. Fixed acceptance, candidate evidence and distinct success, no-op, partial and blocked outcomes make results inspectable and recoverable. Choosing appropriate criteria and the next corrective action involves judgment beyond a command wrapper. It belongs to `make / artifact-quality / workflow`, with P0 selection because it deliberately overlaps ordinary production workflows.

The public interaction teaches two forms: `$loop [rounds] [acceptance conditions…] [：task]` and `$loop help [task or concern]`. These are conversation inputs interpreted by the agent, not a shell grammar. Users declare the goal; the agent chooses actions from observed gaps. Rounds normally set an upper bound, defaulting to ten, with early completion. An explicit request for a fixed number of checks preserves that intent without forcing edits. Omitted task text inherits only an unambiguous current target. Conditions keep their comparison direction, native units and evidence requirements; missing criteria do not authorize a universal scorecard or speculative extensibility work.

Help is a read-only invocation builder: it uses conversation context and packaged references, suggests a few relevant criteria and a ready-to-use invocation, then stops. The full ten-term industry menu is disclosed on request. This keeps the common path convenient without adding routine approval gates. Status and cancellation remain controls of the active task, rather than additional entry points to learn. Runtime language, configuration schemas and model selection stay out of ordinary help.

The complete workflow lives in `skills/loop/SKILL.md`, supported only by invocation metadata and the criteria reference. Iteration depends on the active agent following the workflow; the package does not include a standalone command runner or provide host-enforced continuation, background execution or automatic recovery. A script belongs here only when it serves an actual execution path, rather than introducing a separate unused interface. Explicit invocation authorizes scoped local work and necessary records only; external actions and Git delivery still need task-specific authorization. Progress and completion require artifact evidence. Better outcome quality than a baseline remains an empirical question, not a consequence of adopting these design references.

`repo` owns first publication end to end. After resolving one unambiguous hosted-repository identity, it queries the provider and may create exactly one empty repository when absence is confirmed. Creation defaults to private; public visibility requires an explicit instruction in the current invocation. Reusing an existing repository never changes its visibility implicitly.

`deploy` owns deployment after a project is prepared. When the user does not name a provider and project evidence does not conflict, it defaults provider selection to Cloudflare—but not to Pages or Workers, an account, a project, an environment, or production. Its normal path updates one exact existing target and verifies authoritative provider state plus the applicable live endpoint; an explicitly named non-Cloudflare provider is supported only through a complete existing project-owned deployment and verification path. Provisioning, Git publication, routing, domains, secrets, migrations, retries after an indeterminate result, rollback, and deletion remain separate explicit work. The `$deploy plan` modifier performs static local inspection only, with no build, network access, file change, or external mutation.

An intermediate artifact can qualify as a skill when users request it directly, producing it requires semantic judgment, and it passes the same admission test. `to-mmd` qualifies because selecting a diagram model and preserving relationships is more than renaming or mechanically converting a file.

`context-shrink` owns behavior-preserving context reduction inside one user-selected repository directory. It must establish protected behavior and a baseline, scan and classify findings, complete a MAP before mutation, verify every item, and verify the final result. Missing scope, performance tuning, type or architecture redesign, business-behavior changes, Git delivery, and external side effects remain outside its boundary. An empty MAP is a successful no-op, while failed or unavailable critical verification is an honest partial result rather than DONE.

`code-craft` owns implementation of one user-defined code outcome from boundary discovery through success and failure verification. It is a language- and framework-neutral decision standard, not a universal folder layout: project idioms determine syntax and structure, while readability, explicit failure behavior, cohesive change boundaries, separation of pure logic from side effects, and evidence-backed completion remain invariant. It may perform the narrow restructuring required to keep a new change coherent, but broad post-hoc behavior-preserving context reduction belongs to `context-shrink`; read-only review, architecture planning, Git delivery, dependency acquisition, deployment, and external mutations remain outside its boundary.

`human-in-the-loop` belongs to `think`: it helps a person judge whether AI's actual results fit their goals, with little attention. Repeated requests to retain evidence or write back judgments about goals, acceptance and tradeoffs justify this entry; the name reflects that human role. `todo` selects a task within the current project; this skill preserves evidence and corrections for the already-selected task. P1 selection applies to those recording requests. Ordinary development, progress questions and AI context recovery do not trigger file writes.

One root `evidence.md` defaults to four fields—goal, verified result, unresolved issues and next verification—for a predictable reading entry. These are the information needed for judgment, not a rigid format: clear equivalent layouts need no rewrite. People can contribute rough notes; AI preserves their meaning and uncertainty, and leaves unchanged records untouched. Compression must retain the evidence and constraints needed for a decision. Judge value by whether the person can distinguish actual results from unknowns, decide whether the work meets their goals, and see corrections affect subsequent work without added upkeep. Record maintenance neither interrupts nor expands existing task authorization. The complete workflow lives only in `skills/human-in-the-loop/SKILL.md`.

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

The Git workflows `repo`, `push`, and `pr`, the deployment workflow `deploy`, and the cross-domain iteration workflow `loop` are P0. `code-craft`, `todo`, `human-in-the-loop`, `to-mmd`, `ui-to-desc`, `context-shrink`, `seo`, and `geo` are P1. The full convention and host configuration live in `docs/skill-priority.md`.

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
