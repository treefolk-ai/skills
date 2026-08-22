---
name: repo
description: Safely initialize a local project on main, find or create its intended hosted repository, and make the first non-destructive push; use when publishing an unconfigured project for the first time.
metadata:
  treefolk-category: core
  treefolk-domain: git
  treefolk-kind: workflow
---

# Set up a repository

## Outcome

Produce a safely initialized Git repository on `main`, connected to the exact intended `origin`, with the first non-destructive push verified. Reuse the hosted repository when it exists; when an authoritative lookup confirms that it does not, create exactly one empty repository. New hosted repositories are private by default and public only when the current invocation explicitly requests `public`.

## Use when

- A local project is not yet a Git repository and should be published for the first time.
- An uncommitted or unpushed repository needs its initial `main` setup checked and completed.
- The intended hosted repository may already exist or may need to be created before the first push.

## Do not use when

- Authentication still needs to be configured, or the intended host, owner, or repository name cannot be resolved unambiguously.
- An established repository only needs routine changes committed and pushed; use `push`.
- An existing hosted repository needs its visibility changed; handle that as a separate, explicitly authorized action.
- Existing local and remote histories require a merge, rebase, reset, or migration; plan that reconciliation explicitly.

## Inputs

- Required for the complete outcome: one exact hosted-repository identity consisting of host, owner or namespace, and repository name. Resolve it from an existing `origin`, an explicitly supplied URL or repository identity, or—only when unambiguous—the target directory name plus the single active authenticated hosting account's personal namespace.
- Optional: target directory, remote URL or repository identity, initial commit message, and the `public` visibility instruction.
- Defaults: current directory, remote name `origin`, branch `main`, the provider-reported HTTPS Git clone URL when no `origin` or explicit remote transport exists, private visibility for a newly created hosted repository, and a concise initial message consistent with repository conventions or `Initial commit` when no convention exists.
- Treat `public` as a creation-only opt-in when it is explicitly given as the repository visibility instruction in the current invocation, such as `$repo public`. Never infer it from a license, README, project description, or the word “public” used in another context.
- Preserve the visibility of an existing hosted repository. The private default and `public` instruction do not authorize changing it.

## Preconditions

- Resolve and confirm the physical target directory before changing it.
- Determine whether the target is inside another Git work tree and whether it already has its own `.git` entry.
- Inspect any existing repository, branch, commits, worktrees, remotes, and submodule context. Never delete or rebuild `.git`.
- Confirm Git can read a usable `user.name` and `user.email` before creating a commit. Do not change global Git configuration.
- Review the current files and `.gitignore`. Identify likely secrets, tokens, private keys, `.env` files, dependency trees, build output, temporary files, logs, and unusually large files without exposing secret values in the report.
- Confirm there are suitable project files to commit after exclusions. An empty or unsafe initial commit is not required.
- Resolve the intended host, owner or namespace, repository name, transport, and authenticated account without exposing credentials. Do not log in, switch accounts, or create under a guessed personal or organization namespace.

## Workflow

1. Resolve the target and classify it as a new repository, an existing repository root, or a directory nested in another repository. Stop on unintended nesting instead of creating a repository inside a repository.
2. Before changing files, Git history, remotes, or hosted state, resolve one exact hosted-repository identity and the active authenticated account. Prefer an existing `origin`, then an explicitly supplied URL or identity. Only when neither exists may the target directory basename and a single active authenticated personal namespace provide the default. Preserve an existing or explicitly supplied transport; otherwise use the provider-reported HTTPS Git clone URL. Stop if these sources conflict, if the provider would normalize or redirect the name unexpectedly, or if host, account, or ownership remains ambiguous.
3. Query the hosting provider for that exact identity using an authenticated authoritative API or CLI. Treat only a confirmed not-found result as absence; authentication, authorization, connectivity, rate-limit, and indeterminate lookup failures are not evidence that the repository is absent. If it exists, record its canonical identity, web URL, available Git clone URLs, actual visibility, default branch, and advertised refs without changing them. When it already has commits but the local target has no existing Git history to compare, stop before local initialization for explicit reconciliation.
4. Audit the file set before initialization or staging. Keep source and intentional configuration; exclude credentials and obvious generated or temporary material. Make only narrow `.gitignore` changes that are within the requested setup, and never delete files as cleanup.
5. For a new repository, prefer `git init -b main`. If that option is unavailable, run a compatible plain initialization and set the unborn branch reference to `main` before any commit. For an existing repository, preserve `.git` and all history. When it has no commits and its unborn branch has another name, verify that no existing ref or worktree conflicts, then point only that unborn branch to `main`. If committed history is on another branch, stop rather than renaming or switching it implicitly.
6. Recheck status and identity. Create an initial commit only when the repository has no commits and reviewed, suitable files exist. Stage explicit reviewed paths, inspect the staged diff, then commit. If a commit already exists or nothing safe is commit-worthy, do not create an empty or replacement commit.
7. If the hosted repository exists, reuse the provider-reported Git clone URL for the intended transport and preserve its actual visibility. If it is confirmed absent, first require a safe local commit or existing publishable history, then create exactly one empty repository with an explicit visibility setting: private by default or public only for an explicit `public` instruction. Do not initialize it with a README, license, `.gitignore`, template, or first commit, and do not combine creation with an implicit push. Immediately query it again and verify its canonical identity, web and clone URLs, visibility, and empty state before continuing.
8. Inspect `origin`. If absent, add the verified Git clone URL using the intended transport. If it already resolves to the same canonical repository, continue as a no-op. If it differs, stop without replacing it. A hosted repository created before a later conflict is a partial success and must not be deleted as rollback.
9. Inspect advertised refs and the remote's default `HEAD`, then fetch relevant existing history into remote-tracking refs. If remote `main` exists, require its tip to be an ancestor of local `main`. If `main` is absent but any default or other remote branch already has commit history, do not treat the remote as empty: compare the advertised history and stop for explicit integration when it is unrelated or its intended role is unclear. Stop on divergence, a remote-ahead branch, ambiguous default history, or any overwrite risk.
10. Push with a normal `git push -u origin main` only when the update is provably a new branch or fast-forward. Never add a force option.
11. Refresh both provider metadata and Git remote state. Verify the hosted identity and visibility, checked-out branch, upstream, local tip, and remote `main` tip. Report a no-op when every requested state was already correct.

