"""
Additional utilities
"""
import re
import sys
from contextlib import contextmanager


def snake_case(name: str) -> str:
    """
    Convert name from CamelCase to snake_case
    See https://stackoverflow.com/a/1176023
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def camel_case(name: str) -> str:
    """
    Convert name from snake_case to CamelCase
    """
    return name.title().replace("_", "")


@contextmanager
def shadow_argv(argv):
    """ A context manager which allows you to modify sys.argv """
    saved_argv = sys.argv
    sys.argv = argv
    yield
    sys.argv = saved_argv
