import functools
import unittest
from typing import Callable

from oapi.client import Client as _Client


class Client(_Client):
    pass


client_lru_cache: Callable[
    [], Callable[..., Callable[..., Client]]
] = functools.lru_cache  # type: ignore


class TestClient(unittest.TestCase):
    """
    TODO
    """

    @property  # type: ignore
    @client_lru_cache()
    def client(self) -> Client:
        return Client("")


if __name__ == "__main__":
    unittest.main()
