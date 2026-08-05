# toolroom

Typed surfaces for command-line tools, generated from the tools
themselves.

```python
from toolroom import cmake, git

git.switch("-c", "release/v1.4")
cmake.build("build", parallel=8)
```

A tool room is where precision tools are made, kept with their
measurements, repaired when they drift, and issued for use. That is
the whole design, one verb at a time: a stub generator reads each
tool's own `--help` and writes a typed surface for it; the surfaces
are kept with the version they were read from; a weekly refresh
re-takes them when the tool moves; and the bridge issues any tool as
a Python handle — including tools no stub has ever described.

## No transcription

toolroom does **not** transcribe a tool's flags into Python
parameters. Transcription drifts: the wrapper pins the flag-set its
author copied, the tool moves on, and one day a call emits a flag the
installed binary rejects. Instead, keyword arguments translate
*mechanically* — `fix=True` becomes `--fix`, `select=["E", "F"]`
repeats the flag, attribute access chains subcommands — so the
installed tool's own CLI stays the single source of truth, at
whatever version it is. The typed stubs *suggest*; they never forbid.
[Using the tools](usage.md) has the full grammar.

## Standalone, or hosted

With nothing else installed, a call spawns the tool with plain
`subprocess` and answers in a `Result` — the exit code as an `int`
subclass, carrying the captured streams. A failure raises `ToolError`
unless the call opted into `nofail`.

When [footman](https://willemkokke.github.io/footman/) is present in
the process, the same call routes through footman's `run()` instead
and inherits everything a task run means: capture, replay-on-failure,
dry-run, `recording()`, `--json` receipts, parallel lanes. Neither
package imports or depends on the other — detection is the seam, and
it speaks stdlib. [With footman](footman.md) tells that story.

## Install

```sh
pip install toolroom
```

toolroom has **zero runtime dependencies** and needs Python 3.11+.
Pre-release: PyPI currently holds the name-reservation placeholder;
the first real release will be tagged from this repository.
