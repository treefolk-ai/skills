---
name: push
description: Review current Git changes, create a scoped and meaningful commit when needed, and safely push the current branch; use for routine delivery of local work to its intended remote.
metadata:
  treefolk-category: core
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
- Optional mode: `fast`, invoked as `$push fast`.
- Defaults: current directory, current branch, its configured upstream, task-related reviewed changes only, and a concise message derived from the actual diff in the repository's existing style.

## Fast mode

When the user invokes `$push fast`, start immediately without presenting a plan or asking for workflow confirmation when the scope and configured upstream are unambiguous.

- Keep all Safety and Stop conditions.
- Inspect repository state, candidate paths, and each selected diff once.
- Stage only reviewed task paths and run `git diff --cached --check`.
- Commit only when needed, then perform one normal non-force push.
- Skip pre-push fetch/history comparison, commit-style lookup, identity preflight, repeated diff reads, and detailed commit metadata verification.
- After pushing, confirm the remote branch SHA matches `HEAD`.
- Keep the completion report brief.
- If scope or destination is ambiguous, stop quickly and suggest normal `$push`.

## Preconditions

- Confirm the target is a Git repository and identify its root, current branch, `HEAD`, remotes, and upstream.
- Stop on detached `HEAD`; do not switch branches automatically.
- Read `git status`, the unstaged diff, the staged diff, and untracked file names before staging anything.
- Separate current-task changes from obvious unrelated work. Inspect mixed files carefully rather than assuming each whole file belongs in one commit.
- Check candidate files and diffs for `.env` data, tokens, credentials, private keys, generated output, logs, and unexplained large files without echoing secret values.
- When a commit is needed, confirm Git identity and account for repository hooks or contribution rules.

## Workflow

1. Resolve the repository and current branch. Inspect remotes and upstream, then refresh the relevant remote-tracking state when network access is needed and available. Before classifying pending work, inspect the configured upstream branch when one exists; otherwise inspect the same-named branch on the one clearly intended remote. Determine whether that destination exists and how its tip relates to `HEAD`. Stop if the destination cannot be determined safely.
2. Classify the state after reviewing status and both diffs.
   - **Changes exist:** identify one coherent commit scope. Leave unrelated changes untouched and report them. If unrelated work is already staged, do not silently unstage or reset it; stop for direction unless a safe, explicitly authorized isolation is available. If the intended changes represent multiple independent tasks, stop for scope guidance or create only the clearly authorized commit; do not combine them for convenience.
   - **Worktree is clean, commits are ahead:** skip commit creation and continue to the push checks. With no upstream, an absent intended remote branch makes existing local commits pending as a new-branch push; do not misclassify that state as a no-op.
   - **Worktree is clean, no commits are ahead:** return a successful no-op stating that nothing needs committing or pushing.
3. For a commit, stage only explicit, reviewed paths or safely selected hunks. Never use a blanket `git add .`. Re-read the staged diff and ensure it contains the complete intended change, no unrelated work, and no suspected secret.
4. Derive a short, accurate message from the staged diff, preferring the repository's recent message style. Use a user-supplied message only when it still describes the staged content. Create a new commit without amending.
5. Verify the new commit by inspecting its hash, message, parent, and exact changed paths. Ensure any unstaged or untracked files remain as expected.
6. Determine the push destination. Use the configured upstream when present. Without one, establish an upstream for the same current branch only when `origin` is the unique, clearly intended remote and the same-named remote branch is absent or safely related. Stop on multiple plausible remotes or branch ambiguity.
7. Compare local and fetched remote history. Push only a new branch or fast-forward update. If the remote is ahead, divergent, inaccessible, or rejects the push, stop without force, merge, rebase, reset, branch switching, or repeated speculative pushes.
8. Verify the remote branch tip and upstream after the push. Confirm the intended commit is reachable remotely and report any remaining local changes.

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

- For a new commit, verify its hash, message, parent, and exact file set against the reviewed staged diff.
- Verify the current branch and its intended remote/upstream did not change unexpectedly.
- After pushing, refresh or query the remote and confirm its branch tip contains the delivered commit with no unexpected ahead/behind state.
- Verify and enumerate remaining modified, staged, or untracked files.
- For a no-op, verify both that the worktree is clean and that no local commit is waiting to be pushed.

## Completion report

Report the branch, files committed, commit hash, commit message, remote and branch, push result, remaining local changes, and all warnings or stopped conditions. For a push-only result, identify the pushed commit range. For a no-op, explicitly state that there was nothing to commit and nothing to push.