## Stop conditions

- The target is unintentionally nested in another Git repository or its repository boundary is unclear.
- Existing `.git` data is damaged, unusual, or would need replacement.
- Commit identity is missing when a commit is needed.
- A likely secret, credential, private key, `.env` file, generated tree, or unexplained large file would be committed.
- Existing committed history is not safely on the intended `main` path.
- The host, authenticated account, owner or namespace, repository name, transport, or requested creation visibility is missing, conflicting, or ambiguous.
- The provider lookup cannot distinguish confirmed absence from an authentication, authorization, connectivity, rate-limit, or other failure.
- Repository creation or post-creation verification does not produce the exact intended identity and visibility.
- `origin` points somewhere other than the verified canonical repository.
- Remote history is unrelated, divergent, ahead, ambiguous, or cannot be inspected well enough to rule out overwriting it.
- Authentication, connectivity, hooks, or push protection prevents a verifiable normal push.

## Safety

- Never delete `.git`, reconstruct history, force push, amend, reset, merge unrelated histories, or overwrite a remote.
- Never replace or rewrite an existing remote, delete a remote branch, switch an established branch, or modify global Git configuration automatically.
- Never stage everything without reviewing the file list and diff. Never commit credentials, tokens, private keys, `.env` data, or other suspected secrets.
- Never create more than one hosted repository, select a fallback owner or name after a conflict, create a fork or template-derived repository, or add remote starter files that introduce unreviewed history.
- Always pass the new repository's visibility explicitly to the provider. Use private unless the current invocation explicitly requests `public`; never change an existing repository's visibility as part of this workflow.
- After an indeterminate create or push result, query authoritative provider and remote state before considering a retry. Never retry while the earlier attempt's side effects remain unknown.
- If a repository appears after an indeterminate create attempt, report the creation attribution as unverified instead of claiming that it was definitely created or reused by this run.
- Do not log in to a host, switch the active account, expose credentials, use destructive cleanup, delete a newly created repository as rollback, or claim remote success from a command exit code alone.

## Verification

- Confirm the target is the intended repository root and `git status` is understandable.
- Confirm the local branch is `main` without lost or rewritten history.
- If an initial commit was created, inspect its hash, message, and exact file set.
- Query the provider after lookup or creation and confirm the exact host, owner or namespace, repository name, canonical web and Git clone URLs, and actual visibility. For a newly created repository, also confirm that visibility matches the private default or explicit `public` instruction.
- Confirm `origin` resolves to the verified canonical repository without printing embedded credentials.
- After a push, confirm `main` tracks `origin/main`, both tips identify the same commit, and there is no unexpected ahead/behind state.
- If local setup, hosted creation, origin configuration, or push completes without the later steps, verify each completed state separately and report the remaining outcome as incomplete.

## Completion report

Report the target path, repository state before and after, branch, initial commit hash or no-op reason, hosted identity, lookup result, created, reused, or attribution-unverified status, actual visibility, canonical web URL, sanitized `origin`, remote-history inspection, push and upstream result, remaining files or warnings, and every stopped or incomplete part. State explicitly whether a new repository was created as private or public, or an existing repository's visibility was left unchanged. Distinguish local readiness, hosted-repository creation, and verified remote publication.
