# Treefolk Skills design

## Purpose

Treefolk Skills turns recurring user goals into maintainable agent workflows with explicit outcomes, safety boundaries, and verification. It is not a collection of isolated prompts or command aliases.

“Verifiable” means another observer can check the result from the produced artifact or authoritative state. It does not mean that merely having a `Verification` section, passing package validation, or receiving a successful command exit proves the workflow correct.

## Capability boundaries

| Concept | Role |
| --- | --- |
| Skill | A user-invokable workflow that owns a complete, observable outcome |
| Step | One operation inside a workflow |
| Script | Deterministic implementation or verification support |
| Resource | A template, reference, schema, or example used by a workflow |

For example, `git add` is a step; “review, commit, push, and verify this change” may be a skill. Reuse alone does not make a step, script, or resource a public skill.

## Public skill admission

Before adding a public skill, require clear answers to all of these questions:

1. Would a user naturally request this outcome directly?
2. Can the result be checked independently of the agent's completion claim?
3. Does the workflow contain meaningful judgment, safety boundaries, or branching?
4. Is there evidence that the workflow will be used repeatedly?
5. Is its short, unambiguous name worth adding to the user's mental model?

If the capability is mainly part of another workflow, speculative, or weakly supported by demand, keep it as a step, script, resource, or private implementation detail.

## Composition

Compose capabilities inside the natural user outcome before splitting them into public entries. A selected skill may use commands, scripts, resources, or other host capabilities, but it remains responsible for the complete outcome.

An intermediate artifact can qualify as a skill when users request it directly, producing it requires semantic judgment, and it passes the same admission test. Do not split a workflow merely to make its implementation appear modular.

## Safety and evidence

Any workflow that changes files, history, remote state, or external systems must define preconditions, stop conditions, prohibited actions, post-action verification, and a concrete completion report.

Inspect before acting and verify against authoritative state afterward. Treat successful no-ops and honest partial outcomes as first-class results. Never infer success from an exit code alone.

Keep these evidence levels distinct:

- Package validation proves structure and required metadata.
- Installer tests prove the scenarios they exercise in temporary filesystems.
- Per-run verification proves the observed result of that execution.
- End-to-end or live-host compatibility requires separate behavioral evidence.

## Invocation ownership

Require explicit invocation for workflows with consequential side effects or substantial overlap. Allow implicit matching only when the workflow is low-risk and its triggering description is unambiguous. Host-specific policy belongs in a small adapter; the current tier convention is documented in `docs/skill-priority.md`.

Invocation policy decides how a skill is selected, not how much work it may own. Once selected, one entry point must own authorization, safety checks, stopping, verification, and reporting for its complete outcome; it must not rely on implicit chaining to another side-effecting skill.

## Taxonomy and naming

Taxonomy explains and classifies skills. It must not select installation paths, filter activation, or define invocation behavior; installed public skills remain flat.

Names describe the user's goal rather than an implementation command. Keep them short and unambiguous. Mechanical package naming and schema rules belong to `AGENTS.md`, the template, and the validator.
