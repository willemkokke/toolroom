---
icon: lucide/concierge-bell
---

# With footman

toolroom and [footman](https://willemkokke.github.io/footman/) are two
zero-dependency packages that make each other better without either
requiring the other. footman never imports, ships, or names toolroom;
toolroom names footman only inside its seam, and only touches it when
footman is already in the process.

## Detection, not configuration

When a `toolroom` call happens in a process where footman is present —
which is every footman task body, and any script that imported footman
— the bridge routes the call through footman's `run()`. Nothing opts
in and nothing can forget to: the same `git.push()` that spawns a
plain subprocess in a script earns a receipt, captures through the
task's lane, obeys `--dry-run`, and appears in `recording()` when a
footman run is around it.

```python
from footman import task
from toolroom import ruff, pytest


@task
def check() -> None:
    ruff.check("src")  # a real step: receipt, capture, dry-run, recording
    pytest.opts(in_process=False)()
```

Detection keys on footman being *present in the process*, not on a
task running: a bridge call outside any task still routes through
`run()` on footman's default context, exactly as `footman.tools`
behaves. What standalone toolroom adds is the case that could not
exist before — no footman anywhere — where plain `subprocess` answers.

## What the host unlocks

- **Receipts and reporting** — every call is a step: a line in the
  run's story, a row in `--json`, output replayed on failure.
- **`recording()`** — tests capture the commands a block would run
  without executing them.
- **`--dry-run`** — calls are faked, not executed.
- **The in-process lane** — tools that prefer running inside the
  process (pytest via `pytest.main`, mkdocs on macOS where `DYLD_*`
  survives only in-process) do so under footman's stdout and argv
  routers, fully parallel. Standalone this lane does not exist: a
  preference quietly spawns instead, a demand
  (`.opts(in_process=True)`) is a taught refusal.
- **Failure semantics** — a failing call fails the task through
  footman's lane instead of raising `ToolError`.

## The vocabulary twins

toolroom owns its `Argv` and `Result`; footman owns its own pair for
its receipts. Both `Argv`s are ordinary `list[str]` — they compare
equal token-for-token and either flows anywhere the other does. Hosted
calls answer with footman's `Result`, whose surface is a superset of
toolroom's; code written against toolroom's (`ok`, `code`, `stdout`,
`stderr`, `to_argv()`) runs unchanged under both. The seam between the
packages carries only stdlib shapes — `list[str]` in,
int-with-attributes out.

## Zero dependencies, both ways

footman's headline — zero runtime dependencies — keeps no asterisk:
it does not depend on toolroom. toolroom's runtime is stdlib-only too;
footman appears in its *development* dependencies, where it runs the
gate and hosts the conformance suite.
