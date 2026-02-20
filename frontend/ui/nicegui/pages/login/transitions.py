"""State transition helpers for login submit flow."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginSubmitStart:
    loading: bool


@dataclass(frozen=True)
class LoginSubmitDone:
    loading: bool


def begin_login_submit() -> LoginSubmitStart:
    """Return state values used when login submit starts."""
    return LoginSubmitStart(loading=True)


def finalize_login_submit() -> LoginSubmitDone:
    """Return state values used when login submit finishes."""
    return LoginSubmitDone(loading=False)
