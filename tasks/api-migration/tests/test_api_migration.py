"""Tests for api-migration task."""

import os
import sys
from pathlib import Path


def _workspace():
    pp = os.environ.get("PYTHONPATH")
    if pp:
        return Path(pp)
    return Path(__file__).resolve().parent.parent / "workspace"


def _setup():
    ws = str(_workspace())
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup():
    for mod_name in list(sys.modules):
        if mod_name in ("api", "app", "models"):
            del sys.modules[mod_name]


def _dispatch(path, query=None):
    _setup()
    try:
        from api import router
        from app import Request

        req = Request("GET", path, query=query)
        return router.dispatch(req)
    finally:
        _cleanup()


# --- V1 tests (must still work) ---


def test_v1_list_users():
    resp = _dispatch("/api/v1/users")
    assert resp.status == 200
    body = resp.body
    assert isinstance(body, list)
    assert len(body) == 3  # 3 active users
    assert "user_name" in body[0]  # snake_case


def test_v1_get_user():
    resp = _dispatch("/api/v1/users/1")
    assert resp.status == 200
    assert resp.body["user_name"] == "alice"


def test_v1_list_products():
    resp = _dispatch("/api/v1/products")
    assert resp.status == 200
    assert isinstance(resp.body, list)
    assert len(resp.body) == 4


# --- V2 tests ---


def test_v2_list_users_pagination_envelope():
    resp = _dispatch("/api/v2/users")
    assert resp.status == 200
    body = resp.body
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "pageSize" in body
    assert body["total"] == 3  # 3 active users
    assert len(body["items"]) == 3


def test_v2_list_users_camel_case():
    resp = _dispatch("/api/v2/users")
    assert resp.status == 200
    first_user = resp.body["items"][0]
    assert "userName" in first_user
    assert "createdAt" in first_user
    assert "isActive" in first_user
    # Must NOT have snake_case keys
    assert "user_name" not in first_user
    assert "created_at" not in first_user


def test_v2_get_user_data_wrapper():
    resp = _dispatch("/api/v2/users/1")
    assert resp.status == 200
    body = resp.body
    assert "data" in body
    assert body["data"]["userName"] == "alice"


def test_v2_get_user_not_found_error_format():
    resp = _dispatch("/api/v2/users/999")
    assert resp.status == 404
    body = resp.body
    assert "error" in body
    assert isinstance(body["error"], dict)
    assert "code" in body["error"]
    assert "message" in body["error"]


def test_v2_list_products_camel_case():
    resp = _dispatch("/api/v2/products")
    assert resp.status == 200
    body = resp.body
    assert "items" in body
    first = body["items"][0]
    assert "productName" in first
    assert "unitPrice" in first
    assert "stockCount" in first
    assert "categoryName" in first


def test_v2_get_product_data_wrapper():
    resp = _dispatch("/api/v2/products/2")
    assert resp.status == 200
    body = resp.body
    assert "data" in body
    assert body["data"]["productName"] == "Gadget B"


def test_v2_list_orders_with_filter():
    resp = _dispatch("/api/v2/orders", query={"user_id": "1"})
    assert resp.status == 200
    body = resp.body
    assert "items" in body
    assert body["total"] == 2  # Alice has 2 orders
    first = body["items"][0]
    assert "orderId" in first
    assert "totalPrice" in first
    assert "shippingStatus" in first
    assert "orderDate" in first
