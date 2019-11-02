"""
Main entry point for figmentator. This is where we setup the app.
"""
import os
import urllib

import aiocache
from fastapi import FastAPI

from figmentator.routers import story, figment
from figmentator.utils.settings import Settings


app = FastAPI(debug=bool(int(os.environ.get("DEBUG", 0))))

app.include_router(story.router, prefix="/story", tags=["story"])
app.include_router(figment.router, prefix="/figment", tags=["figment"])


@app.on_event("startup")
def initialize_caches():
    """ Initialize the cache """
    url = urllib.parse.urlparse(Settings.cache_url)
    cache_config = dict(urllib.parse.parse_qsl(url.query))
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
        cache_config["serializer"] = "aiocache.serializers.JsonSerializer"
    elif cache_class == aiocache.Cache.MEMORY:
        cache_config["serializer"] = "aiocache.serializers.NullSerializer"

    aiocache.caches.set_config({"default": cache_config})
