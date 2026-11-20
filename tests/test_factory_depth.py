"""A run's depth, set by risk, the evidence a builder report and a behaviour check owe, the copies
of `sdlc`'s rules the factory keeps, and the build gate's question.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from factory_helpers import (
    FULL,
    LISTED,
    NAME,
    ROOT,
    _build_report,
    _change,
    _commit_on_main,
    _escalated,
    _git,
    _report,
    _review,
    _round,
    _run,
    _tier1_run,
    _touch,
    _upgraded,
    _verdicts,
    _verified,
    factory,
    sdlc,
)

# ---------------------------------------------------------------- depth set by risk


def test_with_no_sensitive_list_every_run_is_full(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"], out["limit"]) == ("full", FULL, 3)


def test_a_diff_touching_no_sensitive_path_runs_light(tmp_path, capsys) -> None:
    root = _change(tmp_path, 1, config=LISTED)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"], out["limit"]) == ("light", ["code", "behaviour"], 2)
    _review(root, 1, "code", "VERDICT: PASS")
    _review(root, 1, "behaviour", "VERDICT: PASS")
    assert _verdicts(root, capsys)["next"] == "approve", "light's reviewers complete the round"


def test_a_sensitive_path_deepens_the_run_and_it_never_lightens(tmp_path, capsys) -> None:
    root = _change(tmp_path, config=LISTED)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:1: move it")
    _verified(root, 1, kept=["code: src/a.py:1: move it"])
    _touch(root, "src/secret/key.py")
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["sensitive"]) == ("full", ["src/secret/key.py"])
    assert out["missing"] == FULL and out["limit"] == 3
    for role in ("code", "security", "test"):
        _review(root, 2, role, "VERDICT: PASS")
    (root / "src" / "secret" / "key.py").unlink()
    out = _verdicts(root, capsys)
    assert out["depth"] == "full" and "never lightens" in out["why"]


def test_the_sensitive_list_is_the_base_branch_s_not_the_change_s(tmp_path, capsys) -> None:
    root = _change(tmp_path, config=LISTED)
    (root / ".sdlc" / "config.toml").write_text('[review]\nsensitive = ["src/"]\n')
    _touch(root, "src/a.py")
    _build_report(root, 1)
    assert _verdicts(root, capsys)["depth"] == "light", "editing the list here changes nothing"


def test_the_landing_code_is_reviewed_in_depth(tmp_path, capsys) -> None:
    """153 R10: this repo's own `[review] sensitive` names `closing.py` and `landing.py`, so a
    diff touching either runs full depth, while one elsewhere in `sdlc.py` or `factory.py` stays
    light; and ship's `risk_paths()` names the same two modules and not the scripts."""
    import tomllib

    listed = tomllib.loads((ROOT / ".sdlc" / "config.toml").read_text(encoding="utf-8"))
    sensitive = listed["review"]["sensitive"]
    config = "[review]\nsensitive = " + json.dumps(sensitive) + "\n"
    closing, landing = "scripts/closing.py", "plugins/factory/scripts/landing.py"
    scripts = ["scripts/sdlc.py", "plugins/factory/scripts/factory.py"]
    for path in (closing, landing, *scripts):
        assert (ROOT / path).exists(), path
    for n, path in enumerate((closing, landing)):
        root = _change(tmp_path / f"module-{n}", config=config)
        _touch(root, path)
        _build_report(root, 1)
        out = _verdicts(root, capsys)
        assert out["depth"] == "full" and path in out["sensitive"], (path, out)
    for n, path in enumerate(scripts):
        root = _change(tmp_path / f"script-{n}", config=config)
        _touch(root, path)
        _build_report(root, 1)
        out = _verdicts(root, capsys)
        assert out["depth"] == "light" and not out["sensitive"], (path, out)
    risky = sdlc.risk_paths([closing, landing, *scripts], sensitive)
    assert risky == [closing, landing], risky


def _light_round(tmp_path: Path, tier: object, factory_toml: str | None = None) -> Path:
    """A change at `tier` whose first build touches no sensitive path, with no review yet."""
    root = _change(tmp_path, tier, "build", config=LISTED)
    if factory_toml is not None:
        (root / ".sdlc" / "factory.toml").write_text(factory_toml, encoding="utf-8")
    _touch(root, "src/a.py")
    _build_report(root, 1)
    return root


