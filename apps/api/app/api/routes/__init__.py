"""
API routes module.
"""

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to UAlberta Roadmap API"}


@api_router.get("/hello/{name}")
async def hello(name: str) -> dict[str, str]:
    """Example endpoint with path parameter."""
    return {"message": f"Hello, {name}!"}
