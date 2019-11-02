"""
Additional utilities
"""
import re


def snake_case(name: str) -> str:
    """
    Convert name from CamelCase to snake_case
    See https://stackoverflow.com/a/1176023
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
