"""
Data models based on:
https://storium.com/help/export/json/0.9.2

Empirically discovered nullable fields in the Storium export format:

"act_number"
"alt_text"
"attribution_text"
"attribution_url"
"author_character_seq_id"
"author_user_pid"
"card"
"challenge_completion_polarity"
"challenge_points"
"challenge_points_polarities"
"chapter_number"
"character_seq_id"
"completed_at"
"curscene_last_move_date"
"custom_story_size"
"description"
"failure_stakes"
"game_pid"
"has_ugc"
"host_rules"
"invitee_info"
"is_edited"
"license_limits"
"name"
"narrator_intel"
"new_card"
"place_card"
"player_reference"
"redacted"
"revision_request_reason"
"revisions_requested"
"story_size"
"success_stakes"
"suggested_challenge_points"
"suggested_failure_stakes"
"suggested_stack_size"
"suggested_strength_card_id"
"suggested_success_stakes"
"suggested_weakness_card_id"
"target_challenge_card"
"to_character_seq_id"
"triggers"
"url"
"version"
"via_wild_exchanged_for"
"was_auto_approved"
"world_card_id"

The command used to find these:
> find data/ -iname '*.json' -print0 | xargs -0 -n 1 -P 0 jq '[recurse | if type ==
"object" then to_entries[] | select(.value == null) | .key else "_" end] | unique | .[]'
| sort | uniq)

"""
import re
from enum import auto
from typing import List, Union, Optional

from pydantic import BaseModel, AnyHttpUrl, ConstrainedStr

from figmentator.models.utils import AutoNamedEnum, Field, Datetime, EmptyStr


class UnchangedStr(ConstrainedStr):
    """
    Workaround for mypy rather than use constr, see:

    https://github.com/samuelcolvin/pydantic/issues/239#issuecomment-409644889
    """

    regex = re.compile(r"unchanged")


class RoleStr(ConstrainedStr):
    """
    Workaround for mypy rather than use constr, see:

    https://github.com/samuelcolvin/pydantic/issues/239#issuecomment-409644889
    """

    regex = re.compile(r"narrator|character:\d+")


class CardId(str):
    """ A unique identifier for a card, unique within a game but not across games. """


class UserPid(str):
    """ A unique identifier for a user, unique across all games. """


class CharacterSeqId(str):
    """ A unique identifier for a character, unique within a game but not across
    games."""


class SceneEntrySeqId(str):
    """ A unique identifier for an entry in a scene, unique within a game but not across
    games. """


class EntryFormatString(AutoNamedEnum):
    """
    Enum describing the types of entries:

    - **establishment**: a scene establishment (narrator)
    - **addition**: a scene continuation (narrator)
    - **conclusion**: a scene conclusion (narrator)
    - **move**: a character's move
    - **refresh**: a character refreshed the cards in their hand. in thise case the
      entry is just a container for a 'refreshCards' autotext. use the HandContext
      content, comparing the pre and post values, to see what cards the player chose
      that were added to the character's hand.
    - **subplot**: a character chose a subplot. in this case the entry is just a
      container for a 'newSublot' autotext. the HandContext pre/post delta will contain
      a new subplot card.
    """

    establishment = auto()
    addition = auto()
    conclusion = auto()
    move = auto()
    refresh = auto()
    subplot = auto()


class CardNamespace(AutoNamedEnum):
    """ Enumeration of card types """

    chartype = auto()
    goal = auto()
    person = auto()
    place = auto()
    thing = auto()
    strength = auto()
    weakness = auto()
    obstacle = auto()
    subplot = auto()


class CardPrettyNamespace(AutoNamedEnum):
    """ The name of the CardNamespace displayed on the UI """

    Nature = auto()
    Goal = auto()
    Character = auto()
    Place = auto()
    Asset = auto()
    Strength = auto()
    Weakness = auto()
    Obstacle = auto()
    Subplot = auto()


