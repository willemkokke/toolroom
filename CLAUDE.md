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

- **Zero runtime deps, and the wheel is the bridge + stubs only.**
  Nothing under `src/toolroom/` imports anything but stdlib at module
  level. The machinery under `machinery/` is repo-only and must never
  ship in any dist ("the lean install", ruled 2026-08-05).
- **footman is a dev dependency only** — it runs the gate and hosts
  the conformance suite. `src/toolroom/` may import footman *lazily
  and only behind `_host.hosted()`* (footman present in `sys.modules`
  — presence in the process, never "a task is running").
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

```sh
uv run fm check     # format --check, lint, basedpyright, pytest — parallel
```

The exit code is the verdict — redirect output if it is unwelcome,
never pipe it. pytest must spawn (`.opts(in_process=False)`): xdist's
execnet serialises `sys.argv` into workers, and under a footman run
that is the unpicklable argv-router proxy.

## Layout

```
src/toolroom/      the wheel: __init__.py (bridge), _host.py (seam),
                   _colordata.py, __init__.pyi + _stubs/ (typing)
machinery/         repo-only: drivers, provision, toolfetch, stubgen,
                   toolhelp/toolspec/toolhistory, _tasks.py (fm tools.*)
tool-history/      the per-tool option-event store (append-only)
tests/             bridge + standalone + machinery suites
docs/              Zensical site → willemkokke.github.io/toolroom
tasks.py           mounts machinery._tasks; the gate is `fm check`
```

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

## Releasing

`pyproject.toml` `version` and `src/toolroom/__init__.py`
`__version__` must match the tag and the CHANGELOG entry
(`release.yml` refuses otherwise). `fm tools.prepare-release` rolls
all three the way the runbook would by hand. Push the tag, and only
the tag; trusted publishing does the rest.

## Conventions

Commits are conventional (`feat`/`fix`/`docs`/`chore`…), SSH-signed,
authored as `mail@willem.net`, with **no `Co-Authored-By` or
AI-attribution trailers**. Plain words in README, CHANGELOG, and
docs. Docs are timeless: behaviour changes rewrite pages as
always-been-so; the CHANGELOG owns the narrative.
