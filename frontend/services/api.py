import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _with_auth(headers: dict | None) -> dict:
    merged = {}
    if headers:
        merged.update(headers)
    token = st.session_state.get("session_token", "")
    if token:
        merged.setdefault("X-Session-Token", token)
    return merged


def get(path: str, *, params: dict | None = None, headers: dict | None = None, timeout: int = 10):
    return requests.get(
        f"{API_BASE_URL}{path}",
        params=params,
        headers=_with_auth(headers),
        timeout=timeout,
    )


def post(path: str, *, json: dict | None = None, headers: dict | None = None, timeout: int = 10):
    return requests.post(
        f"{API_BASE_URL}{path}",
        json=json,
        headers=_with_auth(headers),
        timeout=timeout,
    )


def put(path: str, *, json: dict | None = None, headers: dict | None = None, timeout: int = 10):
    return requests.put(
        f"{API_BASE_URL}{path}",
        json=json,
        headers=_with_auth(headers),
        timeout=timeout,
    )


def delete(path: str, *, headers: dict | None = None, timeout: int = 10):
    return requests.delete(
        f"{API_BASE_URL}{path}",
        headers=_with_auth(headers),
        timeout=timeout,
    )