class WildCardExchangeType(AutoNamedEnum):
    """
    Playing a wild card is two steps in the abstract: exchanging the wild for a new card
    (either writing it on the spot, or picking an existing one) and then playing that
    defined card on the challenge. If they wrote a new card the value is 'new', if they
    chose an existing card it is 'existing'.
    """

    new = auto()
    existing = auto()


class AutotextTypeString(AutoNamedEnum):
    """ The autotext type is one of:

    - **pickupCard**: the character picked up a card
    - **giveCard**: the character gave a card to another character
    - **refreshCards**: the character refreshed their cards. note that in this case, the
      actual card content is not included since the UI does not need that info.
    - **completedRewardable**: the character played out their subplot and is enqueued
      for a reward on the next scene
    - **completedRewardableReward**: the character received a wild card reward for
      playing out their subplot
    - **newSubplot**: the character chose a new subplot
    - **rewriteAsset**: the character rewrote an asset card (loses 1 in the stack as the
      cost of rewriting)
    - **discardCard**: the character discarded a card """

    pickupCard = auto()
    giveCard = auto()
    refreshCards = auto()
    completedRewardable = auto()
    completedRewardableReward = auto()
    newSubplot = auto()
    rewriteAsset = auto()
    discardCard = auto()


class Image(BaseModel):
    """
    Definition of an image in [Storium's export
    format](https://storium.com/help/export/json/0.9.2).
    """

    url: Optional[AnyHttpUrl] = Field(
        None,
        description="""Url to image asset, usually to a default stock image unless the
        user uploaded/chose a different one. Can be null when no image present.""",
    )
    attribution_url: Optional[Union[AnyHttpUrl, EmptyStr]] = Field(
        None, description="Url to an attributed source."
    )
    attribution_text: Optional[Union[str, EmptyStr]] = Field(
        None, description="Description of an attributed source."
    )
    alt_text: Optional[Union[str, EmptyStr]] = Field(
        None, description="Alt text for the image."
    )


class HandCardStack(BaseModel):
    """ A stack of cards in a player's hand. """

    card_id: CardId = Field(
        ...,
        description="""A unique identifier for a card, unique within a game but not
        across games.""",
    )

    stack_size: int = Field(
        ...,
        description="""Captures the count of the card in the hard and will always be 1
        or more.""",
    )


class HandContext(BaseModel):
    """ The pre/post state of the entry role's hand. """

    pre: Union[List[HandCardStack], UnchangedStr] = Field(
        ...,
        description="""The cards this role had in their hand at the outset of their
        entry, before the entry caused any changes to it. If a string it will the value
        'unchanged', which is an optimization for data payload size. It means that the
        state of the hand has not changed since the role's prior entry in this scene.
        Because this optimization is bounded by the scene, note the first entry in any
        scene for a particular role will always have this value set, even though it will
        often (but not always) be unchanged from the final state at the end of the prior
        scene.""",
    )

    post: Union[List[HandCardStack], UnchangedStr] = Field(
        ...,
        description="""Same as 'pre' but the state of the role's hand after publishing
        the entry, including the changes caused by the card mechanics in the entry.
        'unchanged' if the entry did not change the character's cards. Note that the
        narrator role's hand is never actually affected by entries. For example, when a
        narrator creates a new card to play to use on a new scene, from a gameplay
        mechanics perspective that new card becomes available retroactively from the
        beginning of the game. So, the narrator role will have the the 'pre' value set
        on the scene establishment handContext, and then the rest of the pre/post values
        for the scene will be 'unchanged'.""",
    )


