"""
Figment related models
"""
from enum import auto
from typing import Any, Optional

from pydantic import BaseModel, Field

from figmentator.models.range import Range
from figmentator.models.storium import SceneEntry
from figmentator.models.utils import AutoNamedEnum


class FigmentStatus(AutoNamedEnum):
    """ The status of a figmentate operation """

    pending = auto()
    failed = auto()
    partial = auto()
    completed = auto()


class FigmentContext(BaseModel):
    """
    This context contains the current scene entry, the cached off preprocessed story
    dict, and potentially a range specifying what portions of a suggestion to generate.
    """

    status: FigmentStatus = Field(
        FigmentStatus.pending,
        description="""The current status of the figment begin generated""",
    )
    range: Optional[Range] = Field(
        None,
        description="""If specified, this is the range of the figment to generate.""",
    )
    entry: SceneEntry = Field(
        ...,
        description="""The scene entry to modify in order to generate a suggestion""",
    )
    data: Any = Field(
        ..., description="""The preprocessed story data created by this figmentator""",
    )
