"""
API routers.
"""

from .courses import router as courses_router
from .programs import router as programs_router
from .roadmap import router as roadmap_router

__all__ = ["courses_router", "programs_router", "roadmap_router"]
