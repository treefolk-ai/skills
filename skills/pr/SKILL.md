---
name: pr
description: Review current Git work, create a safe topic branch when needed, publish the intended commits, and create or reuse a verified pull request; use when local work should be proposed for review without rewriting history.
metadata:
  treefolk-category: share
  treefolk-domain: git
  treefolk-kind: workflow
---

# Open a pull request

## Outcome

Produce exactly one open pull request from a safely published source branch to the intended base branch, with an accurate title, body, readiness state, and verified remote head. Reuse a matching open pull request as a no-op instead of creating a duplicate. If publication cannot be completed safely, preserve local and remote state and report the partial outcome.

## Use when

- Current local work should be proposed for review as a pull request.
- Work is still on the repository's base branch and needs a topic branch before publication.
- A topic branch has changes or commits that still need to be reviewed, committed, pushed, and proposed.
- A matching pull request may already exist and should be verified or reused rather than duplicated.

## Do not use when

- The repository still needs initialization, remote setup, or its first push; use `repo`.
- The user only wants current changes committed and pushed without a pull request; use `push`.
- The request is only to review, merge, close, or administratively manage an existing pull request; handle that narrower lifecycle action directly.
- Local or remote history needs a merge, rebase, reset, amend, force update, or other reconciliation before it can be proposed.

## Inputs

- Required: access to the intended local repository and an authenticated provider capability that can query and create pull requests.
- Optional: target directory, task scope, source branch name, source remote or fork, base repository and branch, title, body, draft state, and issue references.
- Defaults: current directory; the current non-base branch when suitable; otherwise a branch name derived from repository conventions or `work/<short-kebab-summary>`; the provider-reported default branch as base; title and body derived from the committed diff and repository template; ready for review unless draft was requested; and reuse of one matching open pull request.

## Preconditions

- Confirm the repository root, non-detached `HEAD`, current branch and commit, worktree status, staged and unstaged diffs, untracked names, worktrees, remotes, and upstreams.
- Read applicable repository instructions, contribution guidance, pull request templates, branch naming rules, and required validation commands.
- Identify the hosting provider, authenticated account, base repository, provider-reported default branch and exact remote tip, writable source remote or fork, and their relationship. Do not infer `main` merely from a local branch name.
- Refresh or query the relevant remote refs before comparing history. Sanitize remote URLs before reporting them.
- Separate current-task work from unrelated changes and inspect candidate files, diffs, commit messages, and proposed pull request text for secrets, credentials, private keys, `.env` data, generated output, and unexplained large files.
- Query open, closed, and merged pull requests for the prospective source and base when the provider supports it, so duplicate or incompatible prior work is known before creation.

## Workflow

1. Resolve the target repository, provider, base repository and branch, and writable source destination. Explicit inputs and repository instructions take precedence; otherwise use provider metadata and an unambiguous configured remote relationship. Stop rather than guessing among plausible bases, remotes, forks, or repositories.
2. Refresh the relevant base and source refs, record the exact provider base tip, and compare them with local `HEAD`. Keep that recorded remote base tip as the comparison point even when the checked-out local base contains intended commits. Stop on unrelated history, unexpected remote-ahead or divergent source state, or a base state that makes the proposed diff unreliable.
3. Select the source branch.
   - **Already on a non-base branch:** preserve its name and remain on it. Do not create or switch branches merely to improve naming.
   - **On the verified base with coherent current-task changes or commits:** choose the user-supplied branch name, otherwise follow a documented repository convention or derive `work/<short-kebab-summary>`. Validate the name and confirm it is unused by local refs, remote refs, and other worktrees, then create and switch to it at the current commit before staging or committing. This is the only automatic branch-creation case.
   - **On the verified base with nothing to propose:** return a no-op without creating a branch or pull request.
