"""
This router handles the suggestion endpoints.
"""
from fastapi import APIRouter, Body, HTTPException
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from figmentator.models.storium import SceneEntry
from figmentator.utils.routing import CompressibleRoute


router = APIRouter()
router.route_class = CompressibleRoute


@router.post(
    "/new",
    status_code=HTTP_200_OK,
    summary="Generate a figment",
    response_model=SceneEntry,
)
async def new(
    request: Request,
    story_id: str = Body(
        ..., description="""The id of the story to generate the figment for."""
    ),
    entry: SceneEntry = Body(
        ..., description="""The current context of the move in progress"""
    ),
):
    """
    Create a new figment. Returns a 404 if the story data cannot be found.
    """
    # if not story_found:
    #     raise HTTPException(HTTP_404_NOT_FOUND, detail="Unknown story")

    # content_range = request.headers.get('Range')
    return entry
