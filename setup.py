"""
Setup script for managing individual generation models for Storium's writing suggestions
web service woolgatherer.
"""

from setuptools import setup, find_packages


EXTRAS_REQUIRE = {}
EXTRAS_REQUIRE["redis"] = ["aioredis"]


setup(
    name="figmentator",
    version="0.1",
    description="Web service that provides writing suggestions to the Storium platform",
    author="Nader Akoury",
    author_email="nsa@cs.umass.edu",
    url="https://github.com/ngram-lab/figmentator",
    python_requires=">=3.6",
    package_dir={"": "src"},
    packages=find_packages("src"),
    scripts=["scripts/figment"],
    install_requires=[
        "aiocache",
        "fastapi",
        "uvicorn",
        "gunicorn",
        "async-generator;python_version<'3.7'",
        "async-exit-stack;python_version<'3.7'",
    ],
    extras_require=EXTRAS_REQUIRE,
)