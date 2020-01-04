"""
Utilities useful for defining models.
"""
import re
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, Union

from pydantic import Schema, ConstrainedStr, Json as _Json, datetime_parse


Json = Union[_Json, Dict[str, Any]]


class EmptyStr(ConstrainedStr):
    """
    An empty string
    """

    max_length = 0


class AutoNamedEnum(str, Enum):
    """ An enum that automatically uses the enum name for as its value """

    # pylint:disable=unused-argument,no-self-argument
    def _generate_next_value_(name, start, count, last_values):
        """ The value of the enum is always its name """
        return name

    # pylint:enable=unused-argument,no-self-argument


class Datetime(str):
    """ Datetime in the format specified by Storium """

    regex = re.compile(
        r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})"
        r" (?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2}) UTC"
    )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value) -> datetime:
        """ Validate/parse the datetime """
        if isinstance(value, datetime):
            # It's already a datetime!
            return value

        if not isinstance(value, str):
            raise ValueError(f"string: str expected not {type(value)}")

        match = Datetime.regex.match(value)  # type: ignore
        if match:

            kwargs: Dict[str, Union[int, timezone]] = {
                k: int(v) for k, v in match.groupdict().items()
            }
            return datetime(tzinfo=timezone.utc, **kwargs)  # type: ignore

        return datetime_parse.parse_datetime(value)
