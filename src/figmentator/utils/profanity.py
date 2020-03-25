"""
This module is used to filter profanity.
"""
import json
import re
import string


class Profanity:
    """
    A class that encapsulates filtering profanity.
    """

    def __init__(self, profanity_path: str, character_map_path: str):
        with open(profanity_path, "rt") as file:
            self.profanity = [l.strip() for l in file.readlines()]

        with open(character_map_path, "rt") as file:
            self.character_map = json.load(file)

        # Fix up any punctuation that needs to be escaped
        for char_list in self.character_map.values():
            for idx, char in enumerate(char_list):
                if char in string.punctuation:
                    char_list[idx] = "\\" + char

        # Make a regex string to match any punctuation (appropriately escaped)
        escaped = ["\\" + c for c in string.punctuation]
        self.punctuation_regex_str = f"[{','.join(escaped)}]*"

        # Now create individual regex strings for each profanity word
        word_regexes = []
        for word in self.profanity:
            word_regexes.append(self.get_regex_str(word))

        # Finally compile them all into one giant regex
        self.regex = re.compile(
            rf'\b({"|".join(word_regexes)})(?=\s|\Z)', re.IGNORECASE
        )

    def get_regex_str(self, text: str) -> str:
        """
        Get a regular expression string for the given text that accounts for
        character/punction variations.
        """
        regex = ""
        for char in text:
            substitutions = (
                ["\\s"]
                if char in string.whitespace
                else self.character_map.get(char, [char])
            )
            regex += f"[{','.join(substitutions)}]{self.punctuation_regex_str}"

        return regex

    def filter(self, text: str) -> str:
        """
        Filter the passed in text to obfuscate profanity
        """
        return self.regex.sub(lambda x: "*" * len(x.group(0)), text)
