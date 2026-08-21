# Testing

Code that calls tools through toolroom is tested with
`toolroom.testing.answers()`: a context manager that answers every
bridge call from a table instead of spawning, and records what would
have run.

```python
from toolroom.testing import answers

with answers(
    {
        ("uv", "tool", "list"): "hse-devkit v0.0.18\n- hse\n",
        ("git", "push"): 1,
    }
) as calls:
    release()  # the code under test, real handles

assert calls[0].argv[:3] == ["uv", "tool", "list"]
```

The handles under test stay real. `answers()` swaps nothing above the
seam, so verb chaining, flag translation, the `off` sentinel, secrets
redaction and `input=` consumption are all the bridge's own — exercised
exactly as a live call would exercise them. Only execution is replaced,
which is the one part of a call a test has no business exercising.

## The table

**Keys** are argv prefixes — tuples of tokens, or one string split on
whitespace. Matching is against the *name-led* spelling of the call
(`git …`, `python …` — never a resolved interpreter path), and the
longest matching prefix wins.

**Values** are the answer:

- a `str` is stdout, with exit 0 — for code that parses a tool's output
- an `int` is an exit code — for driving the failure path
- a `Result` sets the code and both streams

An unmatched call succeeds silently — exit 0, empty streams — so
`answers()` with no table is a pure call recorder. A non-zero answer
takes the failing lane honestly: the result comes back under `nofail`,
and raises otherwise.

## The record

The yielded list holds one `Call` per interception:

- `.argv` — the name-led raw tokens, the thing assertions read
- `.raw` — what would actually have spawned: resolved interpreter path,
  forced colour switch and all
- `.command` — the shown line, values quoted and secrets redacted
- `.env` — the environment the call handed the seam (`None` inherits)
- `.opts` — the rest of the run policy (`nofail`, `capture`, `input`,
  `cwd`, `timeout`, …) exactly as it crossed
- `.probe` — marks a version read

## The hosted lane

Code written to run inside footman tasks returns footman's `Result` and
catches footman's `RunFailed`. `answers(hosted=True)` simulates that
lane for the block: the bridge takes its hosted paths (an in-process
tool's callable is recorded, never invoked), successes come back as
footman's `Result`, and failures raise `RunFailed`. The default speaks
toolroom's own vocabulary — `Result` back, `ToolError` raised — which
is what a footman-free consumer tests against.

## Version reads

`tool.installed_version()` is answerable from the same table — can the
version line and the real parser reads it:

```python
with answers({("git", "--version"): "git version 2.43.0"}):
    assert release_guard()  # branches on git.installed_version()
```

A version read with no canned answer refuses by name rather than
answering empty: code branches on versions, so an accidental blank
would surface as a confusing parse failure far from the cause. The
per-process version cache is cleared for the block and restored after
it, so a canned version neither loses to an earlier real read nor leaks
into later tests.

## `answers()` and footman's `recording()`

They are different instruments. footman's
[`recording()`](footman.md) is a rehearsal inside the real world:
nothing executes, every call succeeds silently, and a value read opted
`recorded=False` still answers truthfully. `answers()` replaces the
world — canned output, injected failures, version probes included.
Nested, `answers()` wins: it intercepts upstream of footman, so its
answers stand and the recording sees nothing.

Reach for `recording()` when the assertion is "this block would run
these commands"; reach for `answers()` when the code under test needs
a tool to *say* something, or to fail.
