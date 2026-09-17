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

Deliver the current task's reviewed changes as a meaningful commit on the current branch and push them to the intended remote. By default, a successful non-force push reporting the branch update is the delivery confirmation; `$push safe` additionally confirms the remote tip. If there are no local changes but unpushed commits exist, push them without making another commit. If neither exists, return a successful no-op.

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
- Default: fast — current directory, current branch, its configured upstream, and task-related reviewed changes only; start immediately without a plan or confirmation when scope and upstream are unambiguous; commit as soon as possible — inspect and classify in one pass, stage and commit in one pass, and push in one pass, relying on the commit and push outputs instead of separate re-verification; stop quickly and suggest `$push safe` when scope or destination is ambiguous.
- Optional `$push safe`: full verification — present a plan and confirm first; add pre-push history comparison, commit-style lookup, identity preflight, full staged-diff re-read, separate commit inspection, and post-push ahead/behind confirmation.

## Preconditions

- Separate current-task changes from obvious unrelated work. Inspect mixed files carefully rather than assuming each whole file belongs in one commit.
- Check candidate files and diffs for `.env` data, tokens, credentials, private keys, generated output, logs, and unexplained large files without echoing secret values.
- When a commit is needed, confirm Git identity and account for repository hooks or contribution rules.
  - Safe mode: preflight identity and hook configuration explicitly before committing.

## Workflow

1. Inspect and classify in one pass: resolve the repository, current branch, remotes, and upstream, then read `git status` and the candidate diff in the same pass. Classify:
   - **Changes exist:** identify one coherent commit scope. Leave unrelated changes untouched and report them. If unrelated work is already staged, do not silently unstage or reset it; stop for direction unless a safe, explicitly authorized isolation is available. If the intended changes represent multiple independent tasks, stop for scope guidance or create only the clearly authorized commit; do not combine them for convenience.
   - **Worktree is clean, commits are ahead:** skip commit creation and go to the push step. With no upstream, an absent intended remote branch makes existing local commits pending as a new-branch push; do not misclassify that state as a no-op.
   - **Worktree is clean, no commits are ahead:** return a successful no-op stating that nothing needs committing or pushing.
   - Safe mode: also refresh the relevant remote-tracking state and inspect how the destination tip relates to `HEAD` before classifying pending work.
2. Stage and commit in one pass when a commit is needed: stage only explicit, reviewed paths (never a blanket `git add .`), run `git diff --cached --check`, and commit with a short, accurate message; the commit output supplies the hash and summary. Derive the message from the staged diff — prefer the repository's recent style when visible, otherwise use:
   ```text
   <icon> <type>(<scope>): <summary>

   <body>
   ```
   Choose a conventional icon/type pair for the dominant change, keep the type in English, omit the scope only for truly global work, and follow the user's language for the summary and body. Keep the title concise. For a non-trivial commit, include concise bullets covering every material change point; a trivial one-point change may omit the body. Use a user-supplied message only when it still describes the staged content. Create a new commit without amending.
   - Safe mode: re-read the staged diff in full, look up the repository's recent commit style, and preflight identity and hook configuration before committing; after committing, verify the commit's hash, message, parent, and exact changed paths.
3. Push in one pass: one normal non-force push to the configured upstream; without one, use `origin` only when it is the unique, clearly intended remote and the same-named remote branch is absent or safely related. The push output reporting the branch update is the delivery confirmation. Stop if the destination is clearly invalid or unreachable or the remote rejects; do not force, merge, rebase, reset, switch branches, or repeat speculative pushes.
   - Safe mode: before pushing, fetch and compare local and remote history; push only a new branch or fast-forward update. After pushing, refresh or query the remote and confirm the branch tip contains the delivered commit with no unexpected ahead/behind state.

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
- Do not claim success until the commit has been created and the non-force push has reported success on the target branch; `$push safe` also inspects the remote state before claiming success.

## Verification

- For a new commit, confirm its hash and summary from the commit output and that the staged content matched the reviewed scope.
  - Safe mode: also verify the message, parent, and exact file set against the reviewed staged diff.
- After pushing, treat a successful non-force push reporting the branch update as delivery confirmation.
  - Safe mode: refresh or query the remote and confirm the target branch tip contains the delivered commit with no unexpected ahead/behind state.
- Verify and enumerate remaining modified, staged, or untracked files.
- For a no-op, verify both that the worktree is clean and that no local commit is waiting to be pushed.

## Completion report

Report the branch, files committed, commit hash, commit message, remote and branch, push result, remaining local changes, and all warnings or stopped conditions. For a push-only result, identify the pushed commit range. For a no-op, explicitly state that there was nothing to commit and nothing to push.

- Keep the report brief by default; use the detailed report for `$push safe`.
