"""
Figment related models
"""
from typing import Any, Optional

from pydantic import BaseModel, Field

from figmentator.models.range import Range
from figmentator.models.storium import SceneEntry


class FigmentContext(BaseModel):
    """
    This context contains the current scene entry, the cached off preprocessed story
    dict, and potentially a range specifying what portions of a suggestion to generate.
    """

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
