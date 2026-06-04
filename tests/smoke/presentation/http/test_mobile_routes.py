import httpx
from fastapi import status

API = "/api/v1"

EXPECTED_ROUTE_RESPONSES = {status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_CONTENT}

MOBILE_GET_ENDPOINTS = [
    f"{API}/mobile/clients/me",
    f"{API}/mobile/clients/me/verification",
    f"{API}/mobile/clients/me/fines",
    f"{API}/mobile/clients/me/payments",
    f"{API}/mobile/clients/me/outstanding",
    f"{API}/mobile/notifications/",
    f"{API}/mobile/vehicles",
    f"{API}/mobile/rentals",
    f"{API}/mobile/rentals/active",
]

MOBILE_POST_ENDPOINTS = [
    f"{API}/mobile/rentals",
    f"{API}/mobile/payments/record",
    f"{API}/mobile/devices/register",
]

MOBILE_PATCH_ENDPOINTS = [
    f"{API}/mobile/clients/me",
    f"{API}/mobile/clients/me/notification-preferences",
]


async def test_mobile_get_endpoints_are_reachable(
    smoke_client: httpx.AsyncClient,
) -> None:
    for path in MOBILE_GET_ENDPOINTS:
        r = await smoke_client.get(path)
        assert r.status_code in EXPECTED_ROUTE_RESPONSES, (
            f"GET {path} returned {r.status_code}, expected 401 or 422"
        )


async def test_mobile_post_endpoints_are_reachable(
    smoke_client: httpx.AsyncClient,
) -> None:
    for path in MOBILE_POST_ENDPOINTS:
        r = await smoke_client.post(path, json={})
        assert r.status_code in EXPECTED_ROUTE_RESPONSES, (
            f"POST {path} returned {r.status_code}, expected 401 or 422"
        )


async def test_mobile_patch_endpoints_are_reachable(
    smoke_client: httpx.AsyncClient,
) -> None:
    for path in MOBILE_PATCH_ENDPOINTS:
        r = await smoke_client.patch(path, json={})
        assert r.status_code in EXPECTED_ROUTE_RESPONSES, (
            f"PATCH {path} returned {r.status_code}, expected 401 or 422"
        )


async def test_mobile_nonexistent_returns_404(
    smoke_client: httpx.AsyncClient,
) -> None:
    r = await smoke_client.get(f"{API}/mobile/does-not-exist")
    assert r.status_code == status.HTTP_404_NOT_FOUND
