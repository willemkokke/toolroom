"""The testing seam: `answers()` fakes execution, never the handle.

Everything above `_host` stays real in these tests — chaining, flag
translation, redaction — so what the fakes record is what a live call
would have spawned. That is the point of the module: hse's `FakeTool`
re-implemented the bridge's rendering by hand and drifted; `answers()`
exists so a consumer never has to.
"""

from __future__ import annotations

import sys
from typing import Any

import pytest

import toolroom as tools
from toolroom import Result, ToolError, _host
from toolroom.testing import answers


def test_no_table_is_a_pure_recorder():
    with answers() as calls:
        r = tools.terraform.plan()
    assert r.ok and r.stdout == ""
    (call,) = calls
    assert call.argv == ["terraform", "plan"]
    assert not call.probe


def test_canned_stdout_answers_by_prefix():
    with answers({("uv", "tool", "list"): "hse-devkit v0.0.18\n- hse\n"}):
        out = tools.uv.tool.list()
    assert out.stdout.startswith("hse-devkit")


def test_the_longest_matching_prefix_wins():
    with answers({("uv",): "generic", ("uv", "tool", "list"): "specific"}):
        assert tools.uv.tool.list().stdout == "specific"
        assert tools.uv.sync().stdout == "generic"


def test_a_string_key_splits_on_whitespace():
    with answers({"git status": "clean\n"}):
        assert tools.git.status().stdout == "clean\n"


def test_a_non_zero_answer_raises_toolerror_carrying_the_result():
    with answers({("git", "push"): 1}), pytest.raises(ToolError) as err:
        tools.git.push()
    assert int(err.value.result) == 1


def test_nofail_returns_the_failing_result():
    with answers({("git", "push"): 1}):
        r = tools.git.push.opts(nofail=True)()
    assert not r.ok and int(r) == 1


def test_a_result_answer_sets_code_and_both_streams():
    with answers({("cargo", "build"): Result(3, stdout="o", stderr="e")}):
        r = tools.cargo.build.opts(nofail=True)()
    assert (int(r), r.stdout, r.stderr) == (3, "o", "e")


def test_the_real_bridge_renders_the_flags():
    # The reason answers() beats a hand-written fake: `fix=True` is a bare
    # `--fix` and a list repeats its flag — the bridge's own translation,
    # which an imitation drifts from.
    with answers() as calls:
        tools.ruff.check("src", fix=True, select=["E", "F"])
    (call,) = calls
    assert call.argv == ["ruff", "check", "src", "--fix", "--select=E", "--select=F"]


def test_argv_is_name_led_and_raw_keeps_the_path():
    with answers() as calls:
        tools.python("-c", "print('hi')")
    (call,) = calls
    assert call.argv[0] == "python"
    assert call.raw[0] == sys.executable
    assert list(call.argv[1:]) == list(call.raw[1:])


def test_env_and_run_policy_are_recorded():
    with answers() as calls:
        tools.uv.opts(env={"UV_DYNAMIC_VERSIONING_BYPASS": "1.0"}).sync()
    (call,) = calls
    assert call.env == {"UV_DYNAMIC_VERSIONING_BYPASS": "1.0"}
    assert call.opts["capture"] is True and call.opts["nofail"] is False


def test_the_shown_line_redacts_a_secret_the_argv_keeps():
    with answers() as calls:
        tools.git.commit(m=_Marked("hunter2"))
    (call,) = calls
    assert "hunter2" not in call.command
    assert "***" in call.command
    assert any("hunter2" in token for token in call.raw)


class _Marked(str):
    """footman's Secret, duck-typed on `reveal` — local so this suite
    proves the seam without footman in the picture."""

    def reveal(self) -> str:
        return str(self)


def test_a_bad_key_is_a_taught_refusal():
    with pytest.raises(TypeError, match="argv prefix"), answers({42: "x"}):
        pass


def test_a_bad_answer_is_a_taught_refusal():
    bad: dict[Any, Any] = {("git", "status"): ["not", "an", "answer"]}
    with answers(bad), pytest.raises(TypeError, match=r"str \(stdout\)"):
        tools.git.status()


def test_the_seam_is_restored_after_the_block():
    before = (_host.run, _host.probe, _host.hosted)
    with answers({("git", "status"): "x"}):
        pass
    assert (_host.run, _host.probe, _host.hosted) == before


# --- version reads: the probe door ------------------------------------------


def test_a_canned_version_read_parses_with_the_real_parser():
    with answers({("git", "--version"): "git version 99.43.0\n"}) as calls:
        assert tools.git.installed_version() == (99, 43, 0)
        assert tools.git.installed_version() == (99, 43, 0)  # cached: one probe
    (call,) = calls
    assert call.probe
    assert call.argv == ["git", "--version"]
    assert tools._version_cache.get("git") != (99, 43, 0)  # nothing leaked


def test_an_unmatched_version_read_refuses_by_name():
    # An empty answer would surface as installed_version's own "could not
    # read a version" ValueError, which reads as a bug in the code under
    # test; the refusal names the missing table entry instead.
    with answers(), pytest.raises(LookupError, match=r"`git --version`"):
        tools.git.installed_version()


def test_the_process_cache_cannot_preempt_a_canned_version(monkeypatch):
    monkeypatch.setitem(tools._version_cache, "git", (1, 0, 0))
    with answers({("git", "--version"): "git version 99.43.0\n"}):
        assert tools.git.installed_version() == (99, 43, 0)
    assert tools._version_cache["git"] == (1, 0, 0)  # snapshot restored


# --- the hosted simulation ---------------------------------------------------


def test_hosted_simulation_speaks_footman_vocabulary():
    import footman

    with answers({("git", "push"): 1}, hosted=True) as calls:
        ok = tools.git.status()
        assert isinstance(ok, footman.Result)
        with pytest.raises(footman.RunFailed):
            tools.git.push()
    assert [call.argv for call in calls] == [["git", "status"], ["git", "push"]]


def test_hosted_in_process_callable_is_recorded_never_invoked():
    # coverage prefers in-process; under the simulated host the bridge hands
    # the seam a callable, and the fake records the call without running it.
    with answers(hosted=True) as calls:
        r = tools.coverage.report()
    assert r.ok
    (call,) = calls
    assert call.argv[:2] == ["coverage", "report"]


# --- coexistence with footman's recording ------------------------------------


def test_answers_wins_inside_a_recording():
    # recording() is a rehearsal inside the real world; answers() replaces
    # the world. Nested, the innermost wins: the interception sits upstream
    # of footman, so the record sees nothing.
    from footman.testing import recording

    with recording() as steps, answers({("git", "branch"): "main\n"}) as calls:
        out = tools.git.branch()
    assert out.stdout == "main\n"
    assert steps == []
    assert len(calls) == 1


# --- the module is reachable as an attribute ----------------------------------


def test_from_toolroom_import_testing_is_the_module():
    # `from toolroom import X` consults the package's __getattr__ before the
    # import system tries the submodule — without the redirect this would be
    # Tool("testing").
    from toolroom import testing as mod

    assert mod.answers is answers
    assert not isinstance(mod, tools.Tool)
    assert not isinstance(tools.testing, tools.Tool)
