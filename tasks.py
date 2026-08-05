"""toolroom's own tasks — the gate is `fm check`.

Dogfooding twice over: the tasks run under footman (the dev
dependency), and every tool call below goes through toolroom's own
bridge — which detects the footman host and routes through `run()`, so
the gate exercises the hosted lane on every run.
"""

from __future__ import annotations

from footman import include, requires_dep, task

import toolroom as tools

include("machinery._tasks")


@task
def format(fix: bool = False) -> None:
    """ruff format — check by default, rewrite with --fix."""
    if fix:
        tools.ruff.format(".")
    else:
        tools.ruff.format(".", check=True)


@task
def lint(fix: bool = False) -> None:
    """ruff check across the repo."""
    tools.ruff.check(".", fix=fix)


@task
def typecheck() -> None:
    """basedpyright over src, tests, and the tasks file."""
    tools.basedpyright()


@task
def test() -> None:
    """The pytest suite (xdist across cores via addopts).

    Spawned, not in-process: xdist's execnet serialises `sys.argv` into
    each worker (`mainargv`), and inside a footman run that is the argv
    router's proxy — unpicklable by design. A subprocess has a plain
    argv, and the suite is xdist-bound anyway.
    """
    tools.pytest.opts(in_process=False)()


@requires_dep("zensical", reason="docs tooling: uv sync --group docs")
@task
def docs() -> None:
    """Build the documentation site, strictly.

    The per-tool reference pages regenerate first, from the checked-in
    stubs — the build needs no tool on PATH, and the sidebar can never
    fall behind the drivers.
    """
    from pathlib import Path

    from machinery._tasks import pages

    pages(Path("docs/_generated/tools"), nav=Path("zensical.toml"))
    tools.zensical.build(clean=True, strict=True)


@task(pre=[format, lint, typecheck, test])
def check() -> None:
    """The gate: format check, lint, types, tests — in parallel."""
