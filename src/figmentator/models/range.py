"""
Defines the structure for ranges
"""
import string
import unicodedata
from enum import auto
from functools import partial
from typing import Any, List, Optional, Type, Union

import regex as re
from pydantic import BaseModel, Field, ValidationError
from pydantic.error_wrappers import ErrorWrapper

from figmentator.models.utils import AutoNamedEnum


class RangeUnits(AutoNamedEnum):
    """
    When specifying the range of a suggestion, what units are we specifying the range
    in:

    - **chars**: specify the range in characters
    - **words**: specify the range in words
    - **tokens**: specify the range in tokens
    - **sentences**: specify the range in sentences
    """

    chars = auto()
    words = auto()
    tokens = auto()
    sentences = auto()

    def chunk(self, text: str, keep_fragments: bool = True) -> Union[str, List[str]]:
        """
        Split text into range units
        """
        # mypy doesn't realize these are all callable, rather since the values
        # are heterogeneous it thinks the values are random objects, which may
        # or may not be callable
        return {  # type: ignore
            type(self).chars: NFC,
            type(self).words: tokenize,
            type(self).tokens: str.split,
            type(self).sentences: partial(
                split_sentences, keep_fragments=keep_fragments
            ),
        }[self](text)


MARKDOWN_SYMBOLS = r'\*_~"'
START_QUOTATION_MARKS = r'\'"“`‘'
END_QUOTATION_MARKS = r'\'"”´’‚,„'
SENTENCE_END_MARKS = rf"[{MARKDOWN_SYMBOLS}{END_QUOTATION_MARKS}]*"
SENTENCE_START_MARKS = rf"[{MARKDOWN_SYMBOLS}{START_QUOTATION_MARKS}]*"
SUBRANGE_REGEX_STR = r"((?<!=),)?(?P<start>\d+|(?!-(,|$)))-(?P<end>(\d+)?)"
RANGE_REGEX_STR = (
    f"(?P<unit>({'|'.join(RangeUnits)}))=(?P<ranges>({SUBRANGE_REGEX_STR})+)"
)

SUBRANGE_REGEX = regex = re.compile(SUBRANGE_REGEX_STR)
RANGE_REGEX = regex = re.compile(RANGE_REGEX_STR)
TOKENIZER_REGEX = re.compile(r"\w+|[^\w\s]+")
SENT_REGEX = re.compile(
    rf"(?<=\w\w[{string.punctuation}]*[.?!]+"
    rf"(?:{SENTENCE_END_MARKS})?)(?:\s|\r\n)+"
    fr"(?=(?:{SENTENCE_START_MARKS})?[A-Z])"
)


class Subrange(BaseModel):
    """ A portion of a range, which may have a start and/or an end """

    start: Optional[int]
    end: Optional[int]

    def get_slice(self) -> slice:
        """ Convert to a slice """
        return slice(
            self.start,
            self.end if self.start is None or self.end is None else self.end + 1,
        )


class Range(BaseModel):
    """ Definition of a range as defined in https://tools.ietf.org/html/rfc7233
    See also: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range

    Note, the start and end of a range are inclusive. For example, to specify you want
    only the first word, an appropriate Range header would look like:

        Range: words=0-0
    """

    unit: RangeUnits = Field(RangeUnits.words, description=RangeUnits.__doc__)
    ranges: List[Subrange] = Field(
        [],
        description="""
A list of subranges as specified in RFC7233 (https://tools.ietf.org/html/rfc7233)
        """,
    )

    @property
    def slices(self):
        """
        Get all the slices in the range
        """
        return [r.get_slice() for r in self.ranges]

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

    def __str__(self):
        """ Override the string method to return a range as specified by our regexes """
        ranges = ",".join(
            [
                ("" if r.start is None else str(r.start))
                + "-"
                + ("" if r.end is None else str(r.end))
                for r in self.ranges  # pylint:disable=not-an-iterable
            ]
        )
        return f"{self.unit.value}={ranges}"  # pylint:disable=no-member

    def is_finite(self) -> bool:
        """ A method to determine if the range is a finite range """
        if len(self.ranges) != 1:
            return False

        # pylint:disable=unsubscriptable-object
        return self.ranges[0].start is not None and self.ranges[0].end is not None
        # pylint:enable=unsubscriptable-object

    def trim(self, text: str) -> str:
        """
        Trim any excess text outside of the defined range
        """
        # This only makes sense when there is a single range
        assert len(self.ranges) == 1

        segment = self.slices[0]
        chunks = self.unit.chunk(text)
        if len(chunks) > segment.stop:
            text = text[: text.rindex(chunks[segment.stop])]

        return text


def tokenize(text: str) -> List[str]:
    """
    Implement a simple tokenizer that seperates continguous word characters and
    punctuation.
    """
    return TOKENIZER_REGEX.findall(text)


def NFC(text) -> str:
    """
    Normalize the unicode string into NFC form

    Read more about that here:
    https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize
    """
    return unicodedata.normalize("NFC", text)


def split_sentences(text: str, keep_fragments=True) -> List[str]:
    """
    Split a text string into a number of sentences using a simple regex
    """
    sentences = SENT_REGEX.split(text)
    if not keep_fragments and sentences:
        # Rather than have two separate regex expressions, just use the regex
        # meant for splitting at sentence boundaries and add a token that would
        # start a new sentence if the last sentence is not a fragment
        last_sentence = sentences[-1]
        chunks = len(SENT_REGEX.split(last_sentence + " A"))
        if chunks == 1:
            # This indicates the last sentence is actually a fragment, so
            # exclude it
            return sentences[:-1]

    return sentences


def compute_next_range(
    text: str, units: RangeUnits, max_length: int, chunk_size: int
) -> Range:
    """ Compute the range of the passed in text """
    assert chunk_size > 0
    ranges: List[Subrange] = []
    range_dict = {"unit": units, "ranges": ranges}

    text_len = len(units.chunk(text, keep_fragments=False))
    remaining = max_length - text_len
    if remaining > 0:
        size = min(remaining, chunk_size)
        start = text_len if size == remaining else None
        end = start + remaining - 1 if start is not None else size

        ranges.append(Subrange(start=start, end=end))
    elif not remaining:
        ranges.append(Subrange(start=text_len, end=text_len))

    return Range(**range_dict)


def compute_full_range(units: RangeUnits, max_length: int, chunk_size: int) -> Range:
    """ Compute the full range """
    assert chunk_size > 0
    return Range(unit=units, ranges=[Subrange(start=0, end=max_length - 1)])