def _on_base(root: Path, factory_toml: str) -> None:
    """`factory_toml` committed on the base branch too, where `[models]` and the rest of what
    shapes a run are read from, and left in the change's checkout as it was."""
    config = root / ".sdlc" / "factory.toml"
    _git(root, "checkout", "-q", "main")
    config.write_text(factory_toml, encoding="utf-8")
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "factory.toml")
    _git(root, "checkout", "-q", NAME)
    config.write_text(factory_toml, encoding="utf-8")


def test_a_tier_2_light_round_includes_the_test_reviewer(tmp_path, capsys) -> None:
    """R1, R2, R3, R7: a Tier 2's light rounds expect the test reviewer; a Tier 1's, or one whose
    tier won't read, don't; `start` names the same list for the run's one question."""
    both = ["code", "behaviour"]
    for tier, want in ((2, ["code", "test", "behaviour"]), (1, both), ("", both)):
        root = _light_round(tmp_path / f"tier-{tier or 'none'}", tier)
        out = _verdicts(root, capsys)
        assert (out["depth"], out["missing"], out["limit"]) == ("light", want, 2), tier
        _, start = _run(capsys, factory.cmd_start, root, "008", "build")
        assert start["light"]["reviewers"] == want and start["light"]["chosen"] is False, tier
    root = tmp_path / "tier-2" / "repo"
    _review(root, 1, "code", "VERDICT: PASS")
    _review(root, 1, "behaviour", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert (out["next"], out["missing"]) == ("review", ["test"]), "code alone is incomplete"
    _review(root, 1, "test", "VERDICT: PASS")
    assert _verdicts(root, capsys)["next"] == "approve"


def test_a_set_light_list_is_kept_at_either_tier(tmp_path, capsys) -> None:
    """R4, R5: a host's own `[light] reviewers` is used as set, and the Tier 2 default adds
    `test` only when the full depth runs it."""
    root = _light_round(tmp_path / "set", 2, '[light]\nreviewers = ["code"]\n')
    assert _verdicts(root, capsys)["missing"] == ["code"], "a list set by hand is kept"
    cfg = factory.load_config(root)[0]
    assert cfg["light"]["chosen"] is True
    assert factory.light_reviewers(cfg, 2) == factory.light_reviewers(cfg, 1) == ["code"]
    root = _light_round(tmp_path / "no-test", 2, 'reviewers = ["code", "security"]\n')
    assert _verdicts(root, capsys)["missing"] == ["code"], "never a reviewer the full depth lacks"


def test_a_light_round_includes_the_behaviour_reviewer(tmp_path, capsys) -> None:
    """136 R1: unset, `[light]` runs `behaviour` beside `code` at either tier, as the landing's
    own first check does, so a Tier 1 light round isn't complete without it."""
    root = _light_round(tmp_path, 1)
    cfg = factory.load_config(root)[0]
    assert factory.light_reviewers(cfg, 1) == ["code", "behaviour"]
    assert factory.light_reviewers(cfg, 2) == ["code", "test", "behaviour"], "REVIEWERS order"
    _review(root, 1, "code", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert (out["next"], out["missing"]) == ("review", ["behaviour"]), "code alone is incomplete"
    _review(root, 1, "behaviour", "VERDICT: PASS")
    assert _verdicts(root, capsys)["next"] == "approve"


def test_the_behaviour_reviewer_never_deepens_a_light_run(tmp_path, capsys) -> None:
    """136 R1: a light round holding `behaviour` keeps a Tier 1 run light into its next round."""
    root = _light_round(tmp_path, 1)
    for role in ("code", "behaviour"):
        _review(root, 1, role, "VERDICT: CHANGES", f"src/a.py:1: {role} fix")
    _verified(root, 1, kept=["code: src/a.py:1: code fix", "behaviour: src/a.py:1: behaviour fix"])
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"], out["limit"]) == ("light", ["code", "behaviour"], 2)


def test_the_test_reviewer_never_deepens_a_tier_2_light_run(tmp_path, capsys) -> None:
    """R6: a Tier 2 light round holding `code`, `test` and `behaviour` keeps the run light."""
    root = _light_round(tmp_path, 2)
    for role in ("code", "test", "behaviour"):
        _review(root, 1, role, "VERDICT: CHANGES", f"src/a.py:1: {role} fix")
    _verified(root, 1, kept=[f"{r}: src/a.py:1: {r} fix" for r in ("code", "test", "behaviour")])
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    want = ["code", "test", "behaviour"]
    assert (out["depth"], out["missing"], out["limit"]) == ("light", want, 2), out


def test_readme_names_the_light_reviewers_and_models() -> None:
    """136 R6: the README's rule for a Tier 1 light run says the reviewers `light_reviewers()`
    gives and the model `model_for()` gives each scaled reviewer, and gives its reasons."""
    text = " ".join((ROOT / "plugins" / "factory" / "README.md").read_text("utf-8").split())
    cfg = factory.load_config(Path("/nonexistent"))[0]
    light = factory._listed(factory.light_reviewers(cfg, 1))
    assert f"a Tier 1's light rounds run the {light} reviewers" in text, light
    models = {factory.model_for(r, cfg, 1, "light") for r in factory.SCALED}
    assert len(models) == 1, models
    (model,) = models
    assert f"Each reviewer runs on {model} at either depth and tier" in text, model
    assert f"Every scaled reviewer runs on {model}**" in text
    # The table under "Why these defaults" (changes 124, 125, 129 and 131) is history, not a rule:
    # no test can read it, so it is checked by hand against each change's `Close` commit.
    assert "### Why these defaults" in text and "Landing catches: k of n" in text


def test_a_host_s_own_depth_and_models_are_kept(tmp_path, capsys) -> None:
    """136 R9: a host that set `rounds`, `[light]` and `[models]` gets what it set from `start`:
    no default this change moved reaches it, at either tier."""
    own = (
        'reviewers = ["code", "security", "test", "behaviour"]\nrounds = 4\n'
        '[light]\nreviewers = ["code"]\nrounds = 1\n'
        '[models]\ncode = "haiku"\nbehaviour = "haiku"\ntest = "opus"\n'
    )
    for tier in (1, 2):
        root = _light_round(tmp_path / f"tier-{tier}", tier, own)
        _on_base(root, own)
        _, out = _run(capsys, factory.cmd_start, root, "008", "build")
        assert (out["reviewers"], out["rounds"]) == (FULL, 4), tier
        assert out["light"] == {"reviewers": ["code"], "rounds": 1, "chosen": True}, tier
        for level in ("light", "full"):
            models = out["models_at"][level]
            assert (models["code"], models["behaviour"], models["test"]) == (
                "haiku", "haiku", "opus"), (tier, level)  # fmt: skip
        assert out["max_runs"] == 2 + 4 * (4 + 2 + 2), tier
        assert _verdicts(root, capsys)["missing"] == ["code"], tier


def test_the_landing_review_judges_a_tier_2_light_run_with_its_test_reviewer(
    tmp_path, capsys
) -> None:
    """R8: after a resolved conflict, the landing review asks for the same tier's reviewers."""
    root = _light_round(tmp_path, 2)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "reviews" / "land-1").mkdir(parents=True)
    (folder / "runs").mkdir()
    (folder / "runs" / "land-resolved").write_text("", encoding="utf-8")
    _, out = _run(capsys, factory.landing.cmd_land_verdicts, root, "008")
    assert out["missing"] == ["code", "test", "behaviour"], out


@pytest.mark.parametrize(
    "text, problem",
    [
        ("Built it. The gate passed.\n", "has no `## Evidence` section"),
        ("Built it.\n\n## Evidence\n\nAll green.\n", "shows no command run"),
        ("Built.\n\n## Evidence\n\n$ ./check.sh\n12 passed\n$ pytest\nexit: 0\n", "`./check.sh`"),
        ("Built.\n\n## Evidence\n\n$ ./check.sh\n12 passed\n\n## Notes\n\nexit: 0\n", "no `exit:`"),
        (
            "Built.\n\n## Evidence\n\n$ uv run pytest -q | grep passed\n12 passed\n",
            "`uv run pytest -q | grep passed` has no `exit:`",
        ),
    ],
)
def test_a_builder_report_without_its_evidence_stops_the_run(
    tmp_path, capsys, text: str, problem: str
) -> None:
    root = _change(tmp_path)
    _report(root, 1, text)
    out = _verdicts(root, capsys)
    assert out["next"] == "stop"
    assert any("build/round-1.md" in p and problem in p for p in out["problems"]), out["problems"]


# 123 R1: what the script can tell changes nothing, and what it can't.
READS = [
    "cat plan.md",
    "grep -n x a ; grep -n x b ; cmp a b",
    "git -C . show HEAD:a",
    "sed -n '1,5p' f",
    "jq '.a | .b' f.json",
    "awk '$2 > 0 {print $1}' f",
    "awk -F, -v n=2 '{print $n}' f",
    "cat a 2>&1",
    "rg -n x src",
    "file x",
    "file -b -m magic x",
    "git diff",
    "git diff --text --no-ext-diff --no-textconv",
    "git log -p --exit-code",
    "git log --format='%H %s'",
    "git show HEAD",
    "git log --no-show-signature -1",
]
NON_READS = [
    "./check.sh",
    "uv run pytest -q | grep passed",
    "sed -i s/a/b/ f",
    "cat a > b",
    "cat $(x)",
    "find . -delete",
    "git diff --output=f",
    "tee f",
    "xargs rm",
    "X=1 cat f",
    "jq . f > g",
    "awk '{print > \"out\"}' f",
    "awk '{print | \"sh\"}' f",
    "awk 'BEGIN{system(\"rm f\")}'",
    "awk -i inplace '{print}' f",
    "awk -f prog.awk f",
    "awk 'BEGIN{system (\"rm f\")}'",
    "cat a >2",
    "cat a > 2",
    "echo hi >> 1",
    "cat a 2>1",
    "cat a &>1",
    "rg --pre ./x y",
    "rg --pre=./x y",
    "rg --pre-glob '*.gz' --pre ./x y",
    "file -C -m magic",
    "file -bC -m magic",
    "file --compile -m magic",
    "file --comp -m magic",
    "git diff --ext-diff",
    "git log -p --ext",
    "git show --textconv HEAD:a",
    "git -C . blame --textc a",
    "git cat-file --textconv HEAD:a",
    "git -c diff.external=./x diff",
    "git log --show-signature",
    "git show --show-signature HEAD",
    "git -C . log -1 --show-signature --oneline",
    "git log --format=%G?",
    "git log --pretty=format:'%h %GS'",
    "git log --pretty=tformat:%GK",
    "git show -s --format='%GG' HEAD",
    "git shortlog --format=%GS",
    "git log --format %G?",
    "git log --pretty %GF",
    "git -c log.showSignature=true log",
]


@pytest.mark.portable
def test_a_read_is_only_what_the_script_can_tell_changes_nothing() -> None:
    """123 R1: `is_read()` passes only the closed allowlist, judged stage by stage; anything it
    can't see into, or that writes, redirects or runs something else, is not a read."""
    wrong = [c for c in READS if not factory.is_read(c)]
    wrong += [c for c in NON_READS if factory.is_read(c)]
    assert not wrong, wrong


@pytest.mark.portable
def test_a_read_showing_its_output_needs_no_exit() -> None:
    """123 R2: a read followed by a non-blank, non-fence line owes no `exit:`, fenced or not."""
    plain = "## Evidence\n\n$ cat plan.md\n# Plan\n$ grep -n x a ; cmp a b\n3:x\n"
    fenced = "## Evidence\n\n```\n$ git -C . show HEAD:a\nline\n```\n"
    assert factory.read_evidence(plain, "r") == []
    assert factory.read_evidence(fenced, "r") == []


@pytest.mark.portable
def test_a_read_naming_a_mark_is_still_a_read() -> None:
    """135: a filed reply names this machine's paths by `<home>` and `<path-to-clone>`, whose `<`
    and `>` are words there, never redirects: a read naming one owes no `exit:`, as the path it
    replaced didn't. A real redirect beside a mark still makes it a non-read."""
    for mark in (factory.HOME_MARK, factory.CLONE_MARK):
        command = f"ls {mark}/.nvm/bin"
        assert factory.is_read(command), command
        text = f"## Evidence\n\n$ {command}\nnode\n"
        assert factory.read_evidence(text, "r") == [], text
        assert not factory.is_read(f"cat {mark}/a > {mark}/b")
        assert not factory.is_read(f"cat {mark}/a >out")


@pytest.mark.portable
def test_a_silent_read_still_needs_its_exit() -> None:
    """123 R3: a read that prints nothing, before the next `$` or the end, a fence or a blank line
    all it shows, still owes its exit: the exit is its only result."""
    for text in (
        "## Evidence\n\n$ cmp a b\n$ ./check.sh\n1 passed\nexit: 0\n",
        "## Evidence\n\n```\n$ cmp a b\n\n```\n",
    ):
        assert factory.read_evidence(text, "r") == ["r: `cmp a b` has no `exit:` line"], text


@pytest.mark.portable
def test_evidence_citing_the_gate_record_is_a_read() -> None:
    """155 R10: a reviewer's evidence may cite the gate's record by reading it, which owes no
    exit; a run of `factory.py check` is a command like any other, and owes its own."""
    record = ".sdlc/work/008-reopen-drafts/build/round-1.gate.md"
    for cite in (f"cat {record}", f"head -n 3 {record}"):
        text = f"## Evidence\n\n$ {cite}\nGATE: PASS\n"
        assert factory.read_evidence(text, "r") == [], cite
    run = "uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 008"
    assert factory.read_evidence(f"## Evidence\n\n$ {run}\n12 passed\n", "r") == [
        f"r: `{run}` has no `exit:` line"
    ]


def test_a_builders_read_needs_no_exit(tmp_path, capsys) -> None:
    """123 R6: the builder's report goes through the same parser: its gate shows its exit, a read
    after it shows only its output, and the run goes on to review."""
    root = _change(tmp_path)
    evidence = "$ ./check.sh\n12 passed\nexit: 0\n$ cat plan.md\n# Plan\n"
    _report(root, 1, f"Built.\n\n## Evidence\n\n{evidence}")
    out = _verdicts(root, capsys)
    assert (out["next"], out["problems"]) == ("review", []), out


def test_a_report_showing_each_command_and_its_exit_goes_on(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    fenced = "```\n$ ./check.sh\n12 passed\nexit: 0\n$ uv run pytest -q\n3 failed\nexit: 1\n```\n"
    _report(root, 1, f"Built.\n\n## Evidence\n\n{fenced}")
    out = _verdicts(root, capsys)
    assert (out["next"], out["problems"]) == ("review", []), "a failing exit is evidence too"


def test_only_the_newest_report_owes_evidence(tmp_path, capsys) -> None:
    """A run started before the rule keeps its old reports; the next one is checked."""
    root = _change(tmp_path)
    _report(root, 1, "Built before evidence was asked for.\n")
    _round(root, 1, code="CHANGES")
    _verified(root, 1, kept=["code: code fix 1"])
    _build_report(root, 2)
    assert _verdicts(root, capsys)["next"] == "review"


def test_the_behaviour_check_owes_evidence_too(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1)
    reply = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "behaviour.md"
    reply.write_text("VERDICT: PASS\n\n## Notes\n\nIt ran fine.\n")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop"
    assert any("reviews/round-1/behaviour.md" in p for p in out["problems"]), out["problems"]


def test_a_host_s_own_reviewers_are_kept_and_behaviour_is_one_it_can_name(tmp_path) -> None:
    (tmp_path / ".sdlc").mkdir()
    config = tmp_path / ".sdlc" / "factory.toml"
    config.write_text('reviewers = ["code", "test"]\n', encoding="utf-8")
    assert factory.load_config(tmp_path)[0]["reviewers"] == ["code", "test"]
    config.write_text('reviewers = ["behaviour"]\n', encoding="utf-8")
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["reviewers"] == ["behaviour"] and warnings == []
    assert factory.max_runs(factory.load_config(tmp_path / "none")[0]) == 26


@pytest.mark.parametrize(
    "patterns",
    [["src/secret/"], ["*.toml"], ["check.sh", ".claude/*"], ["src/*/key.py"], []],
)
def test_the_risk_matcher_is_sdlc_s_own(patterns: list[str]) -> None:
    paths = ["src/secret/key.py", "check.sh", ".claude/settings.json", "pyproject.toml", "a.py"]
    assert factory.risk_paths(paths, patterns) == sdlc.risk_paths(paths, patterns)


def test_the_factorys_copies_of_ships_notes_and_cap_match_sdlcs() -> None:
    """103: the landing writes the `Skill evals:` and `Fresh review:` lines ship reads, and names
    the cases' cost cap, each from a copy, since the factory's cached copy has no `sdlc.py`."""
    assert factory.CASES_RE.pattern == sdlc.CASES_RE.pattern
    assert factory.FRESH_RE.pattern == sdlc.FRESH_RE.pattern
    assert str(factory.CASE_CAP_USD) == sdlc.CASE_CAP["change"][1]


def test_the_factorys_reading_of_case_failures_matches_sdlcs() -> None:
    """156 R13: the landing names a failed case's graders from the run's record with a copy of
    `sdlc.py`'s reading."""
    record = {"verdicts": {
        "a": {"result": "failed", "runs": [{"graders": [{"name": "x"}, {"name": "y"}]},
                                           {"graders": [{"name": "y"}, {"name": "z"}]}]},
        "b": {"result": "passed on rerun", "runs": [{"graders": [{"name": "x"}]}]},
        "c": {"result": "failed", "runs": []}, "d": "nonsense"}}  # fmt: skip
    assert sdlc.cases_failures(record) == {"a": ["x", "y", "z"], "c": []}
    for r in (record, {}, None, {"verdicts": []}):
        assert factory.landing.cases_failures(r) == sdlc.cases_failures(r)


# ---------------------------------------------------------------- the build gate's question


TAIL = (
    "an arbiter weighs each round's findings, the approver decides, at most 26 agent runs, agents "
    "in auto, all left uncommitted at stage: test?"
)


def _question(root: Path, capsys) -> str | None:
    _, out = _run(capsys, factory.cmd_start, root, "008", "build")
    return out["question"]


def test_start_words_the_build_question_without_a_spec(tmp_path, capsys) -> None:
    """The plain form, word for word as the skill held it: no gate, no sensitive list, no `[ui]`."""
    root = _change(tmp_path, 1, "plan")
    assert _question(root, capsys) == (
        f"Run the factory on {NAME}: the builder plans and builds it, with no gate configured, "
        "code, security, test and behaviour review it in up to 3 rounds, "
        + TAIL
        + " (yes / change the reviewers or rounds / no)"
    )


def test_the_build_question_names_the_base_branch_s_gate_and_light_depth(tmp_path, capsys):
    """The gate clause and the light parenthesis come from the base branch's config alone."""
    config = '[commands]\ncheck = "./check.sh"\n\n[review]\nsensitive = ["src/auth/"]\n'
    root = _change(tmp_path, 1, "plan", config=config)
    assert _question(root, capsys) == (
        f"Run the factory on {NAME}: the builder plans and builds it, the base branch's gate "
        "./check.sh runs on each build before any reviewer (up to 2 fixes a round), code, "
        "security, test and behaviour review it in up to 3 rounds (or code and behaviour in up "
        "to 2 rounds when the diff touches no sensitive path), "
        + TAIL
        + " (yes / change the reviewers or rounds / no)"
    )
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "true"\n', encoding="utf-8")
    assert "gate ./check.sh runs" in _question(root, capsys), "the change's own copy never counts"


UI_TABLE = '[ui]\nserve = "npm run dev"\nshoot = "shot {url} {out}"\npaths = ["web/", "*.css"]\n'


@pytest.mark.parametrize("missing", [None, "serve", "shoot", "paths"])
def test_the_build_question_names_ui_review_only_when_it_can_run(tmp_path, capsys, missing):
    root = _change(tmp_path, 1, "plan")
    ui = "\n".join(
        line for line in UI_TABLE.splitlines() if not missing or not line.startswith(missing)
    )
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    _commit_on_main(root, ".sdlc/factory.toml", ui + "\n")
    _git(root, "checkout", "-q", NAME)
    clause = (
        "review it in up to 3 rounds, and, on a diff touching web/, *.css, the ui and ux "
        "reviewers, which start npm run dev, an arbiter"
    )
    assert (clause in _question(root, capsys)) is (missing is None)


def test_the_build_question_asks_to_write_a_spec_draft(tmp_path, capsys) -> None:
    root = _change(tmp_path, 2, "plan")
    assert _question(root, capsys) == (
        f"Write this spec and run the factory on {NAME}: the builder plans and builds it, with no "
        "gate configured, code, security, test and behaviour review it in up to 3 rounds, "
        + TAIL
        + " (yes / revise a requirement / change the reviewers or rounds / no)"
    )


def test_the_build_question_sends_an_escalated_change_back(tmp_path, capsys) -> None:
    root = _change(tmp_path, 1, "test")
    _escalated(root)
    assert _question(root, capsys) == (
        f"Send {NAME} back to the factory: decision.md kept as decision-1.md, the builder rebuilds "
        "from round 4 with the approver's reasons, with no gate configured, code, security, test "
        "and behaviour review it in up to 3 more rounds, an arbiter weighs each round's findings, "
        "the approver decides again, at most 26 agent runs, agents in auto, all left uncommitted "
        "at stage: test? (yes / change the reviewers or rounds / no)"
    )


def test_the_build_question_carries_on_an_upgraded_run(tmp_path, capsys) -> None:
    root, folder = _tier1_run(tmp_path, config='[review]\nsensitive = ["src/auth/"]\n')
    _upgraded(root, folder)
    assert _question(root, capsys) == (
        f"Write this spec and carry on {NAME}'s factory run as Tier 2: the builder, resumed, "
        "rewrites plan.md against it and builds round 2, with no gate configured, code, security, "
        "test and behaviour review it in up to 3 more rounds (or code, test and behaviour in up "
        "to 2 rounds when the diff touches no sensitive path), an arbiter weighs each round's "
        "findings, the approver decides, at most 26 more agent runs, agents in auto, all left "
        "uncommitted at stage: test? (yes / revise a requirement / change the reviewers or "
        "rounds / no)"
    )


def test_no_build_question_for_a_refusal_or_a_tier_1_spec(tmp_path, capsys) -> None:
    root = _change(tmp_path, 2, "test")
    assert _question(root, capsys) is None, "a test change with no decision is refused"
    _, out = _run(capsys, factory.cmd_start, _change(tmp_path / "b", 1, "plan"), "008", "spec")
    assert out["refusals"] and out["question"] is None, "a Tier 1 change has no spec to ask about"
    code, out = _run(
        capsys, factory.cmd_start, _change(tmp_path / "c", branch="main-ish"), "008", "build"
    )
    assert code == 1 and out["question"] is None, "no worktree of its own"


def test_start_words_the_spec_question(tmp_path, capsys) -> None:
    """2026-11-18-10: the spec gate's question is the script's, as the build gate's is."""
    _, out = _run(capsys, factory.cmd_start, _change(tmp_path, 2, "plan"), "008", "spec")
    assert out["question"] == (
        f"Write this as .sdlc/work/{NAME}/spec.md and advance the change to stage: design? "
        "(yes / revise a requirement)"
    )


def test_no_build_question_without_a_base_branch(tmp_path, capsys) -> None:
    """125: the gate and depth clauses are the base branch's, so with none `start` refuses rather
    than word a question saying there is no gate."""
    root = _change(tmp_path, 1, "plan")
    _git(root, "branch", "-q", "-m", "main", "trunk")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 1 and out["question"] is None
    assert "no base branch: set [git] base in .sdlc/config.toml" in out["refusals"]


@pytest.mark.parametrize(
    "names, said",
    [([], "no reviewer"), (["code"], "code"), (["code", "test"], "code and test"),
     (["code", "security", "test"], "code, security and test")],
)  # fmt: skip
def test_the_build_question_lists_reviewers_as_a_sentence(names, said) -> None:
    assert factory._listed(names) == said
