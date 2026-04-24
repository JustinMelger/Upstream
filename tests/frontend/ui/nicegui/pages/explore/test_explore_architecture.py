from __future__ import annotations

import ast
from pathlib import Path

import pytest


_EXPLORE_DIR = Path("frontend/ui/nicegui/pages/explore")


def _imports_for(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(str(alias.name))
        elif isinstance(node, ast.ImportFrom):
            out.add(str(node.module or ""))
    return out


@pytest.mark.unit
def test_explore_pure_modules_do_not_import_nicegui() -> None:
    for filename in [
        "controller.py",
        "event_bindings.py",
        "list_flow.py",
        "mutations_flow.py",
        "orchestration.py",
        "state.py",
        "ui_glue.py",
        "view_model.py",
    ]:
        imports = _imports_for(_EXPLORE_DIR / filename)
        assert "nicegui" not in imports
        assert not any(name.startswith("nicegui.") for name in imports)


@pytest.mark.unit
def test_explore_page_imports_page_package_modules() -> None:
    imports = _imports_for(_EXPLORE_DIR / "page.py")
    assert "frontend.ui.nicegui.pages.explore.controller" in imports
    assert "frontend.ui.nicegui.pages.explore.detail_page" in imports
    assert "frontend.ui.nicegui.pages.explore.event_bindings" in imports
    assert "frontend.ui.nicegui.pages.explore.list_flow" in imports
    assert "frontend.ui.nicegui.pages.explore.list_sections" in imports
    assert "frontend.ui.nicegui.pages.explore.mutations_flow" in imports
    assert "frontend.ui.nicegui.pages.explore.share_flow" in imports
    assert "frontend.ui.nicegui.pages.explore.sections" in imports
    assert "frontend.ui.nicegui.pages.explore.state" in imports
    assert "frontend.ui.nicegui.pages.explore.ui_glue" in imports
    assert "frontend.ui.nicegui.pages.explore.view_model" in imports
    assert "frontend.ui.nicegui.pages.courses.controller" not in imports
    assert "frontend.ui.nicegui.pages.paths.controller" not in imports
    assert "frontend.ui.nicegui.pages.articles.controller" not in imports
    assert "frontend.ui.nicegui.services.courses_service" not in imports
    assert "frontend.ui.nicegui.services.articles_service" not in imports


@pytest.mark.unit
def test_explore_controller_depends_on_gateway_not_page_controllers() -> None:
    imports = _imports_for(_EXPLORE_DIR / "controller.py")
    assert "frontend.ui.nicegui.pages.explore.gateway" in imports
    assert "frontend.ui.nicegui.pages.courses.controller" not in imports
    assert "frontend.ui.nicegui.pages.paths.controller" not in imports
    assert "frontend.ui.nicegui.pages.articles.controller" not in imports


@pytest.mark.unit
def test_explore_ui_modules_are_the_only_modules_allowed_to_import_nicegui() -> None:
    allowed_ui_modules = {
        "actions.py",
        "detail_article.py",
        "detail_common.py",
        "detail_course.py",
        "detail_flow.py",
        "detail_path.py",
        "detail_video.py",
        "list_items.py",
        "list_sections.py",
        "page.py",
        "sections.py",
    }
    for path in sorted(_EXPLORE_DIR.glob("*.py")):
        imports = _imports_for(path)
        imports_nicegui = ("nicegui" in imports) or any(name.startswith("nicegui.") for name in imports)
        if imports_nicegui:
            assert path.name in allowed_ui_modules


@pytest.mark.unit
def test_explore_article_cards_use_compact_mode() -> None:
    src = (_EXPLORE_DIR / "list_items.py").read_text(encoding="utf-8")
    assert "render_article_card(" in src
    assert "compact_mode=True" in src


@pytest.mark.unit
def test_explore_detail_path_uses_unselect_endpoint_for_untracking() -> None:
    src = (_EXPLORE_DIR / "detail_path.py").read_text(encoding="utf-8")
    assert 'api.post(f"/paths/{pid}/unselect", {})' in src
    assert 'api.delete(f"/paths/{pid}/select")' not in src


@pytest.mark.unit
def test_explore_detail_path_reuses_shared_tracking_seed_helper_for_select() -> None:
    src = (_EXPLORE_DIR / "detail_path.py").read_text(encoding="utf-8")
    assert "select_path_and_seed_tracking(" in src


@pytest.mark.unit
def test_explore_detail_course_refreshes_route_after_tracking_mutations() -> None:
    src = (_EXPLORE_DIR / "detail_course.py").read_text(encoding="utf-8")
    assert 'refresh_url = f"/explore/courses/{cid}"' in src
    assert "ui.navigate.to(refresh_url)" in src
    assert 'if normalized_status == "interested":' in src


@pytest.mark.unit
def test_explore_detail_review_summaries_refresh_after_review_mutations() -> None:
    for filename in ["detail_course.py", "detail_article.py", "detail_video.py", "detail_path.py"]:
        src = (_EXPLORE_DIR / filename).read_text(encoding="utf-8")
        assert "on_changed=_handle_reviews_changed" in src


@pytest.mark.unit
def test_explore_detail_close_actions_return_to_matching_tab() -> None:
    common_src = (_EXPLORE_DIR / "detail_common.py").read_text(encoding="utf-8")
    assert "back_url: str = \"/explore\"" in common_src
    assert 'ui.link("Explore", str(back_url or "/explore"))' in common_src

    assert 'render_breadcrumb(label="Courses", back_url="/explore?tab=courses")' in (
        _EXPLORE_DIR / "detail_course.py"
    ).read_text(encoding="utf-8")
    assert 'render_breadcrumb(label="Articles", back_url="/explore?tab=articles")' in (
        _EXPLORE_DIR / "detail_article.py"
    ).read_text(encoding="utf-8")
    assert 'render_breadcrumb(label="Videos", back_url="/explore?tab=videos")' in (
        _EXPLORE_DIR / "detail_video.py"
    ).read_text(encoding="utf-8")
    assert 'render_breadcrumb(label="Learning Path", back_url="/explore?tab=paths")' in (
        _EXPLORE_DIR / "detail_path.py"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_explore_article_resource_link_opens_in_new_tab() -> None:
    src = (_EXPLORE_DIR / "detail_article.py").read_text(encoding="utf-8")
    assert 'ui.link(learning_item_source_action_label("article"), source_url).props("target=_blank")' in src
