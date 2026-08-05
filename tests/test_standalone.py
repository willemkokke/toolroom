"""The standalone lane: no footman host, plain subprocess, toolroom's own vocabulary.

footman is importable in this suite (it is the dev dependency that runs
the hosted tests), so standalone behaviour is reached the honest way the
seam defines it: `hosted()` answers False and every call takes the
subprocess executor. Patching that one function *is* the standalone
process, as far as the bridge can tell.
"""

from __future__ import annotations

import subprocess
import sys
from typing import cast

import pytest

import toolroom as tools
from toolroom import Argv, Result, ToolError, _host


@pytest.fixture(autouse=True)
def standalone(monkeypatch):
    monkeypatch.setattr(_host, "hosted", lambda: False)


def test_spawn_returns_result_with_streams_and_tokens():
    r = tools.python("-c", "import sys; print('out'); print('err', file=sys.stderr)")
    assert isinstance(r, Result)
    assert r.ok and int(r) == 0
    assert r.stdout.strip() == "out"
    assert r.stderr.strip() == "err"
    assert r.to_argv()[0] == sys.executable
    assert sys.executable in r.command or r.command.startswith("'")


def test_failure_raises_toolerror_carrying_the_result():
    with pytest.raises(ToolError) as err:
        tools.python("-c", "import sys; print('why', file=sys.stderr); sys.exit(3)")
    result = err.value.result
    assert int(result) == 3
    assert "why" in str(err.value)
    assert "exited 3" in str(err.value)


def test_nofail_returns_the_failing_result():
    r = tools.python.opts(nofail=True)("-c", "raise SystemExit(2)")
    assert not r.ok
    assert int(r) == 2


def test_capture_false_leaves_streams_empty():
    r = tools.python.opts(capture=False)("-c", "print('straight through')")
    assert r.ok
    assert r.stdout == "" and r.stderr == ""


def test_env_is_the_childs_whole_environment(monkeypatch):
    # The hosted contract, kept standalone: what you pass is what the
    # child gets — never a merge over the parent's environment. hse's
    # portability sweep caught the divergence; this pins the repair.
    monkeypatch.setenv("TOOLROOM_INHERITED", "leaks")
    r = tools.python.opts(env={"TOOLROOM_PROBE": "42"})(
        "-c",
        "import os; print(os.environ.get('TOOLROOM_PROBE'), "
        "os.environ.get('TOOLROOM_INHERITED'))",
    )
    assert r.stdout.strip() == "42 None"


def test_cwd_and_rel_root_the_call(tmp_path):
    sub = tmp_path / "inner"
    sub.mkdir()
    r = tools.python.opts(cwd=tmp_path, rel="inner")(
        "-c", "import os; print(os.getcwd())"
    )
    assert r.stdout.strip().endswith("inner")


def test_input_feeds_stdin():
    r = tools.python.opts(input="fed line\n")(
        "-c", "import sys; print(sys.stdin.read().strip().upper())"
    )
    assert r.stdout.strip() == "FED LINE"


def test_input_is_consumed_exactly_once():
    handle = tools.python.opts(input="once\n")
    handle("-c", "import sys; sys.stdin.read()")
    with pytest.raises(TypeError, match="already fed"):
        handle("-c", "import sys; sys.stdin.read()")


def test_in_process_demand_needs_a_host():
    with pytest.raises(ValueError, match="needs a footman host"):
        tools.coverage.opts(in_process=True)("--version")


def test_in_process_preference_degrades_to_spawn():
    # coverage is constructed in_process=True; standalone it must simply spawn
    # and answer correctly.
    r = tools.coverage("--version")
    assert r.ok
    assert "coverage" in r.stdout.lower() or r.stdout.strip()


def test_timeout_propagates():
    with pytest.raises(subprocess.TimeoutExpired):
        tools.python.opts(timeout=0.2)("-c", "import time; time.sleep(10)")


def test_argv_twin_is_an_ordinary_list():
    built = tools.git.push.argv(force=True)
    assert isinstance(built, Argv)
    assert built == ["git", "push", "--force"]
    assert built.posix() == "git push --force"
    assert built.windows() == "git push --force"


def test_argv_positional_is_a_taught_refusal():
    cmd = tools.git.status.argv()
    with pytest.raises(TypeError, match=r"built command line \(Argv\)"):
        # The cast is the point: the stub already refuses this spelling
        # statically; the test asserts the runtime teaches it too.
        tools.uv.run(cast("str", cmd))


def test_reporting_lane_opts_are_accepted_and_ignored():
    # title/recorded/pre_record are host vocabulary; standalone they must not
    # change execution or crash.
    r = tools.python.opts(title="probe", recorded=False)("-c", "print('ok')")
    assert r.stdout.strip() == "ok"


def test_color_on_reads_the_conventional_environment(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert _host.color_on() is False
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert _host.color_on() is True


def test_container_error_wording_matches_the_doors():
    text = _host.container_error(["a"], "git", example="git(*value)")
    assert "bare list" in text
    assert "git(*value)" in text
