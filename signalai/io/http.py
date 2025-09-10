"""HTTP helper utilities for making requests with retries and timeouts."""

from __future__ import annotations

import time
from typing import Any

import requests
from requests import Response, RequestException

__all__ = ["request", "get", "get_json"]


def request(
    method: str,
    url: str,
    *,
    retries: int = 3,
    timeout: float = 10.0,
    backoff_factor: float = 0.5,
    **kwargs: Any,
) -> Response:
    """Perform an HTTP request with basic retry and timeout handling.

    Args:
        method: HTTP method such as ``"GET"`` or ``"POST"``.
        url: The URL to request.
        retries: Number of attempts before giving up. Defaults to ``3``.
        timeout: Timeout for each request in seconds. Defaults to ``10``.
        backoff_factor: Factor for exponential backoff between retries.
        **kwargs: Additional arguments forwarded to :func:`requests.request`.

    Returns:
        ``requests.Response`` object.

    Raises:
        :class:`requests.RequestException` if the request fails after the
        given number of retries or returns an error status code.
    """
    last_exc: RequestException | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except RequestException as exc:
            last_exc = exc
            if attempt == retries:
                raise
            sleep = backoff_factor * (2 ** (attempt - 1))
            time.sleep(sleep)
    # Should never reach here
    assert last_exc is not None
    raise last_exc


def get(url: str, **kwargs: Any) -> Response:
    """Convenience wrapper for ``GET`` requests."""
    return request("GET", url, **kwargs)


def get_json(url: str, **kwargs: Any) -> Any:
    """Return JSON content of a ``GET`` request."""
    return get(url, **kwargs).json()

