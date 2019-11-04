"""
A very basic example of a figmentator
"""
from typing import Any, Dict, List, Optional

from figmentator.figment.base import Figmentator
from figmentator.models.figment import FigmentContext
from figmentator.models.storium import SceneEntry
from figmentator.models.suggestion import SuggestionType

class SimpleFigmentator(Figmentator):
    """
    A dead simple figmentator that generates useless scene_entry suggestions
    """

    LOREM_IPSUM = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure
dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
mollit anim id est laborum.
"""

    def __init__(self, suggestion_type: SuggestionType):
        """ Initialize the figmentator """
        if suggestion_type is not SuggestionType.scene_entry:
            raise ValueError("This figmentator can only generate scene entries!")

        super().__init__(suggestion_type)

    def startup(self, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        This method should perform any necessary startup, such as loading the model
        parameters. After this method completes, the model should be ready to perform
        preprocessing and suggestion generation. It should return whether it was able to
        successfully startup.
        """
        return True

    def shutdown(self) -> None:
        """
        This method should perform any necessary shutdown actions, such as releasing the
        model parameters. After this method completes, all resources used by the model
        should be released.
        """

    def preprocess(
        self, story_snapshot: Dict[str, Any], data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        This method should perform any preprocessing required on the story needed before
        generating suggestions. It must return a dictionary representing the
        preprocessed story. This dictionary will be provided to the figmentate method.

        - story: A story as specified in https://storium.com/help/export/json/0.9.2
        - data: an optional dictionary of any previously preprocesed data from a
          previous snapshot of the same story
        """
        return story_snapshot

    def figmentate(self, contexts: List[FigmentContext]) -> List[SceneEntry]:
        """
        This method should generate a figment for each context in the list.
        """
        entries: List[SceneEntry] = []
        for context in contexts:
            entry = context.entry.copy()
            if not entry.description:
                entry.description = ""

            entry.description += type(self).LOREM_IPSUM
            entries.append(entry)

        return entries
