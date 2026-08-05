# Treefolk Skills design

## Purpose

Treefolk Skills is a small, portable collection of complete workflows for AI agents. It exists to turn recurring user intent into maintainable procedures with explicit outcomes, safety boundaries, and verification—not to collect isolated prompts or command aliases.

The current public surface is intentionally limited to `setup-repo`, `commit-push`, `pr`, and `to-mmd`.

## Skill vs step vs script vs resource

| Concept | Meaning |
| --- | --- |
| Skill | A user-invokable, repeatable workflow with an independently verifiable outcome |
| Step | One operation inside a workflow |
| Script | Deterministic implementation support |
| Resource | Template, reference, schema, or example used by a skill |

A command such as `git add` is normally a step. A small shell program that performs a stable mechanical check is a script. Neither becomes a public skill merely because it is reusable.

## User intent over command wrappers

Name and design a skill around a goal a user would naturally request. “Commit and push these changes” is a workflow: it includes scope review, secret checks, message selection, push decisions, and verification. “Run `git push`” is an implementation instruction and does not justify a separate skill.

## Granularity test

Before exposing a skill, ask:

1. Would a user naturally request it directly?
2. Does it produce an independent, verifiable outcome?
3. Does it contain non-trivial judgment, workflow, or safety rules?
4. Will it be reused?
5. Is its name worth adding to the user's mental model?

Most answers should be yes. If the capability is mainly one step of an existing workflow, keep it internal.

## Public surface minimization

Every public name is cognitive and maintenance cost. Add only workflows with demonstrated value. Do not create placeholder skills, speculative category directories, or separate skills for each command in a workflow.

## Composition model

Skills may use shell commands, repository scripts, templates, references, or other real capabilities. Composition should happen inside a natural workflow first. Do not split a coherent outcome solely to make the implementation appear modular.

## Intermediate artifacts

An intermediate artifact can still justify a public skill when users also request it directly and producing it requires semantic judgment. `to-mmd` qualifies because selecting a diagram model and preserving relationships is more than changing a file format.

## Safety and verification

Any workflow that changes files, history, or remote state must define preconditions, stop conditions, safety rules, verification, and a concrete completion report. Inspect before acting, verify after acting, and report partial or no-op outcomes precisely. Never infer success from an exit code alone.

## Taxonomy model

Taxonomy is metadata, not an installation path. Installed skills remain flat, while each `SKILL.md` declares `treefolk-category`, `treefolk-domain`, and `treefolk-kind`.

- `core` is the only stable category today.
- `make` is planned for creating products and works, but is not active yet.
- The category for outward communication, distribution, adoption, and growth does not yet have a final English name.
- Do not stabilize `market`, `reach`, or another candidate in directories, validation rules, or compatibility promises before that decision is made.

Future taxonomy is not a stable API. The current skills use `core / git / workflow` for `setup-repo`, `commit-push`, and `pr`, and `core / format / transform` for `to-mmd`.

## Naming rules

- Use lowercase kebab-case.
- Keep names short, verb-led when practical, and unambiguous.
- Describe user intent, not every internal operation.
- Match the directory name and frontmatter `name` exactly.

## Promotion rule

Repeated internal steps may become skills only after they prove independent user demand.

Promotion also requires an independently verifiable result, meaningful judgment or safety value, repeated use, and a name users should reasonably remember. When evidence is weak, retain the capability as a step, script, or resource.

## Anti-patterns

- Thin command wrappers such as separate `init-repo`, `commit`, or `push` skills.
- Excessive atomicity that forces users to orchestrate implementation details.
- Empty categories, speculative skills, or placeholder resource trees.
- Copies of the same skill body for different agent hosts.
- Taxonomy encoded as nested installation directories.
- Side effects without preflight checks, stop conditions, and post-action verification.
- Empty commits, forced work for an already-correct state, or no-op results reported as failures.
- Claims of compatibility, validation, or successful delivery that were not actually verified.
