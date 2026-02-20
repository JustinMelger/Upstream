"""State transition helpers for AI Curator actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateStart:
    generating: bool
    meta_text: str


@dataclass(frozen=True)
class GenerateDone:
    generating: bool
    meta_text: str


@dataclass(frozen=True)
class ApplyStart:
    applying: bool
    meta_text: str


@dataclass(frozen=True)
class ApplyDone:
    applying: bool
    meta_text: str


def begin_generate() -> GenerateStart:
    """Return state values used when draft generation starts."""
    return GenerateStart(generating=True, meta_text="Generating draft...")


def finalize_generate(*, count: int) -> GenerateDone:
    """Return state values used when draft generation completes."""
    return GenerateDone(generating=False, meta_text=f"Draft ready ({max(0, int(count))} courses)")


def begin_apply() -> ApplyStart:
    """Return state values used when apply starts."""
    return ApplyStart(applying=True, meta_text="Creating courses...")


def finalize_apply() -> ApplyDone:
    """Return state values used when apply completes."""
    return ApplyDone(applying=False, meta_text="Done")
