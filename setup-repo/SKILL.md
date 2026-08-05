---
name: setup-repo
description: Safely initialize a local project on main, connect an existing remote repository, and make the first non-destructive push; use when publishing an unconfigured local project for the first time.
metadata:
  treefolk-category: core
  treefolk-domain: git
  treefolk-kind: workflow
---

# Set up a repository

## Outcome

Produce a safely initialized Git repository on `main`, connected to the intended existing `origin`, with the first non-destructive push verified. If no remote URL is available, complete only the safe local work and report remote publication as incomplete.

## Use when

- A local project is not yet a Git repository and should be published for the first time.
- An uncommitted or unpushed repository needs its initial `main` setup checked and completed.
- The remote repository already exists and its URL is known.

## Do not use when

- The remote repository still needs to be created or authentication configured; handle that separately first.
- An established repository only needs routine changes committed and pushed; use `commit-push`.
- Existing local and remote histories require a merge, rebase, reset, or migration; plan that reconciliation explicitly.

## Inputs

- Required for the complete outcome: the existing remote repository URL.
- Optional: target directory and initial commit message.
- Defaults: current directory, remote name `origin`, branch `main`, and a concise initial message consistent with repository conventions or `Initial commit` when no convention exists.

## Preconditions

- Resolve and confirm the physical target directory before changing it.
- Determine whether the target is inside another Git work tree and whether it already has its own `.git` entry.
- Inspect any existing repository, branch, commits, worktrees, remotes, and submodule context. Never delete or rebuild `.git`.
- Confirm Git can read a usable `user.name` and `user.email` before creating a commit. Do not change global Git configuration.
- Review the current files and `.gitignore`. Identify likely secrets, tokens, private keys, `.env` files, dependency trees, build output, temporary files, logs, and unusually large files without exposing secret values in the report.
- Confirm there are suitable project files to commit after exclusions. An empty or unsafe initial commit is not required.

## Workflow

1. Resolve the target and classify it as a new repository, an existing repository root, or a directory nested in another repository. Stop on unintended nesting instead of creating a repository inside a repository.
2. Audit the file set before initialization or staging. Keep source and intentional configuration; exclude credentials and obvious generated or temporary material. Make only narrow `.gitignore` changes that are within the requested setup, and never delete files as cleanup.
3. For a new repository, prefer `git init -b main`. If that option is unavailable, run a compatible plain initialization and set the unborn branch reference to `main` before any commit. For an existing repository, preserve `.git` and all history. When it has no commits and its unborn branch has another name, verify that no existing ref or worktree conflicts, then point only that unborn branch to `main`. If committed history is on another branch, stop rather than renaming or switching it implicitly.
4. Recheck status and identity. Create an initial commit only when the repository has no commits and reviewed, suitable files exist. Stage explicit reviewed paths, inspect the staged diff, then commit. If a commit already exists or nothing safe is commit-worthy, do not create an empty or replacement commit.
5. Inspect `origin`. If it is absent and a remote URL was supplied, add that exact URL. If it already resolves to the same intended URL, continue as a no-op. If it differs, stop without changing it. If no URL was supplied, finish the local checks and report that remote publication was not completed.
6. Inspect the remote before pushing. Query advertised refs and its default `HEAD`, then fetch relevant existing history into remote-tracking refs. If remote `main` exists, require its tip to be an ancestor of local `main`. If `main` is absent but any default or other remote branch already has commit history, do not treat the remote as empty: compare the advertised history and stop for explicit integration when it is unrelated or its intended role is unclear. Stop on divergence, a remote-ahead branch, ambiguous default history, authentication uncertainty, or any overwrite risk.
7. Push with a normal `git push -u origin main` only when the update is provably a new branch or fast-forward. Never add a force option.
8. Refresh or query remote state and verify the checked-out branch, upstream, local tip, and remote `main` tip. Report a no-op when every requested state was already correct.

## Stop conditions

- The target is unintentionally nested in another Git repository or its repository boundary is unclear.
- Existing `.git` data is damaged, unusual, or would need replacement.
- Commit identity is missing when a commit is needed.
- A likely secret, credential, private key, `.env` file, generated tree, or unexplained large file would be committed.
- Existing committed history is not safely on the intended `main` path.
- `origin` points somewhere other than the supplied remote URL.
- Remote history is unrelated, divergent, ahead, ambiguous, or cannot be inspected well enough to rule out overwriting it.
- Authentication, connectivity, hooks, or push protection prevents a verifiable normal push.

## Safety

- Never delete `.git`, reconstruct history, force push, amend, reset, merge unrelated histories, or overwrite a remote.
- Never replace or rewrite an existing remote, delete a remote branch, switch an established branch, or modify global Git configuration automatically.
- Never stage everything without reviewing the file list and diff. Never commit credentials, tokens, private keys, `.env` data, or other suspected secrets.
- Do not create a GitHub repository, log in to a host, use destructive cleanup, or claim remote success from a command exit code alone.

## Verification

- Confirm the target is the intended repository root and `git status` is understandable.
- Confirm the local branch is `main` without lost or rewritten history.
- If an initial commit was created, inspect its hash, message, and exact file set.
- Confirm `origin` is the intended URL without printing embedded credentials.
- After a push, confirm `main` tracks `origin/main`, both tips identify the same commit, and there is no unexpected ahead/behind state.
- If only local setup completed, verify that state separately and mark the remote outcome incomplete.

## Completion report

Report the target path, repository state before and after, branch, initial commit hash or no-op reason, sanitized `origin`, remote inspection result, push and upstream result, remaining files or warnings, and any stopped or incomplete part. Distinguish local readiness from verified remote publication.
