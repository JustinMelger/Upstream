"""First-login onboarding helpers for the Home page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, MutableMapping


HOME_INTRO_DISMISSED_KEY = "home_intro_dismissed_v1"


@dataclass(frozen=True, slots=True)
class IntroStep:
    """Single onboarding step."""

    title: str
    body: str


INTRO_STEPS: tuple[IntroStep, IntroStep, IntroStep] = (
    IntroStep(
        title="Track one course",
        body="Open Explore and use Track on any course card to start your personal queue.",
    ),
    IntroStep(
        title="Select one path",
        body="Choose one path in Explore to unlock milestone progress and your next step.",
    ),
    IntroStep(
        title="Review one shared item",
        body="Open Teams and leave a review on one shared learning item or path to keep momentum.",
    ),
)


def should_show_home_intro(*, storage_user: MutableMapping[str, Any]) -> bool:
    """Return whether the first-login intro should be visible."""
    return bool(storage_user.get(HOME_INTRO_DISMISSED_KEY) is not True)


def dismiss_home_intro(*, storage_user: MutableMapping[str, Any]) -> None:
    """Persist dismissal state for the first-login intro."""
    storage_user[HOME_INTRO_DISMISSED_KEY] = True
