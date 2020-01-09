"""
Main entry point for figmentator. This is where we setup the app.
"""
import os
import urllib
from typing import Any, Dict

import aiocache
from fastapi import FastAPI

from figmentator.routers import story, figment
from figmentator.utils.settings import Settings
from figmentator.figment.scheduler import Figmentators


app = FastAPI(debug=bool(int(os.environ.get("DEBUG", 0))))

app.include_router(story.router, prefix="/story", tags=["story"])
app.include_router(figment.router, prefix="/figment", tags=["figment"])


@app.on_event("startup")
def initialize_caches():
    """ Initialize the cache """
    url = urllib.parse.urlparse(Settings.cache_url)
    cache_config: Dict[str, Any] = dict(urllib.parse.parse_qsl(url.query))
    cache_class = aiocache.Cache.get_scheme_class(url.scheme)

    if url.path:
        cache_config.update(cache_class.parse_uri_path(url.path))

    if url.hostname:
        cache_config["endpoint"] = url.hostname

    if url.port:
        cache_config["port"] = str(url.port)

    if url.password:
        cache_config["password"] = url.password

    if cache_class == aiocache.Cache.REDIS:
        cache_config["cache"] = "aiocache.RedisCache"
        cache_config["serializer"] = {"class": "aiocache.serializers.PickleSerializer"}
    elif cache_class == aiocache.Cache.MEMORY:
        cache_config["cache"] = "aiocache.SimpleMemoryCache"
        cache_config["serializer"] = {"class": "aiocache.serializers.NullSerializer"}

    aiocache.caches.set_config({"default": cache_config})


@app.on_event("startup")
async def initialize_figmentators():
    """ Initialize the configured figmentators """
    await Figmentators.startup()


@app.on_event("shutdown")
async def shutdown_figmentators():
    """ Shutdown the configured figmentators """
    await Figmentators.shutdown()
