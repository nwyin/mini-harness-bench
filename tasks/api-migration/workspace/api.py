"""API v1 endpoints."""

from __future__ import annotations

from app import Request, Response, Router
from models import ORDERS, PRODUCTS, USERS

router = Router()


# --- Users ---


@router.get("/api/v1/users")
def list_users(request: Request, params: dict[str, str]) -> Response:
    """List all active users."""
    users = [u.to_dict() for u in USERS if u.is_active]
    return Response(200, users)


@router.get("/api/v1/users/{user_id}")
def get_user(request: Request, params: dict[str, str]) -> Response:
    """Get a single user by ID."""
    uid = int(params["user_id"])
    for u in USERS:
        if u.user_id == uid:
            return Response(200, u.to_dict())
    return Response(404, {"error": "user_not_found"})


# --- Products ---


@router.get("/api/v1/products")
def list_products(request: Request, params: dict[str, str]) -> Response:
    """List all products."""
    products = [p.to_dict() for p in PRODUCTS]
    return Response(200, products)


@router.get("/api/v1/products/{product_id}")
def get_product(request: Request, params: dict[str, str]) -> Response:
    """Get a single product by ID."""
    pid = int(params["product_id"])
    for p in PRODUCTS:
        if p.product_id == pid:
            return Response(200, p.to_dict())
    return Response(404, {"error": "product_not_found"})


# --- Orders ---


@router.get("/api/v1/orders")
def list_orders(request: Request, params: dict[str, str]) -> Response:
    """List orders, optionally filtered by user_id."""
    user_id = request.query.get("user_id")
    orders = ORDERS
    if user_id:
        orders = [o for o in orders if o.user_id == int(user_id)]
    return Response(200, [o.to_dict() for o in orders])
