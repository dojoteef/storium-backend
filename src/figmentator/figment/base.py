"""
This defines the base API required for all figmentators.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from figmentator.models.figment import FigmentContext, FigmentStatus
from figmentator.models.suggestion import SuggestionType
from figmentator.utils import profanity


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
    def figmentate(self, contexts: List[FigmentContext]) -> List[FigmentContext]:
        """
        This method should generate a figment for each context in the list.

        It returns a list of scene entries with the suggestion filled in or
        None.
        """
        raise NotImplementedError()


class CharacterEntryFigmentator(Figmentator):  # pylint:disable=abstract-method
    """
    Base class for all character entry moves
    """

    def __init__(self, suggestion_type: SuggestionType):
        """ Initialize the Figmentator """
        super().__init__(suggestion_type)

        self.profanity = profanity.Profanity(
            "resources/profanity.txt", "resources/character_map.json"
        )

    @abstractmethod
    def process(self, context: FigmentContext) -> Optional[Dict[str, Any]]:
        """
        This method performs any processing needed before generating a suggestion
        """
        raise NotImplementedError()

    @abstractmethod
    def sample(self, processed: List[Dict[str, Any]]) -> List[Optional[str]]:
        """
        This method generates a batch of character entry text
        """
        raise NotImplementedError()

    def validate(self, context: FigmentContext) -> Optional[slice]:
        """
        This method should validate the passed in context
        """
        entry = context.entry

        if not entry.description:
            entry.description = ""

        if not context.range:
            logging.warning("Failed to generate character entry: no range specified")
            return None

        if len(context.range.ranges) > 1:
            logging.warning(
                "Failed to generate character entry: too many ranges specified"
            )
            return None

        text_range = context.range.slices[0]
        if not text_range.stop:
            logging.warning(
                "Failed to generate character entry: no range end specified"
            )
            return None

        index = len(context.range.unit.chunk(entry.description, keep_fragments=False))
        if text_range.start is not None and text_range.start != index:
            logging.warning(
                "Failed to generate character entry: unexpected range start specified"
            )
            return None

        return text_range

    def figmentate(self, contexts: List[FigmentContext]) -> List[FigmentContext]:
        """
        This method should generate a figment for each context in the list.

        It returns a list of scene entries with the suggestion filled in or
        None.
        """
        entry_segments: List[slice] = []
        processed_entries: List[Dict[str, Any]] = []
        for context in contexts:
            segment = self.validate(context)
            if not segment:
                context.status = FigmentStatus.failed
                continue

            processed = self.process(context)
            if processed is None:
                context.status = FigmentStatus.failed
                continue

            entry_segments.append(segment)
            processed_entries.append(processed)

        segments = iter(entry_segments)

        # Make sure we filter profanity that the model might generate
        samples = (
            (self.profanity.filter(s) if s else None)
            for s in self.sample(processed_entries)
        )
        for context in contexts:
            if context.status == FigmentStatus.failed:
                continue

            sample = next(samples)
            segment = next(segments)
            if not sample:
                context.status = FigmentStatus.failed
                continue

            assert context.range is not None
            assert context.entry.description is not None

            context.entry.description += sample
            chunks = context.range.unit.chunk(context.entry.description)

            # Mark the status as completed or partially completed
            if not sample or (context.range.is_finite() and len(chunks) > segment.stop):
                context.status = FigmentStatus.completed
            else:
                context.status = FigmentStatus.partial

        return contexts
