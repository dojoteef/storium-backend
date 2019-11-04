"""
Defines the structure for ranges
"""
import re
from enum import auto
from typing import Any, List, Optional, Type

from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper

from figmentator.models.utils import Field, AutoNamedEnum


class RangeUnits(AutoNamedEnum):
    """
    When specifying the range of a suggestion, what units are we specifying the range
    in:

    - **words**: specify the range in words
    - **tokens**: specify the range in tokens
    """

    words = auto()
    tokens = auto()


SUBRANGE_REGEX_STR = r"((?<!=),)?(?P<start>\d+|(?!-(,|$)))-(?P<end>(\d+)?)"
RANGE_REGEX_STR = (
    f"(?P<unit>({'|'.join(RangeUnits)}))=(?P<ranges>({SUBRANGE_REGEX_STR})+)"
)

SUBRANGE_REGEX = regex = re.compile(SUBRANGE_REGEX_STR)
RANGE_REGEX = regex = re.compile(RANGE_REGEX_STR)


class Subrange(BaseModel):
    """ A portion of a range, which may have a start and/or an end """

    start: Optional[int]
    end: Optional[int]


class Range(BaseModel):
    """ Definition of a range as defined in https://tools.ietf.org/html/rfc7233
    See also: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range

    Note, the start and end of a range are inclusive. For example, to specify you want
    only the first word, an appropriate Range header would look like:

        Range: words=0-0
    """

    unit: RangeUnits = Field(RangeUnits.tokens, description=RangeUnits.__doc__)
    ranges: List[Subrange] = Field(
        ...,
        description="""
A list of subranges as specified in RFC7233 (https://tools.ietf.org/html/rfc7233)
        """,
    )

    @classmethod
    def validate(cls: Type["Range"], value: Any) -> "Range":
        """ Validate the passed in value """
        if isinstance(value, str):
            match = RANGE_REGEX.fullmatch(value)
            if not match:
                raise ValidationError(
                    [
                        ErrorWrapper(
                            ValueError(f"Unable to parse Range!"), loc=cls.__name__
                        )
                    ],
                    cls,
                )

            match_groups = match.groupdict()
            return cls(
                unit=match_groups["unit"],
                ranges=[
                    Subrange(
                        **{k: int(v) if v else None for k, v in m.groupdict().items()}
                    )
                    for m in SUBRANGE_REGEX.finditer(match_groups["ranges"])
                ],
            )

        return super().validate(value)
