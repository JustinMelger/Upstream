from __future__ import annotations

from frontend.ui.nicegui.pages.ai_curator.transitions import begin_apply, begin_generate, finalize_apply, finalize_generate


def test_ai_curator_generate_transitions() -> None:
    start = begin_generate()
    assert start.generating is True
    assert start.meta_text == "Generating draft..."
    done = finalize_generate(count=3)
    assert done.generating is False
    assert done.meta_text == "Draft ready (3 courses)"


def test_ai_curator_apply_transitions() -> None:
    start = begin_apply()
    assert start.applying is True
    assert start.meta_text == "Creating courses..."
    done = finalize_apply()
    assert done.applying is False
    assert done.meta_text == "Done"
