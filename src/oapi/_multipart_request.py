"""
This module extends the functionality of `urllib.request.Request` to support
multipart requests, to support passing instances of sob models to the `data`
parameter/property for `urllib.request.Request`, and to support casting
requests as `str` or `bytes` (typically for debugging purposes and/or to aid in
producing non-language-specific API documentation).
"""

from __future__ import annotations

import collections
import random
import string
from collections.abc import (
    ItemsView,
    Iterable,
    Iterator,
    Mapping,
    Reversible,
    Sequence,
)
from urllib.request import Request as _Request  # type: ignore

import sob


class Headers:
    """
    A dictionary of headers for a `Request`, `Part`, or `MultipartRequest`
    instance.
    """

    def __init__(
        self,
        items: Mapping[str, str] | Iterable[tuple[str, str]],
        request: Data,
    ) -> None:
        self._dict: dict[str, str] = {}
        if not isinstance(request, Data):
            raise TypeError(request)
        self.request: Data = request
        self._init_items(items)

    def _init_items(
        self,
        data: Mapping[str, str] | Iterable[tuple[str, str]],
    ) -> None:
        if data is not None:
            items: Iterable[tuple[str, str]]
            if isinstance(
                data, (dict, collections.OrderedDict, sob.abc.Dictionary)
            ) or (isinstance(data, Mapping) and isinstance(data, Reversible)):
                items = data.items()
            elif isinstance(data, Mapping):
                items = sorted(data.items(), key=lambda item: item[0])
            else:
                items = data
            key: str
            value: str
            for key, value in items:
                self.__setitem__(key, value)

    def _reset_part(self) -> None:
        if isinstance(self.request, Part):
            del self.request.boundary
            self.request.clear_bytes()

    def pop(  # type: ignore
        self, key: str, default: str | None = None
    ) -> str | None:
        key = key.capitalize()
        self._reset_part()
        return self._dict.pop(key, default)

    def popitem(self) -> tuple[str, str]:
        self._reset_part()
        return self._dict.popitem()

    def setdefault(self, key: str, default: str = "") -> str:
        key = key.capitalize()
        self._reset_part()
        return self._dict.setdefault(key, default)

    def update(  # type: ignore
        self,
        *args: Mapping[str, str]
        | sob.abc.Dictionary
        | Iterable[tuple[str, str]],
        **kwargs: str,
    ) -> None:
        capitalized_dict: dict[str, str] = {}
        key: str
        value: str
        for key, value in dict(*args, **kwargs).items():
            capitalized_dict[key.capitalize()] = value
        self._reset_part()
        self._dict.update(capitalized_dict)

    def __getitem__(self, key: str) -> str:
        key = key.capitalize()
        value: str | None
        if key == "Content-length":
            value = str(self._get_content_length())
        elif key == "Content-type":
            value = self._get_content_type()
        else:
            value = self._dict.__getitem__(key)
        if not isinstance(value, str):
            raise TypeError(value)
        return value

    def get(
        self,
        key: str,
        default: str | sob.Undefined = sob.UNDEFINED,
    ) -> str:
        try:
            return self.__getitem__(key)
        except KeyError:
            if isinstance(default, sob.abc.Undefined):
                raise
            return default

    def __delitem__(self, key: str) -> None:
        self._reset_part()
        self._dict.__delitem__(key.capitalize())

    def __setitem__(self, key: str, value: str) -> None:
        key = key.capitalize()
        if key != "Content-length":
            self._reset_part()
            self._dict.__setitem__(key, value)

    def _get_content_length(self) -> int:
        return len(self.request.data or b"")

    def _get_boundary(self) -> str:
        boundary: str = ""
        if isinstance(self.request, Part):
            boundary = str(self.request.boundary, encoding="utf-8")
        return boundary

    def _get_content_type(self) -> str:
        if isinstance(self.request, Part) and self.request.parts:
            return f"multipart/form-data; boundary={self._get_boundary()}"
        return self._dict.__getitem__("Content-type")

    def __len__(self) -> int:
        return self._dict.__len__()

    def __iter__(self) -> Iterator[str]:
        keys: set[str] = set()
        key: str
        for key in self._dict.__iter__():
            keys.add(key)
            yield key
        if (
            (type(self.request) is not Part)
            # *Always* include "Content-length"
            and ("Content-length" not in keys)
        ):
            yield "Content-length"
        if (
            isinstance(self.request, Part)
            and self.request.parts
            # Always include "Content-type" for multi-part requests
            and ("Content-type" not in keys)
        ):
            yield "Content-type"

    def __contains__(self, key: str) -> bool:  # type: ignore
        return self._dict.__contains__(key.capitalize())

    def items(self) -> ItemsView[str, str]:  # type: ignore
        for key in self.__iter__():
            yield key, self[key]

    def keys(self) -> Iterator[str]:  # type: ignore
        key: str
        yield from self.__iter__()

    def values(self) -> Iterator[str]:  # type: ignore
        key: str
        for key in self.__iter__():
            yield self[key]

    def copy(self) -> Headers:
        return self.__class__(self._dict.items(), request=self.request)

    def __copy__(self) -> Headers:
        return self.copy()


