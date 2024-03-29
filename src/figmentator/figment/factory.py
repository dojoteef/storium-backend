"""
A factory that creates concrete Figmentator instances and also acts as a registry for
getting the registered Figmentators.
"""
import os
import subprocess
from asyncio import Lock, get_event_loop
from typing import Any, Dict, List, Optional, Type

from pkg_resources import (Distribution, EntryPoint, Environment, Requirement,
                           find_distributions, parse_requirements, working_set)
from pydantic import BaseModel, BaseSettings, Field, validator
from setuptools import setup

from figmentator.figment.base import Figmentator
from figmentator.models.suggestion import SuggestionType
from figmentator.utils import shadow_argv


class FigmentatorSettings(BaseModel):
    """ Defines the settings for an individual Figmentator """

    cls: EntryPoint = Field(
        EntryPoint.parse("model=figmentator.examples.simple:SimpleFigmentator"),
        description="""
The package path to a model class in the form of an EntryPoint as specified by:
https://setuptools.readthedocs.io/en/latest/pkg_resources.html#creating-and-parsing
        """,
    )
    requires: List[Requirement] = Field(
        [],
        description="""
A list of required packaged as specified by:
https://setuptools.readthedocs.io/en/latest/pkg_resources.html#requirements-parsing
""",
    )
    properties: Optional[Dict[str, Any]] = Field(
        ...,
        description="""
This is a dict of properties that will be passed to your model's startup method. It can
include anything you need to initalize your model, e.g. the path to your model
parameters.
""",
    )

    @classmethod
    def _parse_cls(cls: Type["FigmentatorSettings"], value: Any) -> EntryPoint:
        """ Parse and validate the model class in EntryPoint format """
        if isinstance(value, str):
            value = EntryPoint.parse(value)
        elif not isinstance(value, EntryPoint):
            raise ValueError(f"Must be str or EntryPoint, not {type(value)}!")

        return value

    @classmethod
    def _parse_requires(
        cls: Type["FigmentatorSettings"], value: Any
    ) -> List[Requirement]:
        """ Parse and validate a list of Requirements """
        if not isinstance(value, list):
            raise ValueError(f"Must be a list, not {type(value)}!")

        return list(parse_requirements([str(v) for v in value]))

    # In order to appease mypy, I cannot simply use validator as a decorator. Otherwise
    # it thinks the method is a normal method that expects self, because validator
    # internally wraps it in a classmethod (which mypy apparently doesn't handle well).
    parse_cls = validator("cls", pre=True)(getattr(_parse_cls, "__func__"))
    parse_requires = validator("requires", pre=True, whole=True)(
        getattr(_parse_requires, "__func__")
    )

    class Config:
        """
        Need to set allow_arbitrary_types so pydantic doesn't complain about EntryPoint
        """

        arbitrary_types_allowed = True


class FigmentatorFactorySettings(BaseSettings):
    """ Defines the settings for the figmentator factory """

    multiversion: bool = Field(
        False,
        description="Whether to support multi-version python packages (uses easy_install)",
    )

    install_dir: str = Field(
        os.path.abspath(os.curdir),
        description="""
The directory to install any additional requirements into. This directoy MUST be in
sys.path or PYTHONPATH and must be writable by the user during execution of this app.
        """,
    )

    figmentators: Dict[SuggestionType, FigmentatorSettings] = Field(
        {SuggestionType.scene_entry: FigmentatorSettings()},
        description="""
A mapping of SuggestionType to settings for the associated Figmentator.
        """,
    )

    class Config:
        """ Specify metadata for these settings """

        env_prefix = "FIG_FACTORY_"


