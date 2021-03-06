"""
This router handles the suggestion endpoints.
"""
from typing import Any, Dict

from aiocache import caches
from pydantic import ValidationError
from fastapi import APIRouter, Body, Path, Query, HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import (
    HTTP_200_OK,
    HTTP_206_PARTIAL_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
)

from figmentator.models.range import Range
from figmentator.models.figment import FigmentContext, FigmentStatus
from figmentator.models.storium import SceneEntry
from figmentator.models.suggestion import SuggestionType
from figmentator.figment.scheduler import Figmentators
from figmentator.utils.routing import CompressibleRoute


router = APIRouter()
router.route_class = CompressibleRoute


@router.post(
    "/{story_id}/new",
    status_code=HTTP_200_OK,
    summary="Generate a figment",
    response_model=SceneEntry,
)
async def new(
    request: Request,
    response: Response,
    story_id: str = Path(
        ..., description="""The id of the story to generate the figment for."""
    ),
    entry: SceneEntry = Body(
        ..., description="""The current entry representing the move in progress"""
    ),
    suggestion_type: SuggestionType = Query(
        ..., description="""The suggestion type to generate"""
    ),
):
    """
    Create a new figment. Returns a 404 if the story data cannot be found.
    """
    cache = caches.get("default")
    story_data = await cache.get(f"{suggestion_type}:{story_id}")
    if story_data is None:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Unknown story")

    context_dict: Dict[str, Any] = {"data": story_data, "entry": entry.copy()}
    try:
        figment_range = request.headers.get("Range")
        if figment_range:
            context_dict["range"] = Range.validate(figment_range)
    except ValidationError:
        raise HTTPException(
            HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, "Invalid range specified!"
        )

    context = FigmentContext(**context_dict)
    context = await Figmentators.figmentate(suggestion_type, context)
    if context.status == FigmentStatus.failed:
        raise HTTPException(HTTP_406_NOT_ACCEPTABLE, "Unable to generate suggestion!")

    if context.status == FigmentStatus.partial:
        response.status_code = HTTP_206_PARTIAL_CONTENT

    return context.entry