class Card(BaseModel):
    """ An object representing a card in Storium. """

    card_id: CardId = Field(
        ...,
        description="""A unique identifier for a card, unique within a game but not
        across games.""",
    )

    name: Optional[str] = Field(None, description="The name of the card.")

    namespace: CardNamespace = Field(..., description=CardNamespace.__doc__)

    pretty_namespace: CardPrettyNamespace = Field(
        ..., description=CardPrettyNamespace.__doc__
    )

    image: Optional[Image] = Field(
        None, description="A user-added image for the entry if any."
    )

    polarity: int = Field(
        ...,
        description="""-1 for weakness cards, 1 for strength cards, 0 for all other
        cards.""",
    )

    description: Optional[str] = Field(
        None, description="Markdown string descrbing the card"
    )

    author_user_pid: Optional[UserPid] = Field(
        None,
        description=f"""Not necessarily someone in the game, could be the world author
        for world cards. {UserPid.__doc__}""",
    )

    author_character_seq_id: Optional[CharacterSeqId] = Field(
        None,
        description=f"""For cards created in-game by characters, like during character
        creation or wild card definitions, or asset rewriting, etc etc, this will
        contain the character seq id of the character who created it.
        {CharacterSeqId.__doc__}""",
    )

    is_deleted: bool = Field(
        ...,
        description="""true if the narrator/host deletes the card from the game. The
        object still persists because existing content may still reference it, deletion
        just prevents the card from being visible / an option for future choices.""",
    )

    is_wild: bool = Field(
        ...,
        description="""true for wild cards held in character hands. When a player plays
        a wild card on a move, they write a new card (or pick an existing one) and the
        wild card is removed from their hand, the wild card persists in a dangling state
        but no longer belongs to anyone.""",
    )

    via_wild_exchanged_for: Optional[WildCardExchangeType] = Field(
        None,
        description=f"""This attribute is only populated within the context of
        scenes[].entries[].plays.cards_played_on_challenge[] payloads, and when
        non-null, means the card play on the challenge was the result of the character
        choosing a wild card to play. {WildCardExchangeType.__doc__}""",
    )

    is_edited: Optional[bool] = Field(
        None,
        description="""Set true any time a card is edited. used for cards that are
        cloned from a source world to indicate the card content has been changed from
        the original world card's content.""",
    )

    world_card_id: Optional[CardId] = Field(
        None,
        description="""Cards that are part of worlds have this set to their own id, and
        then game cards that are cloned from world cards inherit this property while
        getting a new primary card id.""",
    )

    redacted: Optional[bool] = Field(
        None,
        description="""True if the author of this card redacted their contributions to
        the game.""",
    )

    stack_size: Optional[int] = Field(
        ...,
        description="""When a card is represented as a stack of cards, e.g. the user has
        more than one of them, or a stack is played for pickup, this is the count of the
        stack. This is a contextual property.""",
    )

    challenge_points: Optional[int] = Field(
        None,
        description="""For challenge cards, the number of associated points (required
        card plays). This is a contextual property.""",
    )

    challenge_points_polarities: Optional[List[int]] = Field(
        None,
        description="""For challenge cards, the polarities of the cards that have been
        played on the challenge. in the ui this is represented as the color of the
        individual pips on the upper right of the card. this is a contextual
        property.""",
    )

    success_stakes: Optional[str] = Field(
        None,
        description="""The narrator's description of what happens if the challenge is
        met with successful outcome. The ui for this field is prepopulated with
        suggested_success_stakes and the user can use it as-is or edit it. This is a
        contextual property.""",
    )

    failure_stakes: Optional[str] = Field(
        None,
        description="""Like success_stakes, but for the failure/setback outcome. this is
        a contextual property.""",
    )

    suggested_stack_size: Optional[int] = Field(
        None,
        description="""The default stack size when initially giving this card or making
        it available for pickup.""",
    )

    suggested_success_stakes: Optional[str] = Field(
        None, description="Default initial value for success_stakes."
    )

    suggested_failure_stakes: Optional[str] = Field(
        None, description="Default initial value for failure_stakes."
    )

    suggested_challenge_points: Optional[int] = Field(
        None, description="Default initial value for challenge_points."
    )

    suggested_strength_card_id: Optional[CardId] = Field(
        None,
        description="""To expedite character creation, for nature cards (chartype),
        during character creation choosing this card will pre-populate the strength card
        with this suggestion, which the user can override.""",
    )

    suggested_weakness_card_id: Optional[CardId] = Field(
        None,
        description="Similar to suggested_strength_card_id but for the weakness card.",
    )


