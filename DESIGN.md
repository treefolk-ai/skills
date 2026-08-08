# Treefolk Skills design

## Product map

`core` supports the whole personal AI workflow. The product loop is `think` → `make` → `share` → `learn`; `core` and `make` currently contain public skills.

| Category | User job | Completion boundary | Current skills | Status |
| --- | --- | --- | --- | --- |
| `core` | Operate recurring AI-assisted work safely with reusable foundations and cross-cutting utilities | The common workflow or intermediate artifact is complete and independently inspectable | `repo`, `push`, `pr`, `to-mmd` | Active |
| `think` | Turn information or uncertainty into understanding, a decision, or a plan | The reasoning artifact can be reviewed; no final product is required | None | Product direction |
| `make` | Turn intent or a decision into a usable product or creative artifact | The artifact exists and has been checked; publication is outside the boundary | `ui-to-desc` | Active |
| `share` | Help finished work reach and make sense to its intended audience | Publication, communication, distribution, or adoption has an observable result | None | Working category |
| `learn` | Turn outcomes and feedback into reusable knowledge or a better workflow | The learning is preserved for future work, not only stated in the current conversation | None | Product direction |

Only `core` and `make` are active taxonomy today. Directional rows guide discovery and product planning; they do not promise future skills, create installation paths, or claim implemented capability. `share` is a working name for outward communication, distribution, adoption, and growth and should be reconsidered when real skills make that boundary concrete.

### Classification axes

| Axis | Question it answers | Current examples |
| --- | --- | --- |
| Category | Where does this outcome belong in the user's AI workflow? | `core`, `make` |
| Domain | What subject, system, or artifact does it operate on? | `git`, `format`, `ui-design` |
| Kind | What form of work does the skill perform? | `workflow`, `transform`, `synthesis` |
| Invocation tier | How may the host select it? This is policy, not taxonomy. | P0 explicit, P1 implicit-capable, P2 disabled |

### Current classification

| Skill | Category | Domain | Kind | Primary user outcome |
| --- | --- | --- | --- | --- |
| `repo` | `core` | `git` | `workflow` | Initialize and publish a repository safely for the first time |
| `push` | `core` | `git` | `workflow` | Deliver one reviewed change to its intended remote |
| `pr` | `core` | `git` | `workflow` | Publish work as exactly one verified pull request |
| `to-mmd` | `core` | `format` | `transform` | Produce faithful, editable Mermaid source |
| `ui-to-desc` | `make` | `ui-design` | `synthesis` | Turn multi-turn UI evidence into one reviewable component design description |

## Product intent

Treefolk Skills is the evolving product layer for a personal AI workflow. It turns recurring user goals into named, maintainable workflows so the user can ask for an outcome naturally, trust the decisions made along the way, and improve the process once for future agents and hosts.

The library is not a catalog of everything an agent can do. It should contain the smallest coherent set of workflows that noticeably reduces repeated explanation, decision effort, and execution risk.

“Verifiable” is a design property: the result can be checked from a produced artifact or authoritative state. It is not a claim that every skill has an automated end-to-end test.

## Category design

Choose a category from the user's primary reason for invoking the skill, not from the tools or intermediate steps it happens to use.

- `core` is not a synonym for “important” or “frequent.” It is the active starting layer for broadly reusable workflow foundations. Revisit current assignments when a new product family becomes concrete enough to improve discovery.
- `think` ends in a decision, model, synthesis, or plan. If the requested final result is a document, diagram, application, or other usable artifact, prefer `make`.
- `make` owns creation and transformation of the artifact. Publishing or distributing that artifact belongs to `share` unless publication is inseparable from the natural outcome.
- `share` owns observable communication, publication, distribution, adoption, or growth. Creating collateral alone remains `make`.
- `learn` closes the loop by preserving evidence, lessons, or workflow improvements for later use. Solving only the present decision remains `think`.

Activate or rename a category only when real recurring skills make it improve discovery or roadmap decisions. Do not create one category per tool, customer, content type, or implementation technology. Categories remain metadata; public skill packages and host activation remain flat.

## Convenience model

A skill is convenient when the user can express the desired outcome without orchestrating implementation details.

- Prefer one entry point that owns the natural outcome over a chain of small public commands.
- Use short, goal-oriented names and triggering descriptions that distinguish nearby choices.
- Default the common safe path and make no-op behavior successful and explicit.
- Ask only for information that materially changes the result, authorization, or safety.
- Keep high-impact or overlapping workflows explicit; allow implicit matching only when the workflow is low-risk and uniquely described.
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

An intermediate artifact can qualify as a skill when users request it directly, producing it requires semantic judgment, and it passes the same admission test. `to-mmd` qualifies because selecting a diagram model and preserving relationships is more than renaming or mechanically converting a file.

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
- P1 allows explicit or description-based selection for focused, low-risk workflows.
- P2 disables a workflow through host configuration when it should not participate in selection.

The Git workflows `repo`, `push`, and `pr` are P0. `to-mmd` and `ui-to-desc` are P1. The full convention and host configuration live in `docs/skill-priority.md`.

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
- `core` as a dumping ground for every useful capability.
- Categories based on tools rather than user outcomes.
- Empty categories, speculative packages, or placeholder resource trees.
- Copies of one workflow body for different hosts.
- Taxonomy encoded as nested installation paths or activation filters.
- Side effects without preflight checks, stop conditions, and post-action verification.
- A default that saves a question by silently increasing risk.
- Empty commits, forced work for an already-correct state, or no-op results reported as failures.
- Claims of compatibility, validation, or delivery that were not actually verified.
