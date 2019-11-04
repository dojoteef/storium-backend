"""
This router handles the stories endpoints.
"""
from asyncio import gather
from typing import Any, Dict

from aiocache import caches
from fastapi import APIRouter, Body, HTTPException
from starlette.status import HTTP_200_OK, HTTP_406_NOT_ACCEPTABLE

from figmentator.utils.routing import CompressibleRoute
from figmentator.figment.factory import figmentator_factory


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
    cache_updates = []
    cache = caches.get("default")
    for figmentator in figmentator_factory.figmentators:
        cache_key = f"{figmentator.suggestion_type}:{story_id}"
        story_data = await cache.get(cache_key)
        preprocessed = figmentator.preprocess(story, story_data)
        cache_updates.append(cache.set(cache_key, preprocessed))

    if not cache_updates:
        raise HTTPException(HTTP_406_NOT_ACCEPTABLE, "Unable to process story!")

    await gather(*cache_updates)