class Autotext(BaseModel):
    """ Annotations of mechanical card changes made as part of the move. """

    type: AutotextTypeString = Field(..., description="The type of this autotext.")

    to_character_seq_id: Optional[CharacterSeqId] = Field(
        None,
        description="""The character who got a card(s), usually this is the player
        themselves, except in 'giveCard' cases.""",
    )

    card: Optional[Card] = Field(
        None, description="The card that was the primary object of the action."
    )

    new_card: Optional[Card] = Field(
        None, description="For asset rewriting, the new asset card."
    )

    automatic: bool = Field(
        ...,
        description="""Was this a user choice to include in the move or did the system
        do it automatically, e.g. it was 'completedRewardable' or
        'completedRewardableReward'.""",
    )

    text: str = Field(
        ..., description="A user-friendly textual rendition of the card mechanic."
    )


class SceneEntry(BaseModel):
    """ A single entry in a scene, i.e. one player's move. """

    user_pid: UserPid = Field(
        ...,
        description=f"""A unique identifier for a user, unique across all games.
        {UserPid.__doc__}""",
    )

    seq_id: SceneEntrySeqId = Field(..., description=SceneEntrySeqId.__doc__)
    format: EntryFormatString = Field(..., description=EntryFormatString.__doc__)

    pretty_format: str = Field(
        ..., description="A user-friendly string for the entry format."
    )

    character_seq_id: Optional[CharacterSeqId] = Field(
        None,
        description=f"""The seq iq of the character playing, or null for narrator moves
        (see role). {CharacterSeqId.__doc__}""",
    )

    role: RoleStr = Field(
        ...,
        description="""Either 'narrator' or 'character:XYZ' where XYZ is the
        character_seq_id.""",
    )

    description: Optional[str] = Field(
        None, description="Markdown string descrbing the body of the entry if any."
    )

    created_at: Datetime = Field(
        ..., description="The time when the scene entry was created."
    )

    image: Optional[Image] = Field(
        None, description="A user-added image for the entry if any."
    )

    hand_context: HandContext = Field(
        ..., description="The pre/post state of the entry role's hand."
    )

    challenge_cards: List[Card] = Field(
        ...,
        description="""For 'establishment' and 'addition' formats, challenge cards the
        narrator adds to the scene.""",
    )

    target_challenge_card: Optional[Card] = Field(
        None,
        description="For 'move' formats, the challenge the user is playing to, if any.",
    )

    cards_played_on_challenge: List[Card] = Field(
        ...,
        description="""For 'move' formats, the card(s) the player played on
        target_challenge_card.""",
    )

    challenge_completion_polarity: Optional[int] = Field(
        None,
        description="""When not null, this property signals that the move completed a
        challenge and that the author is accordingly expected to narrate the outcome,
        the polarity of which is also defined by this value. (-1 for setback, 1 for a
        success, and 0 for an uncertain outcome in which the author is permitted full
        freedom in what happens.)""",
    )

    place_card: Optional[Card] = Field(
        None,
        description="For 'establishment' the place the card for the scene location.",
    )

    cards_for_pickup: List[Card] = Field(
        ...,
        description="""For 'establishment' and 'addition' formats, any card(s) the
        narrator played for pickup by other players.""",
    )

    autotexts: List[Autotext] = Field(
        ...,
        description="""For most move types, annotations of mechanical card changes made
        as part of the move.""",
    )

    revisions_requested: Optional[bool] = Field(
        None, description="If the narrator has requested revisions to the move."
    )

    revision_request_reason: Optional[str] = Field(
        None,
        description="""The narrators reasoning if revisions are requested and the reason
        is made public.""",
    )

    author_is_narrator_when_published: bool = Field(
        ...,
        description="""If the user was also the narrator at the time the entry was
        published.""",
    )

    redacted: Optional[bool] = Field(
        None, description="If the user redacted themselves from the game."
    )
