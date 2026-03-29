"""API v1 and v2 endpoints."""

from __future__ import annotations

from typing import Any

from app import Request, Response, Router
from models import ORDERS, PRODUCTS, USERS

router = Router()


# --- Helpers for v2 ---


def _snake_to_camel(name: str) -> str:
    """Convert a snake_case string to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _convert_keys(obj: Any) -> Any:
    """Recursively convert all dict keys from snake_case to camelCase."""
    if isinstance(obj, dict):
        return {_snake_to_camel(k): _convert_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_keys(item) for item in obj]
    return obj


def _paginated(items: list[dict], page: int = 1, page_size: int | None = None) -> dict:
    """Wrap a list of items in a pagination envelope."""
    total = len(items)
    if page_size is None:
        page_size = total
    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


def _v2_error(code: str, message: str) -> dict:
    """Create a v2-style error response body."""
    return {"error": {"code": code, "message": message}}


def _v2_single(data: dict) -> dict:
    """Wrap a single item in a v2 data envelope."""
    return {"data": data}


# --- V1: Users ---


@router.get("/api/v1/users")
def list_users_v1(request: Request, params: dict[str, str]) -> Response:
    users = [u.to_dict() for u in USERS if u.is_active]
    return Response(200, users)


@router.get("/api/v1/users/{user_id}")
def get_user_v1(request: Request, params: dict[str, str]) -> Response:
    uid = int(params["user_id"])
    for u in USERS:
        if u.user_id == uid:
            return Response(200, u.to_dict())
    return Response(404, {"error": "user_not_found"})


# --- V1: Products ---


@router.get("/api/v1/products")
def list_products_v1(request: Request, params: dict[str, str]) -> Response:
    products = [p.to_dict() for p in PRODUCTS]
    return Response(200, products)


@router.get("/api/v1/products/{product_id}")
def get_product_v1(request: Request, params: dict[str, str]) -> Response:
    pid = int(params["product_id"])
    for p in PRODUCTS:
        if p.product_id == pid:
            return Response(200, p.to_dict())
    return Response(404, {"error": "product_not_found"})


# --- V1: Orders ---


@router.get("/api/v1/orders")
def list_orders_v1(request: Request, params: dict[str, str]) -> Response:
    user_id = request.query.get("user_id")
    orders = ORDERS
    if user_id:
        orders = [o for o in orders if o.user_id == int(user_id)]
    return Response(200, [o.to_dict() for o in orders])


# --- V2: Users ---


@router.get("/api/v2/users")
def list_users_v2(request: Request, params: dict[str, str]) -> Response:
    users = [_convert_keys(u.to_dict()) for u in USERS if u.is_active]
    return Response(200, _paginated(users))


@router.get("/api/v2/users/{user_id}")
def get_user_v2(request: Request, params: dict[str, str]) -> Response:
    uid = int(params["user_id"])
    for u in USERS:
        if u.user_id == uid:
            return Response(200, _v2_single(_convert_keys(u.to_dict())))
    return Response(404, _v2_error("user_not_found", "User not found"))


# --- V2: Products ---


@router.get("/api/v2/products")
def list_products_v2(request: Request, params: dict[str, str]) -> Response:
    products = [_convert_keys(p.to_dict()) for p in PRODUCTS]
    return Response(200, _paginated(products))


@router.get("/api/v2/products/{product_id}")
def get_product_v2(request: Request, params: dict[str, str]) -> Response:
    pid = int(params["product_id"])
    for p in PRODUCTS:
        if p.product_id == pid:
            return Response(200, _v2_single(_convert_keys(p.to_dict())))
    return Response(404, _v2_error("product_not_found", "Product not found"))


# --- V2: Orders ---


@router.get("/api/v2/orders")
def list_orders_v2(request: Request, params: dict[str, str]) -> Response:
    user_id = request.query.get("user_id")
    orders = ORDERS
    if user_id:
        orders = [o for o in orders if o.user_id == int(user_id)]
    items = [_convert_keys(o.to_dict()) for o in orders]
    return Response(200, _paginated(items))
