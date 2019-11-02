"""
This router handles the stories endpoints.
"""
from typing import Any, Dict
from fastapi import APIRouter, Body
from starlette.status import HTTP_200_OK

from figmentator.models.utils import Field
from figmentator.utils.routing import CompressibleRoute


router = APIRouter()
router.route_class = CompressibleRoute


@router.post("/snapshot", status_code=HTTP_200_OK, summary="Preprocess a Story")
async def snapshot(
    story_id: str = Body(..., description="""A unique identifier for the story"""),
    story: Dict[str, Any] = Body(
        ...,
        description="""A story in the [Storium export format]
        (https://storium.com/help/export/json/0.9.2).""",
    ),
):
    """
    This method accepts a snapshot of a story. It does any necessary preprocessing and
    caches it off, such that subsequent requests generations requests can use the cached
    off data.
    """
