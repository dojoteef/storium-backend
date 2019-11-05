"""
A very basic example of a figmentator
"""
import time
import logging
from typing import Any, Dict, List, Optional
import unicodedata

from figmentator.figment.base import Figmentator
from figmentator.models.figment import FigmentContext
from figmentator.models.range import RangeUnits
from figmentator.models.storium import SceneEntry
from figmentator.models.suggestion import SuggestionType


def NFC(text):
    """
    Normalize the unicode string into NFC form

    Read more about that here:
    https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize
    """
    return unicodedata.normalize("NFC", text)


class SimpleFigmentator(Figmentator):
    """
    A dead simple figmentator that generates useless scene_entry suggestions
    """

    LOREM_IPSUM = NFC(
        """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius,
turpis et commodo pharetra, est eros bibendum elit, nec luctus magna felis
sollicitudin mauris. Integer in mauris eu nibh euismod gravida. Duis ac tellus
et risus vulputate vehicula. Donec lobortis risus a elit. Etiam tempor. Ut
ullamcorper, ligula eu tempor congue, eros est euismod turpis, id tincidunt
sapien risus a quam. Maecenas fermentum consequat mi. Donec fermentum.
Pellentesque malesuada nulla a mi. Duis sapien sem, aliquet nec, commodo eget,
consequat quis, neque. Aliquam faucibus, elit ut dictum aliquet, felis nisl
adipiscing sapien, sed malesuada diam lacus eget erat. Cras mollis scelerisque
nunc. Nullam arcu. Aliquam consequat. Curabitur augue lorem, dapibus quis,
laoreet et, pretium ac, nisi. Aenean magna nisl, mollis quis, molestie eu,
feugiat in, orci. In hac habitasse platea dictumst."""
    )

    # Due to using split(), the behavior when specifying a range in characters
    # is different than what happens when specifying a range in words. We use
    # the split version for words, so whitespace will be trimmed, e.g. newlines
    # will be removed. For characters, these would be preserved. If this were
    # not just a simple example to demonstrate the API, this would have to be
    # dealt with more appropriately.
    LOREM_IPSUM_SPLIT = LOREM_IPSUM.split()

    def __init__(self, suggestion_type: SuggestionType):
        """ Initialize the figmentator """
        if suggestion_type is not SuggestionType.scene_entry:
            raise ValueError("This figmentator can only generate scene entries!")

        super().__init__(suggestion_type)

        self.preprocess_time = 1
        self.generation_time = 2

    def startup(self, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        This method should perform any necessary startup, such as loading the model
        parameters. After this method completes, the model should be ready to perform
        preprocessing and suggestion generation. It should return whether it was able to
        successfully startup.
        """
        if properties:
            self.preprocess_time = properties.get(
                "preprocess_time", self.preprocess_time
            )
            self.generation_time = properties.get(
                "generation_time", self.generation_time
            )

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
        time.sleep(self.preprocess_time)  # simulate slow preprocessing
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

            text = type(self).LOREM_IPSUM
            if context.range:
                if len(context.range.ranges) > 1:
                    logging.warning("Failed to generate text.")
                    continue

                entry_range = context.range.ranges[0]
                if not entry_range.end:
                    logging.warning("Failed to generate text.")
                    continue

                if context.range.unit == RangeUnits.words:
                    text = type(self).LOREM_IPSUM_SPLIT
                    index = len(entry.description.split())
                else:
                    index = len(NFC(entry.description))

                if entry_range.start is not None and entry_range.start != index:
                    logging.warning("Failed to generate text.")
                    continue

                range_end = index + entry_range.end
                new_text = text[index:range_end]

                past_end = range_end - len(text)
                if past_end > 0:
                    # Wrap if needed, but include a space before wrapping
                    new_text += [" "] if isinstance(new_text, list) else " "
                    new_text += text[:past_end]

                if context.range.unit == RangeUnits.words:
                    if entry.description and not entry.description[:-1].isspace():
                        # Add a starting space if needed
                        new_text = [" "] + new_text

                    # It's a list and we need a string
                    new_text = " ".join(new_text)

                text = new_text

            entry.description += text
            entries.append(entry)

        time.sleep(self.generation_time)  # simulate a slow generation process
        return entries
