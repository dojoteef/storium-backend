"""
Utilities useful for routing
"""
import gzip
import zlib
from typing import Callable

from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response


class CompressedRequest(Request):
    """ Allow the body of the request to be compressed with gzip or zlib """

    async def body(self) -> bytes:
        """ Override the original body method """
        if not hasattr(self, "_body"):
            body = await super().body()
            if "gzip" in self.headers.getlist("Content-Encoding"):
                body = gzip.decompress(body)
            elif "deflate" in self.headers.getlist("Content-Encoding"):
                body = zlib.decompress(body)
            setattr(self, "_body", body)

        return self._body


class CompressibleRoute(APIRoute):
    """ An APIRoute which supports gzip/zlib compressed body """

    def get_route_handler(self) -> Callable:
        """ Override the original get route handler to return out custom handler """
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            """ A route handler that wraps the request in our custom class """
            request = CompressedRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
