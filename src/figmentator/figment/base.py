"""
This defines the base API required for all figmentators.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from figmentator.models.figment import FigmentContext
from figmentator.models.storium import SceneEntry
from figmentator.models.suggestion import SuggestionType


class Figmentator(ABC):
    """
    An abstract class which defines the required operations of a generation model.
    """

    def __init__(self, suggestion_type: SuggestionType):
        """ Initialize the Figmentator """
        self.suggestion_type = suggestion_type

    @abstractmethod
    def startup(self, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        This method should perform any necessary startup, such as loading the model
        parameters. After this method completes, the model should be ready to perform
        preprocessing and suggestion generation. It should return whether it was able to
        successfully startup.
        """
        raise NotImplementedError()

    @abstractmethod
    def shutdown(self) -> None:
        """
        This method should perform any necessary shutdown actions, such as releasing the
        model parameters. After this method completes, all resources used by the model
        should be released.
        """
        raise NotImplementedError()

    @abstractmethod
    def preprocess(
        self, story_snapshot: Dict[str, Any], data: Optional[Any] = None
    ) -> Any:
        """
        This method should perform any preprocessing required on the story needed before
        generating suggestions. It should return an object representing the
        preprocessed story. This object will be provided to the figmentate method.

        - story: A story as specified in https://storium.com/help/export/json/0.9.2
        - data: an optional object representing any previously preprocesed data from a
          previous snapshot of the same story
        """
        raise NotImplementedError()

    @abstractmethod
    def figmentate(self, contexts: List[FigmentContext]) -> List[Optional[SceneEntry]]:
        """
        This method should generate a figment for each context in the list.

        It returns a list of scene entries with the suggestion filled in or
        None.
        """
        raise NotImplementedError()
