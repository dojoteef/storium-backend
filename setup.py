"""
Setup script for managing individual generation models for Storium's writing suggestions
web service woolgatherer.
"""

from setuptools import setup, find_packages


EXTRAS_REQUIRE = {}
EXTRAS_REQUIRE["redis"] = ["aioredis==1.3.1"]


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
    scripts=["scripts/figment", "scripts/docker-volume"],
    install_requires=[
        "aiocache==0.11.1",
        "pydantic==1.1.1",
        "fastapi==0.45.0",
        "uvicorn==0.10.3",
        "async-generator==1.10;python_version<'3.7'",
        "async-exit-stack==1.0.1;python_version<'3.7'",
    ],
    extras_require=EXTRAS_REQUIRE,
)
