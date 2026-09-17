---
name: push
description: Review current Git changes, create a scoped and meaningful commit when needed, and safely push the current branch; use for routine delivery of local work to its intended remote.
metadata:
  treefolk-category: share
  treefolk-domain: git
  treefolk-kind: workflow
---

# Commit and push

## Outcome

Deliver the current task's reviewed changes as a meaningful commit on the current branch and verify that the intended remote received it. If there are no local changes but unpushed commits exist, push them without making another commit. If neither exists, return a successful no-op.

## Use when

- Finished local work should be reviewed, committed, and pushed.
- A clean worktree may contain commits that still need to reach the remote.
- Unrelated local changes must remain untouched while the current task is delivered.

## Do not use when

- The project has not been initialized or connected for its first push; use `repo`.
- History needs rebasing, merging, resetting, amending, or force-updating; handle that as an explicit history operation.
- The user only wants a review or a local commit with no push; follow that narrower request directly.

## Inputs

- Required: no value beyond access to the intended local repository.
- Optional: target directory, task scope, explicit paths, and a commit message.
- Optional mode: `safe`, invoked as `$push safe`, for full pre-push and post-push verification.
- Defaults: the streamlined path; current directory, current branch, its configured upstream, task-related reviewed changes only, and a concise message derived from the actual diff in the repository's existing style.

## Default mode

By default, `$push` runs the streamlined path: start immediately without presenting a plan or asking for workflow confirmation when the scope and configured upstream are unambiguous.

- Keep all Safety and Stop conditions.
- Inspect repository state and candidate paths once, with no extra scans.
- Stage only reviewed task paths and run `git diff --cached --check`.
- Commit only when needed, then perform one normal non-force push.
- Avoid pre-commit staged/unstaged diff repetition, skip pre-push fetch/history comparison, detailed commit metadata verification, commit-style lookup, and identity preflight.
- After pushing, prefer a lightweight reachability check only (`git ls-remote` against the target branch). Do not run additional history comparisons.
- Keep the completion report brief.
- If scope or destination is ambiguous, stop quickly and suggest `$push safe`.

## Safe mode

When the user invokes `$push safe`, run the full verification path for extra care on shared or complex repositories.

- Present a plan and confirm the workflow before acting.
- Re-read repository state and staged/unstaged diffs as needed to confirm the commit contains only the intended change.
- Look up the repository's recent commit style before deriving the message, and preflight Git identity.
- Fetch and compare local and remote history before pushing; push only a new branch or a fast-forward update.
- Verify the new commit's hash, message, parent, and exact changed paths.
- After pushing, refresh or query the remote and confirm its branch tip contains the delivered commit with no unexpected ahead/behind state.
- Produce a detailed completion report.

## Preconditions

- Confirm the target is a Git repository and identify its root, current branch, `HEAD`, remotes, and upstream in a single repo/branch snapshot; avoid repeated or auxiliary checks.
- Stop on detached `HEAD`; do not switch branches automatically.
- Read `git status` and candidate paths once before staging anything.
- Skip listing all untracked names and skip a separate staged-diff pre-read unless explicitly required for an already-staged commit.
- Separate current-task changes from obvious unrelated work. Inspect mixed files carefully rather than assuming each whole file belongs in one commit.
- Check candidate files and diffs for `.env` data, tokens, credentials, private keys, generated output, logs, and unexplained large files without echoing secret values.
- When a commit is needed, confirm Git identity and account for repository hooks or contribution rules.
  - Safe mode: preflight identity and hook configuration explicitly before committing.

## Workflow

1. Resolve the repository, current branch, remotes, and upstream in one pass; determine whether the destination exists enough to avoid ambiguous routing. Stop if the destination cannot be determined safely.
   - Safe mode: also refresh the relevant remote-tracking state and inspect how the destination tip relates to `HEAD` before classifying pending work.
2. Classify the state after reviewing status and the candidate diff once.
   - **Changes exist:** identify one coherent commit scope. Leave unrelated changes untouched and report them. If unrelated work is already staged, do not silently unstage or reset it; stop for direction unless a safe, explicitly authorized isolation is available. If the intended changes represent multiple independent tasks, stop for scope guidance or create only the clearly authorized commit; do not combine them for convenience.
   - **Worktree is clean, commits are ahead:** skip commit creation and continue to the push checks. With no upstream, an absent intended remote branch makes existing local commits pending as a new-branch push; do not misclassify that state as a no-op.
   - **Worktree is clean, no commits are ahead:** return a successful no-op stating that nothing needs committing or pushing.
