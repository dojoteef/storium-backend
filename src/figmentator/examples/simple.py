"""
A very basic example of a figmentator
"""
import time
from typing import Any, Dict, List, Optional

from figmentator.figment.base import CharacterEntryFigmentator
from figmentator.models.figment import FigmentContext
from figmentator.models.suggestion import SuggestionType


class SimpleFigmentator(CharacterEntryFigmentator):
    """
    A dead simple figmentator that generates useless scene_entry suggestions
    """

    LOREM_IPSUM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
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
        time.sleep(self.preprocess_time)  # simulate slow preprocessing
        return story_snapshot

    def process(self, context: FigmentContext) -> Optional[Dict[str, Any]]:
        """
        This method performs any processing needed before generating a suggestion
        """
        segment = self.validate(context)

        assert segment is not None
        assert context.range is not None
        return {"text": context.range.unit.chunk(type(self).LOREM_IPSUM)[segment]}

    def sample(self, processed: List[Dict[str, Any]]) -> List[str]:
        """
        This method generates a batch of character entry text
        """
        time.sleep(self.generation_time)  # simulate a slow generation process
        return [d["text"] for d in processed]
