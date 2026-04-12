from __future__ import annotations

from enum import StrEnum


class PrimaryPage(StrEnum):
    """Primary top-level pages."""

    HOME = "home"
    EXPLORE = "explore"
    TEAMS = "teams"
    PROFILE = "profile"


PRIMARY_PAGE_SUBTITLES: dict[PrimaryPage, str] = {
    PrimaryPage.HOME: "What should I do next? Continue learning and review team activity.",
    PrimaryPage.EXPLORE: "What can I discover? Search and share learning items and paths.",
    PrimaryPage.TEAMS: "See what teammates shared and reviewed recently.",
    PrimaryPage.PROFILE: "Review your personal and team learning stats in one place.",
}


def subtitle_for(page: PrimaryPage) -> str:
    """Return the contextual subtitle copy for a top-level page."""
    return PRIMARY_PAGE_SUBTITLES[page]