class FigmentatorFactory:
    """
    This class acts as a factory and a registry for Figmentators. You simply register a
    Figmentator to the factory, then ask for the Figmentator by SuggestionType. It only
    allows a single unique Figmentator per SuggestionType. It is also responsible for
    calling the startup/shutdown of each Figmentator.
    """

    def __init__(self):
        """ Create the factory """
        self.lock = Lock()
        self.env = Environment()
        self.loop = get_event_loop()
        self.figmentators_by_type = {}
        self.settings = FigmentatorFactorySettings()

    @property
    def figmentators(self):
        """ Return a list of all the figmentators """
        return list(self.figmentators_by_type.values())

    async def get(self, suggestion_type: SuggestionType) -> Figmentator:
        """
        Get a Figmentator by it's type. If there are valid settings for a
        Figmentator it will instatiate it (and install any needed requirements.
        """
        async with self.lock:
            if suggestion_type not in self.figmentators_by_type:
                if (
                    suggestion_type
                    not in self.settings.figmentators  # pylint:disable=unsupported-membership-test
                ):
                    raise ValueError(
                        f"Cannot create Figmentator of type {suggestion_type}"
                    )

                settings = self.settings.figmentators[  # pylint:disable=unsubscriptable-object
                    suggestion_type
                ]

                requirements = await self.loop.run_in_executor(
                    None,  # use default executor
                    working_set.resolve,  # resolve model requirements
                    settings.requires,  # list of requirements
                    self.env,  # environment
                    self.installer,  # installer for missing requirements
                    True,  # whether to replace conflicting requirements
                )

                for requirement in requirements:
                    working_set.add(requirement, replace=True)

                try:
                    model_cls = settings.cls.resolve()
                except ImportError as e:
                    raise e

                if not issubclass(model_cls, Figmentator):
                    raise ValueError("model_cls must be a subclass of Figmentator")

                figmentator = model_cls(suggestion_type)
                await self.loop.run_in_executor(
                    None, figmentator.startup, settings.properties
                )
                self.figmentators_by_type[suggestion_type] = figmentator

            return self.figmentators_by_type[suggestion_type]

    async def remove(self, figmentator: Figmentator):
        """
        Get a Figmentator by it's type. If there are valid settings for a
        Figmentator it will instatiate it (and install any needed requirements.
        """
        async with self.lock:
            suggestion_type = figmentator.suggestion_type
            assert suggestion_type in self.figmentators_by_type

            figmentator.shutdown()
            del self.figmentators_by_type[suggestion_type]

    def get_distribution(self, requirement: Requirement) -> Optional[Distribution]:
        """
        Get a distribution that statisfies the requirement. Use
        find_distributions so it looks on disk, thus can find newly installed
        pacakges. """
        for distribution in find_distributions(self.settings.install_dir):
            if distribution in requirement:
                return distribution

        return None

    def installer(self, requirement: Requirement) -> Optional[Distribution]:
        """ A method for using easy_install or pip to install a requirement """
        for dist in self.env[requirement.key]:
            if dist not in requirement:
                self.env.remove(dist)

        if self.settings.multiversion:
            # Use easy_install despite being deprecated as it is the only way to
            # have multi-version package support. See:
            # https://packaging.python.org/guides/multi-version-installs/
            # https://packaging.python.org/discussions/pip-vs-easy-install/
            with shadow_argv(
                [
                    "",
                    "easy_install",
                    "--install-dir",
                    self.settings.install_dir,
                    str(requirement),
                ]
            ):
                setup()
        else:
            # Use pip instead since we don't need multiversion support and pip is vastly
            # easier to use (and supports wheels)
            subprocess.run(
                [
                    "pip3",
                    "install",
                    "--target",
                    self.settings.install_dir,
                    str(requirement),
                ]
            )

        distribution = self.get_distribution(requirement)
        if distribution:
            working_set.add(distribution, replace=True)

        return distribution


figmentator_factory = FigmentatorFactory()


async def get_figmentator(suggestion_type: SuggestionType) -> Figmentator:
    """
    A method that acquires a Figmentator asynchronously, since it may require
    instantiating the Figmentator (and possibly installing requirements)
    """
    return await figmentator_factory.get(suggestion_type)


async def remove_figmentator(figmentator: Figmentator):
    """
    A method that acquires a Figmentator asynchronously, since it may require
    instantiating the Figmentator (and possibly installing requirements)
    """
    await figmentator_factory.remove(figmentator)