3. For a commit, stage only explicit, reviewed paths or safely selected hunks. Never use a blanket `git add .`. Run one staged diff check (`git diff --cached --check`) and ensure the staged content contains the complete intended change, no unrelated work, and no suspected secret.
   - Safe mode: re-read the staged diff in full and confirm the complete intended change without unrelated work before committing.
4. Derive a short, accurate message from the staged diff. Prefer an established recent repository style when it was inspected. When no style lookup was performed or history is inconsistent, use:
   ```text
   <icon> <type>(<scope>): <summary>

   <body>
   ```
   Choose a conventional icon/type pair for the dominant change, keep the type in English, omit the scope only for truly global work, and follow the user's language for the summary and body. Keep the title concise. For a non-trivial commit, include concise bullets covering every material change point; a trivial one-point change may omit the body. Use a user-supplied message only when it still describes the staged content. Create a new commit without amending.
   - Safe mode: look up recent repository commit style before deriving the message.
5. Verify the new commit by inspecting its hash and basic staged intent. Ensure any unstaged or untracked files remain as expected.
   - Safe mode: also verify the commit's message, parent, and exact changed paths.
6. Determine the push destination. Use the configured upstream when present. Without one, establish an upstream for the same current branch only when `origin` is the unique, clearly intended remote and the same-named remote branch is absent or safely related. Stop on multiple plausible remotes or branch ambiguity.
7. Push with one normal non-force push. Stop if the destination is clearly invalid or unreachable, or if the remote rejects the push; do not force, merge, rebase, reset, switch branches, or repeat speculative pushes.
   - Safe mode: before pushing, fetch and compare local and remote history. Push only a new branch or fast-forward update; stop if the remote is ahead, divergent, or inaccessible.
8. Verify the remote branch tip after the push with a lightweight presence check (for example via `git ls-remote` on the target branch). Confirm the intended commit is reachable remotely and report any remaining local changes.
   - Safe mode: also refresh or query the remote and confirm the branch tip contains the delivered commit with no unexpected ahead/behind state.

## Stop conditions

- The directory is not a repository, `HEAD` is detached, or the current branch or destination is ambiguous.
- Changes cannot be divided into a coherent authorized commit without mixing unrelated work.
- A suspected secret, credential, private key, `.env` file, generated tree, or unexplained large file is in the candidate commit.
- Identity is missing, hooks fail, or the resulting commit cannot be verified.
- The upstream and `origin` disagree unexpectedly, multiple remotes are plausible, or a remote branch relationship cannot be established.
- The remote is ahead or divergent, or the push is rejected and would require history reconciliation or force.

## Safety

- Never use `git add .` as a substitute for review, and never stage unrelated user changes.
- Never commit likely secrets, tokens, private keys, `.env` contents, or unreviewed generated files.
- Never create an empty commit for a no-op, amend automatically, switch branches, rewrite history, reset user work, or modify global Git configuration.
- Never force push, overwrite another person's remote history, or automatically merge or rebase after rejection.
- Do not claim success until the commit and remote state have both been inspected.

## Verification

- For a new commit, verify its hash and basic staged intent.
  - Safe mode: also verify the message, parent, and exact file set against the reviewed staged diff.
- Verify the current branch and its intended remote/upstream did not change unexpectedly.
- After pushing, perform a lightweight remote check and confirm the target branch tip contains the delivered commit.
  - Safe mode: refresh or query the remote and confirm no unexpected ahead/behind state.
- Verify and enumerate remaining modified, staged, or untracked files.
- For a no-op, verify both that the worktree is clean and that no local commit is waiting to be pushed.

## Completion report

Report the branch, files committed, commit hash, commit message, remote and branch, push result, remaining local changes, and all warnings or stopped conditions. For a push-only result, identify the pushed commit range. For a no-op, explicitly state that there was nothing to commit and nothing to push.

- Keep the report brief by default; use the detailed report for `$push safe`.
