"""build.py merges [[checkpoints]] into the trace and guards the step range. The checkpoint carries
the author's QUESTION only — never an answer; the real next state adjudicates (ADR-0011)."""

import pytest

from glassbox_tracer import BuildError
from glassbox_tracer.build import build_lesson

LESSON = '''
id = "cp-test"
title = "cp"
register = "procedural"
problem = "p"
author = "t"
created = "2026-06-25"
source = """
a = 1
b = 2
a = b
"""
[[checkpoints]]
step = 1
ask = "after a = b, what is a?"
'''


def _write(tmp_path, text):
    p = tmp_path / "x.lesson.toml"
    p.write_text(text, encoding="utf-8")
    return p


def test_checkpoint_flag_and_prompt_merged(tmp_path):
    obj = build_lesson(_write(tmp_path, LESSON))
    cps = [s for s in obj["trace"] if s.get("checkpoint")]
    assert len(cps) == 1
    assert cps[0]["step"] == 1
    assert cps[0]["checkpoint_prompt"] == "after a = b, what is a?"
    # no answer is ever stored on the step
    assert "answer" not in cps[0]


def test_checkpoint_without_ask_sets_flag_only(tmp_path):
    obj = build_lesson(_write(tmp_path, LESSON.replace('\nask = "after a = b, what is a?"', "")))
    cps = [s for s in obj["trace"] if s.get("checkpoint")]
    assert len(cps) == 1 and "checkpoint_prompt" not in cps[0]


def test_checkpoint_on_last_step_fails(tmp_path):
    # the trace has 3 steps (0,1,2); a checkpoint on the last has nothing to predict.
    with pytest.raises(BuildError, match="checkpoint step index"):
        build_lesson(_write(tmp_path, LESSON.replace("step = 1", "step = 2")))


def test_checkpoint_missing_step_fails(tmp_path):
    bad = LESSON.replace("step = 1\n", "")
    with pytest.raises(BuildError, match="needs a 'step'"):
        build_lesson(_write(tmp_path, bad))