class Data:
    """
    One of a multipart request's parts.
    """

    def __init__(
        self,
        data: sob.abc.MarshallableTypes = None,
        headers: Headers | Mapping[str, str] | None = None,
    ) -> None:
        """
        Parameters:

            data:
            headers: A dictionary of headers (for this part of
                the request body, not the main request). This should (almost)
                always include values for "Content-Disposition" and
                "Content-Type".
        """
        self._bytes: bytes | None = None
        self._headers: Headers | None = None
        self._data: bytes | None = None
        self.headers = headers  # type: ignore
        self.data = data  # type: ignore

    @property  # type: ignore
    def headers(self) -> Headers | None:
        return self._headers

    @headers.setter
    def headers(self, headers: Mapping[str, str] | Headers | None) -> None:
        self._bytes = None
        if headers is None:
            headers = Headers({}, self)
        elif isinstance(headers, Headers):
            headers.request = self
        else:
            headers = Headers(headers, self)
        self._headers = headers

    @property  # type: ignore
    def data(self) -> bytes | None:
        return self._data

    @data.setter
    def data(
        self,
        data: sob.abc.MarshallableTypes,
    ) -> None:
        self._bytes = None
        if data is not None:
            if (data is not None) and not (isinstance(data, (str, bytes))):
                data = sob.serialize(data)
            if isinstance(data, str):
                data = bytes(data, encoding="utf-8")
        self._data = data

    @data.deleter
    def data(self) -> None:
        self.data = None

    def clear_bytes(self) -> None:
        self._bytes = None

    def __bytes__(self) -> bytes:
        if self._bytes is None:
            lines: list[bytes] = []
            if self.headers is not None:
                key: str
                value: str
                for key, value in self.headers.items():
                    lines.append(bytes(f"{key}: {value}", encoding="utf-8"))
            lines.append(b"")
            if self.data is not None:
                lines.append(self.data)
            self._bytes = b"\r\n".join(lines) + b"\r\n"
        return self._bytes

    def __str__(self) -> str:
        return (
            repr(bytes(self))[2:-1]
            .replace("\\r\\n", "\r\n")
            .replace("\\n", "\n")
        )


