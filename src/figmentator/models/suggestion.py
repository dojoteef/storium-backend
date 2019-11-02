"""
Data models for suggestions.
"""
from enum import auto

from figmentator.models.utils import AutoNamedEnum


class SuggestionType(AutoNamedEnum):
    """ The type of suggestion. One of:

    - **scene_entry**: Suggest a scene entry
    """

    scene_entry = auto()
