# CLAUDE.md

Guidance for Claude Code (and any agent) working in this repo.

## What toolroom is

Typed surfaces for command-line tools, generated from the tools
themselves. Standalone, a call spawns the tool with plain `subprocess`
and answers in `Result` (`ToolError` on failure unless `nofail`); with
[footman](https://github.com/willemkokke/footman) present in the
process, the same call routes through footman's `run()` and inherits
capture, dry-run, `recording()`, and receipts. Neither package depends
on the other. Python 3.11+, pre-1.0, moving fast.

## Hard invariants — do not violate

- **Zero runtime deps, and the wheel is the bridge + the testing seam
  (`toolroom.testing`) + stubs only.**
  Nothing under `src/toolroom/` imports anything but stdlib at module
  level. The machinery under `src/machinery/` is repo-only: uv_build
  ships only the declared `toolroom` module, the release workflow
  fails if machinery leaks into the wheel, and the editable install is
  what makes it importable in the dev env ("the lean install", ruled
  2026-08-05).
- **footman is a dev dependency only** — it runs the gate and hosts
  the conformance suite. `src/toolroom/` may import footman *lazily
  and only behind `_host.hosted()`* (footman present in `sys.modules`
  — presence in the process, never "a task is running") — or behind
  `toolroom.testing.answers(hosted=True)`, the consumer explicitly
  asserting footman semantics (a missing footman there is a taught
  refusal at entry).
  `machinery/` may lean on footman internals freely: it is repo-only
  and pinned.
- **The seam speaks stdlib.** `list[str]` in, int-with-attributes
  out. toolroom's `Argv`/`Result` are footman's twins, never shared
  classes; no `ArgvLike` protocol anywhere.
- **The stubs never forbid.** Every verb ends `**flags: Any`; unknown
  verbs fall through; the stubs never import footman.
- **`__init__.py` ↔ `__init__.pyi` parity** — every module-level
  runtime binding is declared in the stub; `test_tools.py` enforces
  it.

## The gate (run before every commit)

This project dogfoods footman, so use `uv run fm …`:

```sh
uv run fm check     # format --check, lint, basedpyright, pytest — parallel
```

**The exit code is the verdict — never put a filter between it and
you.** A pipe replaces the gate's status with the filter's (`fm check |
tail -4` reports tail's 0 and shows the step summary while the failing
step scrolls past). Redirection *keeps* the code, so when the output is
unwelcome, redirect rather than pipe and read the file only on failure:

```sh
uv run fm check > /tmp/gate.log 2>&1     # exit code preserved; read the log if non-zero
```

pytest must spawn (`.opts(in_process=False)`): xdist's execnet
serialises `sys.argv` into workers, and under a footman run that is the
unpicklable argv-router proxy.

## Layout

```
src/toolroom/      the wheel: __init__.py (bridge), _host.py (seam),
                   _colordata.py, __init__.pyi + _stubs/ (typing)
src/machinery/     repo-only, never in the wheel: drivers, provision,
                   toolfetch, stubgen, toolhelp/toolspec/toolhistory,
                   _tasks.py (fm tools.*)
tool-history/      the per-tool option-event store (append-only)
tests/             bridge + standalone + machinery suites
docs/              Zensical site → willemkokke.github.io/toolroom
notes/             design notes, `YYYYMMDD-` prefixed — tracked, never published
tasks.py           mounts machinery._tasks; the gate is `fm check`
```

## Notes

`notes/` holds the design reasoning — what was decided, what was
rejected and why, what was measured before choosing, and which
questions are still open. The docs say what toolroom *is*; a note says
how it got there and what it nearly was instead. They are tracked, so a
plan outlives the laptop it was written on, but they are **not
published**: the site builds from `docs/` with an explicit nav, so
nothing in `notes/` reaches the website.

**Name them `YYYYMMDD-<slug>.md`, dated the day the note was started**,
so the directory sorts into the order the thinking happened
(`20260727-cross-platform-observation.md`). Keep the date of the *first*
draft when a note grows — the prefix records when the thread opened, not
when it was last touched; a plan that turns into a different plan gets a
new note and links back.

A note that has landed says so at the top rather than being deleted: the
CHANGELOG carries what shipped, the note carries the reasoning that
never reaches a docs page. A note written before a major reshaping (the
0.32.0 split that brought this machinery over from footman) says that
too, so it reads as history rather than as a queue.

## Testing conventions

- **`from __future__ import annotations` gotcha:** in test files,
  annotations become strings evaluated via `eval_str`, so a class or
  function referenced in an annotation must be **module-level**, not
  local to the test, or it won't resolve.
- The suite fans out with xdist (`addopts = "-n auto --dist worksteal"`);
  to debug one test serially (live `-s`, `--pdb`, `-x`), override with
  `-n0`.
- ruff nits that fail the gate: line length 88; RUF043 (regex metachars
  in `pytest.raises(match=…)` → raw string, escape `.`/`|`); RUF003
  (en-dash in comments → hyphen); I001 import order; RUF022 (`__all__`
  sort). Fix fast with `uv run ruff check --fix . && uv run ruff format .`
  (the whole repo, as CI lints it — `notes/` is tracked too).
  Target `py311`; the type-checker is basedpyright.

## The refresh and its trigger

`.github/workflows/refresh.yml` gathers on three platforms weekly,
assembles into `tool-history/`, regenerates stubs, and opens a PR
carrying the prepared release bump — merging releases (the workflow
tags after the merge; the tag publishes via trusted publishing).

The trigger has three modes via the repo variable `REFRESH_MODE`:
`human` (default — a person merges), `graded` (pure-additions diffs
auto-merge; `Refreshed.additions_only` is the classifier), `auto`.
Escalating past `human` needs branch protection on the `gate` check,
auto-merge enabled, and the `REFRESH_TOKEN` PAT secret. Switching
modes is a config change — never reopen the design.

## Work in a worktree, and clean up after yourself

**Every agent session works in its own git worktree, from before its
first edit.** The maintainer edits the main checkout live, so an agent
editing there shares a tree with uncommitted work it did not write:
`git add -A` sweeps someone else's half-finished change into your
commit, a `git stash` around your own gate run takes their edits with
it, and a failing test can belong to either of you with nothing to say
which. `EnterWorktree` before touching a file; the main checkout is the
maintainer's.

**A session cleans up what it created.** Before you finish: the worktree
is removed (`ExitWorktree`, or `git worktree remove`), every branch you
merged is deleted **locally and on the remote**, and `git worktree list`
shows only the main checkout. A merged branch left on the remote is not
inert — the refresh workflow names its branch for the date, and a
leftover one is how a closed PR for the same head comes to look open.
Leave `git branch -a` showing `main` and nothing else.

## Commits & identity

- **Author/committer email is the maintainer's personal `mail@willem.net`,
  and every commit is SSH-signed so GitHub shows "Verified."** A global
  git `includeIf` keyed on the `willemkokke` remote applies the personal
  email automatically; signing is global. If a commit ever shows
  **Unverified**, check both: (a) committer email is `mail@willem.net`
  (a *verified* account email), and (b) the SSH key is registered as a
  **signing** key, not just an auth key — `gh api
  users/willemkokke/ssh_signing_keys` must be non-empty. Signing changes
  the commit hash (the signature is in the object), so "verifying"
  existing commits means rewriting them. Never disable signing to dodge
  a prompt.
- **No `Co-Authored-By:` trailers**, and no AI-attribution lines. The
  maintainer is the sole author and owner of any issues; commit messages
  end at the body.
- Conventional-commit prefixes (`feat`/`fix`/`docs`/`test`/`refactor`/`chore`),
  one logical change per commit, body explaining root cause + fix.
- 1Password gates SSH signing (caches ~10 min). Don't retry a failed
  signed commit or SSH push — it routes through 1Password; fall back
  once, say so, and wait.

## Docs

- Site is [Zensical](https://zensical.org) in `docs/`, published to
  willemkokke.github.io/toolroom; `fm docs` regenerates the tool pages
  and the colour page into `docs/_generated/`.
- **Plain words — no consultant jargon** ("lever"/"leverage"/"synergy",
  "utilize", "delve", etc.) in README, CHANGELOG, or docs.
- Docs are timeless: a behaviour change rewrites the page as
  always-been-so; the CHANGELOG owns the narrative.
- CHANGELOG follows [Keep a Changelog](https://keepachangelog.com/) +
  SemVer; pre-1.0 minors may include breaking changes. Compare-links at
  the bottom reference tags.

## Releasing

The version lives in **two** places that must match the tag *and* the
CHANGELOG entry: `pyproject.toml` `version` and
`src/toolroom/__init__.py` `__version__` — `release.yml` refuses
otherwise. `fm tools.prepare-release` rolls all three the way the
runbook would by hand.

Push the tag, and only the tag; trusted publishing does the rest. Never
`git push` casually — the maintainer drives releases, and a stray tag
publishes.

Unlike footman, `main` here is **not** branch-protected, so a release
bump can land directly — but the weekly refresh PR is the usual path,
and escalating `REFRESH_MODE` past `human` would require protection on
the `gate` check first.

**footman is the companion repo** (`willemkokke/footman`): it consumes
toolroom as a dev dependency and releases on its own train. A toolroom
release never waits on footman, and a footman release never waits on a
stub reading.