class Part(Data):
    def __init__(
        self,
        data: sob.abc.MarshallableTypes = None,
        headers: Headers | Mapping[str, str] | None = None,
        parts: Sequence[Part] | Parts | None = None,
    ):
        """
        Parameters:

            data:
            headers: A dictionary of headers (for this part of
                the request body, not the main request). This should (almost)
                always include values for "Content-Disposition" and
                "Content-Type".
        """
        self._boundary: bytes | None = None
        self._parts: Parts | None = None
        self.parts = parts  # type: ignore
        Data.__init__(self, data=data, headers=headers)

    @property  # type: ignore
    def boundary(self) -> bytes:
        """
        Calculates a boundary which is not contained in any of the request
        parts.
        """
        if self._boundary is None:
            part: Part
            data: bytes = b"\r\n".join(
                [self._data or b""]
                + [bytes(part) for part in (self.parts or ())]
            )
            boundary: bytes = b"".join(
                bytes(
                    random.choice(  # noqa: S311
                        string.digits + string.ascii_letters
                    ),
                    encoding="utf-8",
                )
                for _index in range(16)
            )
            while boundary in data:
                boundary += bytes(
                    random.choice(  # noqa: S311
                        string.digits + string.ascii_letters
                    ),
                    encoding="utf-8",
                )
            self._boundary = boundary
        return self._boundary

    @boundary.deleter
    def boundary(self) -> None:
        self._boundary = None

    @property  # type: ignore
    def data(self) -> bytes | None:
        data: bytes | None
        if self.parts:
            part: Part
            data = b"%s\r\n--%s--" % (
                (b"\r\n--%s\r\n" % self.boundary).join(
                    [self._data or b""]
                    + [bytes(part).rstrip() for part in self.parts]
                ),
                self.boundary,
            )
        else:
            data = self._data
        return data

    @data.setter
    def data(
        self,
        data: sob.abc.MarshallableTypes,
    ) -> None:
        Data.data.__set__(self, data)  # type: ignore

    @property  # type: ignore
    def parts(self) -> Parts | None:
        return self._parts

    @parts.setter
    def parts(self, parts: Parts | Sequence[Part] | None) -> None:
        if parts is None:
            parts = Parts([], request=self)
        elif isinstance(parts, Parts):
            parts.request = self
        else:
            parts = Parts(parts, request=self)
        self._boundary = None
        self._parts = parts


class Parts:
    def __init__(self, items: Sequence[Part], request: Part) -> None:
        self._list: list[Part] = list(items)
        self.request = request

    def append(self, item: Part) -> None:
        self.request._boundary = None  # noqa: SLF001
        self.request._bytes = None  # noqa: SLF001
        self._list.append(item)

    def clear(self) -> None:
        self.request._boundary = None  # noqa: SLF001
        self.request._bytes = None  # noqa: SLF001
        self._list.clear()

    def extend(self, items: Iterable[Part]) -> None:
        self.request._boundary = None  # noqa: SLF001
        self.request._bytes = None  # noqa: SLF001
        self._list.extend(items)

    def reverse(self) -> None:
        self.request._boundary = None  # noqa: SLF001
        self.request._bytes = None  # noqa: SLF001
        self._list.reverse()

    def __delitem__(self, key: int) -> None:
        self.request._boundary = None  # noqa: SLF001
        self.request._bytes = None  # noqa: SLF001
        self._list.__delitem__(key)

    def __setitem__(self, key: int, value: Part) -> None:
        self.request._boundary = None  # noqa: SLF001
        self.request._bytes = None  # noqa: SLF001
        self._list.__setitem__(key, value)

    def __iter__(self) -> Iterator[Part]:
        return iter(self._list)

    def __len__(self) -> int:
        return self._list.__len__()

    def __bool__(self) -> bool:
        return bool(self._list)


class Request(Data, _Request):  # type: ignore
    """
    A sub-class of `urllib.request.Request` which accommodates additional data
    types, and serializes `data` in accordance with what is indicated by the
    request's "Content-Type" header.
    """

    def __init__(
        self,
        url: str,
        data: sob.abc.MarshallableTypes = None,
        headers: Mapping[str, str] | Headers | None = None,
        origin_req_host: str | None = None,
        unverifiable: bool = False,  # noqa: FBT001 FBT002
        method: str | None = None,
    ) -> None:
        self._bytes: bytes | None = None
        self._headers = None
        self._data = None
        self.headers = headers  # type: ignore
        _Request.__init__(
            self,
            url,
            data=data,  # type: ignore
            headers=self.headers,  # type: ignore
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method,
        )


class MultipartRequest(Part, Request):  # type: ignore
    """
    A sub-class of `Request` which adds a property (and initialization
    parameter) to hold the `parts` of a multipart request.

    https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html
    """

    def __init__(
        self,
        url: str,
        data: sob.abc.MarshallableTypes = None,
        headers: Headers | Mapping[str, str] | None = None,
        origin_req_host: str | None = None,
        unverifiable: bool = False,  # noqa: FBT001 FBT002
        method: str | None = None,
        parts: Sequence[Part] | Parts | None = None,
    ) -> None:
        Part.__init__(self, data=data, headers=headers, parts=parts)
        Request.__init__(
            self,
            url,
            data=data,
            headers=headers,
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method,
        )