4. Review all current-task changes. Keep unrelated work untouched. If unrelated content is already staged or files cannot be separated safely, stop for scope direction instead of resetting, unstaging, stashing, or combining work.
5. When a commit is needed, stage only explicit reviewed paths or selected hunks, re-read the staged diff, derive an accurate message in the repository's style, and create a new commit without amending. If the worktree is clean, require at least one intended commit in the source-versus-recorded-base-tip range.
6. Verify every new commit's hash, parent, message, and exact paths. Run the repository-required and task-relevant validations that are locally available, recording commands and results honestly. Do not invent successful tests or silently convert a requested ready pull request into a draft.
7. Resolve the push destination from the configured upstream or one uniquely intended writable remote. Push only a new source branch or a provable fast-forward update, establishing a same-named upstream when needed. Never force. Re-query the remote and require its source tip to equal local `HEAD` before proceeding.
8. Inspect the committed `recorded-provider-base-tip...source` range and diff after publication. Require a non-empty, coherent change set that contains the intended work and no unexpected commits, unrelated files, or suspected secrets.
9. Query pull requests again using the exact source repository, source branch, and base.
   - If one matching open pull request exists, reuse it. Preserve its author-written title, body, base, and draft state unless the user explicitly requested a compatible update; make no change when it already satisfies the request.
   - If multiple matches exist, or only a closed or merged pull request conflicts with the requested identity, stop rather than choosing, reopening, or duplicating it automatically.
10. When no match exists, derive a concise title and truthful body from the committed diff, repository template, and actual validation results. Preserve required template sections, distinguish failed or unrun checks, and include issue references only when supplied or established. Create one pull request with the requested readiness state. Do not add reviewers, assignees, labels, milestones, auto-merge, or other policy choices unless explicitly requested.
11. Re-query the provider and verify the pull request's repository, number, URL, open state, base, source repository and branch, remote head commit, title, and draft or ready state. Inspect local status again and report remaining unrelated or uncommitted work.

## Stop conditions

- The target is not a Git repository, `HEAD` is detached, or the current branch, task scope, base, source repository, source remote, or provider is ambiguous.
- An automatic branch name is invalid, already exists locally or remotely, is checked out in another worktree, or cannot be derived without guessing the task's meaning.
- Candidate work mixes unrelated changes, contains suspected secrets or unreviewed generated material, or cannot form a coherent committed diff.
- Commit identity is missing, required hooks fail, or a new commit cannot be verified.
- The source remote is ahead, divergent, unrelated, not writable, or cannot be inspected well enough to prove a normal push is safe.
- There is no committed difference between base and source, the committed range contains unexpected work, or repository policy requires validations that have not passed for a ready pull request.
- Pull request authentication is unavailable, duplicate identity is ambiguous, an incompatible closed or merged pull request exists, or provider state cannot be verified after creation.

## Safety

- Never force push, amend automatically, rewrite history, reset, rebase, merge, delete or rename branches, replace remotes, rebuild `.git`, or modify global Git configuration.
- Create and switch branches automatically only from the verified base under the source-selection rule. Never overwrite an existing ref or switch away from an established non-base branch automatically.
- Never stage the whole worktree as a substitute for review, disturb unrelated user work, or commit likely secrets, credentials, private keys, `.env` contents, or unreviewed generated files.
- Never create a hosted repository or fork, change branch protection, expose credentials in a URL, or claim a push or pull request succeeded from a command exit code alone.
- Never fabricate change summaries, issue links, validation results, reviewers, or readiness. Do not merge, enable auto-merge, or close a pull request as part of this workflow.

## Verification

- Confirm the selected source branch and base are the intended refs and record whether the source branch was preserved or newly created.
- For each new commit, verify its identity and exact file set; verify the remote source tip equals local `HEAD` after pushing.
- Review the final `recorded-provider-base-tip...source` commits and diff for scope, unexpected content, suspected secrets, and a non-empty proposed change.
- Query the provider after creation or reuse and confirm one open pull request has the intended repository, base, source repository and branch, head commit, title, URL, and draft or ready state.
- Verify remaining local changes and distinguish parser, static, local test, CI, and unrun validation results.

## Completion report

Report the repository, base, source remote and branch, whether a branch was created automatically, commits created or reused, push and upstream result, pull request number and URL, created or reused status, title, draft or ready state, validation commands and results, remaining local changes, and every warning or incomplete step. For a no-op, state whether nothing was available to propose or an existing pull request already satisfied the request.
