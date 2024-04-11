from typing import TypeAlias

try:
    import httpx
    import requests
except ImportError: ...

# TODO: Fix types
BaseHttpClientAuth: TypeAlias = "httpx.Auth | requests.auth.AuthBase | object | None"
BaseHttpClientResponse: TypeAlias = "httpx.Response | requests.Response | None"
