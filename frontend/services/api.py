import os

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def get(path: str, *, params: dict | None = None, headers: dict | None = None, timeout: int = 10):
    return requests.get(f"{API_BASE_URL}{path}", params=params, headers=headers, timeout=timeout)


def post(path: str, *, json: dict | None = None, headers: dict | None = None, timeout: int = 10):
    return requests.post(f"{API_BASE_URL}{path}", json=json, headers=headers, timeout=timeout)


def put(path: str, *, json: dict | None = None, headers: dict | None = None, timeout: int = 10):
    return requests.put(f"{API_BASE_URL}{path}", json=json, headers=headers, timeout=timeout)


def delete(path: str, *, headers: dict | None = None, timeout: int = 10):
    return requests.delete(f"{API_BASE_URL}{path}", headers=headers, timeout=timeout)
