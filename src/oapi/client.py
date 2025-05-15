from __future__ import annotations

import builtins
import collections.abc
import copyreg
import decimal
import functools
import gzip
import inspect
import json
import os
import re
import shlex
import ssl
import sys
import threading
import time
import typing
from base64 import b64encode
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime
from http.client import HTTPException, HTTPResponse
from http.cookiejar import CookieJar
from itertools import chain
from logging import Logger, getLogger
from pathlib import Path
from re import Match, Pattern
from ssl import SSLError
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, parse_qs, quote, urlparse, urlunparse
from urllib.parse import urlencode as _urlencode
from urllib.request import (
    HTTPCookieProcessor,
    HTTPSHandler,
    OpenerDirector,
    Request,
    build_opener,
    urlopen,
)
from warnings import warn

import sob

from oapi._multipart_request import MultipartRequest, Part
from oapi._utilities import (
    deprecated,
    get_type_format_property,
    iter_distinct,
)
from oapi.oas.model import (
    Encoding,
    Header,
    MediaType,
    OAuthFlow,
    OpenAPI,
    Operation,
    Parameter,
    PathItem,
    Properties,
    Reference,
    RequestBody,
    Response,
    Schema,
    SecurityScheme,
    SecuritySchemes,
)
from oapi.oas.references import Resolver

_str_lru_cache: typing.Callable[
    [], typing.Callable[..., typing.Callable[..., str]]
] = functools.lru_cache  # type: ignore
_dict_str_model_lru_cache: typing.Callable[
    [],
    typing.Callable[..., typing.Callable[..., dict[str, type[sob.abc.Model]]]],
] = functools.lru_cache  # type: ignore
_lru_cache: typing.Callable[
    [], typing.Callable[..., typing.Callable[..., typing.Any]]
] = functools.lru_cache  # type: ignore

# region Client ABC

URLENCODE_SAFE: str = "|;,/=+"


def urlencode(
    query: collections.abc.Mapping[str, typing.Any]
    | collections.abc.Sequence[tuple[str, typing.Any]],
    doseq: bool = True,  # noqa: FBT001 FBT002
    safe: str = URLENCODE_SAFE,
    encoding: str = "utf-8",
    errors: str = "",
    quote_via: typing.Callable[[str, bytes | str, str, str], str] = quote,
) -> str:
    """
    This function wraps `urllib.parse.urlencode`, but has different default
    argument values. Additionally, when a mapping/dictionary is passed for a
    query value, that dictionary/mapping performs an update to the query
    dictionary.

    Parameters:
        query:
        doseq:
        safe:
        encoding:
        errors:
        quote_via:
    """
    items: list[tuple[str, typing.Any]] = []
    for item in (
        query.items() if isinstance(query, collections.abc.Mapping) else query
    ):
        if isinstance(
            item, (collections.abc.Mapping, sob.abc.Dictionary, sob.abc.Object)
        ):
            # The only dictionaries which should exist
            # for values which have been formatted are
            # intended to be bumped up into the top-level
            items += list(item.items)
        else:
            items.append(item)
    return _urlencode(
        query=items,
        doseq=doseq,
        safe=safe,
        encoding=encoding,
        errors=errors,
        quote_via=quote_via,
    )


def _item_is_not_empty(item: tuple[str, typing.Any]) -> bool:
    return bool(item[0] and (item[-1] is not None) and item[-1] != "")


def _censor_long_json_strings(text: str, limit: int = 2000) -> str:
    """
    Replace JSON strings (such as base-64 encoded images) longer than `limit`
    with "...".
    """
    limit_expression: str = '[^"]' * limit
    return re.sub(f'"{limit_expression}[^"]*"', '"..."', text)


_PRIMITIVE_VALUE_TYPES: tuple[type, ...] = (
    str,
    bool,
    int,
    float,
    decimal.Decimal,
    date,
    datetime,
)
_PrimitiveValueTypes = typing.Union[
    None, str, bool, int, float, decimal.Decimal, date, datetime, bytes
]


def _format_primitive_value(
    value: _PrimitiveValueTypes,
) -> str | None:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float, decimal.Decimal)):
        return str(value)
    if isinstance(value, bytes):
        return str(
            b64encode(value),
            encoding="ascii",
        )
    if not isinstance(value, (datetime, date)):
        raise TypeError(value)
    return value.isoformat()


def _format_simple_argument_value(
    value: sob.abc.MarshallableTypes,
    *,
    explode: bool = False,
) -> str:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    item: tuple[str, _PrimitiveValueTypes]
    if isinstance(value, dict):
        if explode:
            return ",".join(
                f"{item[0]}={_format_primitive_value(item[1])}"
                for item in value
            )
        return ",".join(
            map(
                _format_primitive_value,  # type: ignore
                chain(*value.items()),
            )
        )
    if isinstance(value, collections.abc.Sequence):
        return ",".join(map(_format_primitive_value, value))  # type: ignore
    raise ValueError(value)


def _format_label_argument_value(
    value: sob.abc.MarshallableTypes,
    *,
    explode: bool = False,
) -> str:
    argument_value: str
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        argument_value = _format_primitive_value(value)  # type: ignore
    elif explode:
        item: tuple[str, _PrimitiveValueTypes]
        if isinstance(value, dict):
            argument_value = ".".join(
                f"{item[0]}=" f"{_format_primitive_value(item[1])}"
                for item in value
            )
        elif isinstance(value, collections.abc.Sequence):
            argument_value = ".".join(
                map(_format_primitive_value, value)  # type: ignore
            )
        else:
            raise ValueError(value)
    else:
        argument_value = _format_simple_argument_value(value, explode=False)
    return f".{argument_value}"


def _format_matrix_argument_value(
    name: str,
    value: sob.abc.MarshallableTypes,
    *,
    explode: bool = False,
) -> str | dict[str, str] | collections.abc.Sequence[str] | None:
    argument_value: str
    if value is None:
        return None
    if isinstance(value, _PRIMITIVE_VALUE_TYPES):
        argument_value = f";{name}={_format_primitive_value(value)}"  # type: ignore
    elif explode:
        item: tuple[str, _PrimitiveValueTypes]
        if isinstance(value, dict):
            argument_value = "".join(
                (f";{item[0]}=" f"{_format_primitive_value(item[1])}")
                for item in value
            )
        elif isinstance(value, collections.abc.Sequence):
            value_: _PrimitiveValueTypes
            argument_value = "".join(
                (f";{name}={_format_primitive_value(value_)}")
                for value_ in value
            )
        else:
            raise TypeError(value)
    else:
        argument_value = _format_simple_argument_value(value, explode=False)
        argument_value = f";{name}={argument_value}"
    return argument_value


def _format_form_argument_value(
    value: sob.abc.MarshallableTypes,
    *,
    explode: bool = False,
) -> str | dict[str, str] | collections.abc.Sequence[str] | None:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    if explode:
        if isinstance(value, collections.abc.Mapping):
            key: str
            value_: sob.abc.MarshallableTypes
            return {
                key: _format_primitive_value(value_) or ""
                for key, value_ in value.items()
            }
        if isinstance(value, collections.abc.Sequence):
            return tuple(map(_format_primitive_value, value))  # type: ignore
        raise ValueError(value)
    return _format_simple_argument_value(value)


def _format_space_delimited_argument_value(
    value: sob.abc.MarshallableTypes,
    *,
    explode: bool = False,
) -> str | dict[str, str] | collections.abc.Sequence[str] | None:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    if explode:
        return _format_form_argument_value(value, explode=explode)
    if isinstance(value, collections.abc.Sequence):
        return " ".join(
            map(_format_primitive_value, value)  # type: ignore
        )
    # This style is only valid for arrays
    raise ValueError(value)


def _format_pipe_delimited_argument_value(
    value: sob.abc.MarshallableTypes,
    *,
    explode: bool = False,
) -> str | dict[str, str] | collections.abc.Sequence[str] | None:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    if explode:
        return _format_form_argument_value(value, explode=explode)
    if isinstance(value, collections.abc.Sequence):
        return "|".join(
            map(_format_primitive_value, value)  # type: ignore
        )
    # This style is only valid for arrays
    raise ValueError(value)


def _format_deep_object_argument_value(
    name: str,
    value: sob.abc.MarshallableTypes,
    *,
    explode: bool = False,
) -> str | dict[str, str] | collections.abc.Sequence[str] | None:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    message: str
    if not explode:
        message = (
            "The `deepObject` argument style only supports `explode=True`."
        )
        raise ValueError(message)
    if isinstance(value, collections.abc.Mapping):
        key: str
        value_: sob.abc.MarshallableTypes
        return {
            f"{name}[{key}]": _format_primitive_value(value_) or ""
            for key, value_ in value.items()
        }
    # This style is only valid for dictionaries
    raise ValueError(value)


def format_argument_value(
    name: str,
    value: sob.abc.MarshallableTypes | typing.IO[bytes],
    style: str,
    *,
    explode: bool = False,
    multipart: bool = False,
) -> (
    str
    | dict[str, str]
    | collections.abc.Sequence[str]
    | collections.abc.Sequence[bytes]
    | bytes
    | collections.abc.Sequence[typing.IO[bytes]]
    | typing.IO[bytes]
    | None
):
    """
    Format an argument value for use in a path, query, cookie, header, etc.

    Parameters:
        value:
        style:
        explode:
        multipart: Indicates the argument will be part of a
            multipart request

    See: https://swagger.io/docs/specification/serialization/
    """
    if multipart and (
        isinstance(value, (bytes, sob.abc.Readable))
        or (
            value
            and (not isinstance(value, str))
            and isinstance(value, collections.abc.Sequence)
            and isinstance(value[0], (bytes, sob.abc.Readable))
        )
    ):
        # For multipart requests, we don't apply any formatting to `bytes`
        # objects, as they will be sent in binary format
        return value
    if isinstance(value, sob.abc.Model):
        value = sob.marshal(value)  # type: ignore
    if style == "simple":
        return _format_simple_argument_value(value, explode=explode)
    if style == "label":
        return _format_label_argument_value(value, explode=explode)
    if style == "matrix":
        return _format_matrix_argument_value(name, value, explode=explode)
    if style == "form":
        return _format_form_argument_value(value, explode=explode)
    if style == "spaceDelimited":
        return _format_space_delimited_argument_value(value, explode=explode)
    if style == "pipeDelimited":
        return _format_pipe_delimited_argument_value(value, explode=explode)
    if style == "deepObject":
        return _format_deep_object_argument_value(name, value, explode=explode)
    raise ValueError(style)


def get_request_curl(
    request: Request,
    options: str = "-i",
    censored_headers: collections.abc.Iterable[str] = (
        "X-api-key",
        "Authorization",
    ),
    censored_parameters: tuple[str, ...] = ("client_secret",),
) -> str:
    """
    Render an instance of `urllib.request.Request` as a `curl` command.

    Parameters:
        options: Any additional parameters to pass to `curl`,
            (such as "--compressed", "--insecure", etc.)
    """
    is_json: bool = bool(
        request.headers.get("Content-Type", "").lower() == "application/json"
    )
    censored_headers = tuple(map(str.lower, censored_headers))

    def _get_request_curl_header_item(item: tuple[str, str]) -> str:
        key: str
        value: str
        key, value = item
        if key.lower() in censored_headers:
            value = "***"
        return "-H {}".format(shlex.quote(f"{key}: {value}"))

    data: bytes = (
        request.data
        if isinstance(request.data, bytes)
        else (
            request.data.read()  # type: ignore
            if isinstance(request.data, sob.abc.Readable)
            else (
                b"".join(request.data) if request.data else b""  # type: ignore
            )
        )
    )
    repr_data: str = ""
    if data:
        data_str = data.decode("utf-8")
        if censored_parameters and not is_json:
            query: dict[str, list[str]] = {}
            key: str
            value: list[str]
            for key, value in parse_qs(data_str).items():
                if key in censored_parameters:
                    query[key] = ["***"]
                else:
                    query[key] = value
            data_str = urlencode(query, safe=f"*{URLENCODE_SAFE}", doseq=True)
        try:
            repr_data = shlex.quote(data_str)
        except UnicodeDecodeError:
            # If the data can't be represented as a command-line argument,
            # use a placeholder
            repr_data = "***"
    return " ".join(
        filter(
            None,
            (
                f"curl -X {request.get_method()}",
                options,
                " ".join(
                    map(
                        _get_request_curl_header_item,
                        sorted(request.headers.items()),  # type: ignore
                    )
                ),
                (f"-d {repr_data}" if data else ""),
                shlex.quote(request.full_url),
            ),
        )
    )


def _represent_http_response(
    response: HTTPResponse,
    data: bytes | None = None,
    censored_headers: tuple[str, ...] = (),
) -> str:
    data = HTTPResponse.read(response) if data is None else data
    content_encoding: str
    for content_encoding in response.getheader("Content-encoding", "").split(
        ","
    ):
        content_encoding = content_encoding.strip().lower()  # noqa: PLW2901
        if content_encoding and content_encoding == "gzip":
            data = gzip.decompress(data)
    if censored_headers:
        censored_headers = tuple(map(str.lower, censored_headers))
    header_items: tuple[tuple[str, typing.Any], ...] = (
        tuple(
            (key, "***" if key.lower() in censored_headers else value)
            for key, value in response.headers.items()
        )
        if censored_headers
        else tuple(response.headers.items())
    )
    headers: str = "\n".join(f"{key}: {value}" for key, value in header_items)
    body: str = (
        f'\n\n{str(data, encoding="utf-8", errors="ignore")}' if data else ""
    )
    return (
        f"{response.geturl()}\n"
        f"{response.getcode()}\n"
        f"{headers}"
        f"{body}"
    )


def _set_response_callback(
    response: HTTPResponse, callback: typing.Callable = print
) -> None:
    """
    Perform a callback on an HTTP response at the time it is read
    """

    @functools.wraps(response.read)
    def response_read(amt: int | None = None) -> bytes:
        data: bytes = HTTPResponse.read(response, amt)
        callback(_represent_http_response(response, data))
        return data

    response.read = response_read  # type: ignore


def default_retry_hook(error: Exception) -> bool:
    """
    By default, don't retry for HTTP 404 (NOT FOUND) errors
    and HTTP 401 (UNAUTHORIZED) errors.
    """
    if isinstance(error, HTTPError) and error.code in (404, 401, 409, 410):
        return False
    return True


def retry(
    errors: tuple[type[Exception], ...] | type[Exception] = Exception,
    retry_hook: typing.Callable[[Exception], bool] = default_retry_hook,
    number_of_attempts: int = 1,
    logger: Logger | None = None,
) -> typing.Callable:
    """
    This function decorates another, and causes the decorated function
    to be re-attempted a specified number of times, with exponential
    backoff, until the decorated function is successful or the maximum
    number of attempts is reached (in which case an exception is raised).

    Parameters:
        errors: A sub-class of `Exception`, or a tuple of one or more
            sub-classes of `Exception`. The default is `Exception`, causing
            *all* errors to trigger a retry.
        retry_hook: A function accepting as its only argument the handled
            exception, and returning a boolean value indicating whether or not
            to retry the function.
        number_of_attempts: The maximum number of times to attempt
            execution of the function, *including* the first execution. Please
            note that, because the default for this parameter is 1, this
            decorator will do *nothing* if this argument is not provided.
    """

    def decorating_function(function: typing.Callable) -> typing.Callable:
        attempt_number: int = 1

        @functools.wraps(function)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            nonlocal attempt_number
            nonlocal number_of_attempts
            if number_of_attempts - attempt_number:
                try:
                    return function(*args, **kwargs)
                except errors as error:
                    if not retry_hook(error):
                        raise
                    warning_message: str = (
                        f"Attempt # {attempt_number!s}:\n"
                        f"{sob.errors.get_exception_text()}"
                    )
                    warn(warning_message, stacklevel=2)
                    if logger is not None:
                        logger.warning(warning_message)
                    sleep(2**attempt_number)
                    attempt_number += 1
                    return wrapper(*args, **kwargs)
            return function(*args, **kwargs)

        return wrapper

    return decorating_function


def _remove_none(
    items: collections.abc.Mapping[str, typing.Any]
    | collections.abc.Sequence[tuple[str, typing.Any]],
) -> collections.abc.Sequence[tuple[str, typing.Any]]:
    if isinstance(items, collections.abc.Mapping):
        items = tuple(items.items())
    item: tuple[str, typing.Any]
    return tuple(filter(lambda item: item[1] is not None, items))


def _format_request_data(  # noqa: C901
    json: str | bytes | sob.abc.Model | None,
    data: collections.abc.Mapping[str, typing.Any]
    | collections.abc.Sequence[tuple[str, typing.Any]],
) -> bytes | None:
    formatted_data: bytes | None = None
    if json:
        message: str
        if data:
            message = (
                "A request may only contain form data or JSON data, not both."
            )
            raise ValueError(message)
        # Cast `data` as a `str`
        if isinstance(json, sob.abc.Model):
            json = sob.serialize(json)
        # Convert `str` data to `bytes`
        if isinstance(json, str):
            formatted_data = bytes(json, encoding="utf-8")
        else:
            formatted_data = json
    elif data:
        data = _remove_none(data)
        data = dict(data)
        if not isinstance(data, collections.abc.MutableMapping):
            raise ValueError(data)
        # Convert bytes to base64-encoded strings
        key: str
        value: typing.Any
        for key, value in tuple(data.items()):
            if isinstance(value, sob.abc.Readable):
                value = value.read()  # noqa: PLW2901
                if not isinstance(value, bytes):
                    raise TypeError(value)
            if isinstance(value, bytes):
                data[key] = str(
                    b64encode(value),
                    encoding="ascii",
                )
        formatted_data = bytes(urlencode(data), encoding="utf-8")
    return formatted_data


def _make_thread_locks_pickleable() -> None:
    """
    This makes it so that thread-locked connections can be pickled
    """
    lock_type: type = type(threading.Lock())
    r_lock_type: type = type(threading.RLock())
    copyreg.pickle(lock_type, lambda _: (threading.Lock, ()))
    copyreg.pickle(r_lock_type, lambda _: (threading.RLock, ()))


_make_thread_locks_pickleable()


def _make_http_errors_pickleable() -> None:
    copyreg.pickle(
        HTTPError,
        lambda error: (  # type: ignore
            HTTPError,  # type: ignore
            (
                error.filename,
                error.code,
                error.msg,  # type: ignore
                error.hdrs,  # type: ignore
                error.fp,
            ),
        ),
    )


_make_http_errors_pickleable()


def _make_loggers_pickleable() -> None:
    """
    This makes it so that loggers can be pickled
    """
    logger: Logger
    copyreg.pickle(Logger, lambda logger: (getLogger, (logger.name,)))


_make_loggers_pickleable()


DEFAULT_RETRY_FOR_ERRORS: tuple[type[Exception], ...] = (
    HTTPError,
    SSLError,
    URLError,
    ConnectionError,
    TimeoutError,
    HTTPException,
)
# For backwards-compatibility...
DEFAULT_RETRY_FOR_EXCEPTIONS: tuple[type[Exception], ...] = (
    DEFAULT_RETRY_FOR_ERRORS
)


class SSLContext(ssl.SSLContext):
    """
    This class is a wrapper for `ssl.SSLContext` which makes it possible to
    connect to hosts which have an unverified SSL certificate.
    """

    def __init__(
        self,
        check_hostname: bool = True,  # noqa: FBT001 FBT002
    ) -> None:
        if check_hostname:
            self.load_default_certs()
        else:
            self.check_hostname: bool = False
            self.verify_mode: ssl.VerifyMode = ssl.CERT_NONE
        super().__init__()

    def __reduce__(self) -> tuple:
        """
        A pickled instance of this class will just be an entirely new
        instance.
        """
        return SSLContext, (self.check_hostname,)


def _get_file_name(file: typing.IO, default: str = "") -> str:
    """
    Get the file name from a file's URL or file path
    """
    name: str = ""
    if hasattr(file, "url"):
        name = file.url
    elif hasattr(file, "name"):
        name = file.name
    if name:
        return name.rstrip("/\\").split("/")[-1].split("\\")[-1]
    return default


def _assemble_request(  # noqa: C901
    url: str,
    method: str,
    json: str | bytes | sob.abc.Model | None,
    data: collections.abc.Mapping[
        str, sob.abc.MarshallableTypes | typing.IO[bytes]
    ],
    headers: collections.abc.MutableMapping[
        str,
        str,
    ],
    *,
    multipart: bool,
    multipart_data_headers: collections.abc.Mapping[
        str,
        collections.abc.MutableMapping[
            str,
            str,
        ],
    ],
) -> Request:
    message: str
    if multipart:
        if json or (not data):
            message = (
                "A multi-part request may only contain form data, "
                "not JSON data."
            )
            raise ValueError(message)
        parts: list[Part] = []
        name: str
        part_data: sob.abc.MarshallableTypes
        for name, part_data in data.items():
            if not (
                isinstance(part_data, collections.abc.Sequence)
                and (not isinstance(part_data, bytes))
                and part_data
                and isinstance(part_data[0], (bytes, sob.abc.Readable))
            ):
                part_data = (part_data,)  # noqa: PLW2901
            datum: sob.abc.MarshallableTypes
            for datum in part_data:
                part_headers: collections.abc.MutableMapping = (
                    multipart_data_headers.get(name, {})
                )
                if "Content-disposition" not in part_headers:
                    filename: str = ""
                    if isinstance(datum, sob.abc.Readable):
                        filename = _get_file_name(datum, name)
                        datum = typing.cast(  # noqa: PLW2901
                            sob.abc.Readable, datum
                        ).read()
                    repr_filename: str = (
                        f'; filename="{filename}"' if filename else ""
                    )
                    part_headers["Content-disposition"] = (
                        f'form-data; name="{name}"{repr_filename}'
                    )
                if "Content-type" not in part_headers:
                    if isinstance(datum, bytes):
                        part_headers["Content-type"] = (
                            "application/octet-stream"
                        )
                    elif isinstance(datum, str):
                        part_headers["Content-type"] = "text/plain"
                    else:
                        part_headers["Content-type"] = "application/json"
                parts.append(Part(data=datum, headers=part_headers))
        return MultipartRequest(
            url=url,
            method=method.upper(),
            headers=headers,
            parts=parts,
        )
    if url.lower().rpartition(":")[0] not in ("http", "https", ""):
        raise ValueError(url)
    return Request(  # noqa: S310
        url,
        data=_format_request_data(json, data),
        method=method.upper(),
        headers=headers,
    )


def _get_first(items: collections.abc.Iterable[typing.Any]) -> typing.Any:
    return next(iter(items))


class Client:
    """
    A base class for OpenAPI clients.
    """

    __slots__: tuple[str, ...] = (
        "url",
        "user",
        "password",
        "bearer_token",
        "api_key",
        "api_key_in",
        "api_key_name",
        "oauth2_client_id",
        "oauth2_client_secret",
        "oauth2_username",
        "oauth2_password",
        "oauth2_authorization_url",
        "oauth2_token_url",
        "oauth2_scope",
        "oauth2_refresh_url",
        "oauth2_flows",
        "open_id_connect_url",
        "headers",
        "timeout",
        "retry_number_of_attempts",
        "retry_for_errors",
        "retry_hook",
        "verify_ssl_certificate",
        "logger",
        "echo",
        "_cookie_jar",
        "__opener",
        "_oauth2_authorization_expires",
    )

    def __init__(
        self,
        url: str | None = None,
        *,
        user: str | None = None,
        password: str | None = None,
        bearer_token: str | None = None,
        api_key: str | None = None,
        api_key_in: typing.Literal["header", "query", "cookie"] = "header",
        api_key_name: str = "X-API-KEY",
        oauth2_client_id: str | None = None,
        oauth2_client_secret: str | None = None,
        oauth2_username: str | None = None,
        oauth2_password: str | None = None,
        oauth2_authorization_url: str | None = None,
        oauth2_token_url: str | None = None,
        oauth2_scope: str | tuple[str, ...] | None = None,
        oauth2_refresh_url: str | None = None,
        oauth2_flows: tuple[
            typing.Literal[
                "authorizationCode",
                "implicit",
                "password",
                "clientCredentials",
                # OpenAPI 2.x Compatibility:
                "accessCode",
                "application",
            ],
            ...,
        ]
        | None = None,
        open_id_connect_url: str | None = None,
        headers: collections.abc.Mapping[str, str]
        | collections.abc.Sequence[tuple[str, str]] = (
            ("Accept", "application/json"),
            ("Content-type", "application/json"),
        ),
        timeout: int = 0,
        retry_number_of_attempts: int = 1,
        retry_for_errors: tuple[
            type[Exception], ...
        ] = DEFAULT_RETRY_FOR_ERRORS,
        retry_hook: typing.Callable[  # Force line-break retention
            [Exception], bool
        ] = default_retry_hook,
        verify_ssl_certificate: bool = True,
        logger: Logger | None = None,
        echo: bool = False,
    ) -> None:
        """
        Parameters:
            url: The base URL for API requests.
            user: A user name for use with HTTP basic authentication.
            password:  A password for use with HTTP basic authentication.
            bearer_token: A token for use with HTTP bearer authentication.
            api_key: An API key with which to authenticate requests.
            api_key_in: Where the API key should be conveyed:
                "header", "query" or "cookie".
            api_key_name: The name of the header, query parameter, or
                cookie parameter in which to convey the API key.
            oauth2_client_id: An OAuth2 client ID.
            oauth2_client_secret: An OAuth2 client secret.
            oauth2_username: A *username* for the "password" OAuth2 grant
                type.
            oauth2_password: A *password* for the "password" OAuth2 grant
                type.
            oauth2_authorization_url: The authorization URL to use for an
                OAuth2 flow. Can be relative to `url`.
            oauth2_token_url: The token URL to use for OAuth2
                authentication. Can be relative to `url`.
            oauth2_refresh_url: The URL to be used for obtaining refresh
                tokens for OAuth2 authentication.
            oauth2_flows: A tuple containing one or more of the
                following: "authorizationCode", "implicit", "password" and/or
                "clientCredentials".
            open_id_connect_url: An OpenID connect URL where a JSON
                web token containing OAuth2 information can be found.
            headers: Default headers to include with all requests.
                Method-specific header arguments will override or modify these,
                where applicable, as will dynamically modified headers such as
                content-length, authorization, cookie, etc.
            timeout: The number of seconds before a request will timeout
                and throw an error. If this is 0 (the default), the system
                default timeout will be used.
            retry_number_of_attempts: The number of times to retry
                a request which results in an error.
            retry_for_errors: A tuple of one or more exception types
                on which to retry a request. To retry for *all* errors,
                pass `(Exception,)` for this argument.
            retry_hook: A function, accepting one argument (an Exception),
                and returning a boolean value indicating whether to retry the
                request (if retries have not been exhausted). This hook applies
                *only* for exceptions which are a sub-class of an exception
                included in `retry_for_errors`.
            verify_ssl_certificate: If `True`, SSL certificates
                are verified, per usual. If `False`, SSL certificates are *not*
                verified.
            logger:
                A `logging.Logger` to which requests should be logged.
            echo: If `True`, requests/responses are printed as
                they occur.
        """
        message: str
        # Ensure the API key location is valid
        if api_key_in not in ("header", "query", "cookie"):
            message = (
                f"Invalid input for `api_key_in`:  {api_key_in!r}\n"
                'Valid values are "header", "query" or "cookie".'
            )
            raise ValueError(message)
        # Translate OpenAPI 2x OAuth2 flow names
        if oauth2_flows:
            flow: str
            oauth2_flows = tuple(
                (
                    "authorizationCode"
                    if flow == "accessCode"
                    else "clientCredentials"
                    if flow == "application"
                    else flow
                )
                for flow in oauth2_flows
            )
        # Ensure OAuth2 flows are valid
        if oauth2_flows and not all(
            flow
            in {
                "authorizationCode",
                "implicit",
                "password",
                "clientCredentials",
            }
            for flow in oauth2_flows
        ):
            message = (
                f"Invalid value(s) for `oauth2_flows`:  {api_key_in!r}\n"
                'Valid values are "authorizationCode", "implicit", '
                '"password", or "clientCredentials".'
            )
            raise ValueError(message)
        # Ensure URLs are HTTP/HTTPS (security concern) *or* are relative URLs
        url_: str | None
        for url_ in (
            url,
            oauth2_authorization_url,
            oauth2_token_url,
            oauth2_refresh_url,
            open_id_connect_url,
        ):
            if url_ and (
                url_.lower().rpartition(":")[0] not in ("http", "https", "")
            ):
                raise ValueError(url_)
        # Set properties
        self.url: str | None = url
        self.user: str | None = user
        self.password: str | None = password
        self.bearer_token: str | None = bearer_token
        self.api_key: str | None = api_key
        self.api_key_in: typing.Literal["header", "query", "cookie"] = (
            api_key_in
        )
        self.api_key_name: str = api_key_name
        self.oauth2_client_id: str | None = oauth2_client_id
        self.oauth2_client_secret: str | None = oauth2_client_secret
        self.oauth2_username: str | None = oauth2_username
        self.oauth2_password: str | None = oauth2_password
        self.oauth2_authorization_url: str | None = oauth2_authorization_url
        self.oauth2_token_url: str | None = oauth2_token_url
        self.oauth2_scope: str | tuple[str, ...] | None = oauth2_scope
        self.oauth2_refresh_url: str | None = oauth2_refresh_url
        self.oauth2_flows: (
            typing.Literal[
                "authorizationCode",
                "implicit",
                "password",
                "clientCredentials",
            ]
            | None
        ) = oauth2_flows  # type: ignore
        self.open_id_connect_url: str | None = open_id_connect_url
        self.headers: dict[str, str] = dict(headers)
        self.timeout: int = timeout
        self.retry_number_of_attempts: int = retry_number_of_attempts
        self.retry_for_errors: tuple[type[Exception], ...] = retry_for_errors
        self.retry_hook: typing.Callable[[Exception], bool] = retry_hook
        self.verify_ssl_certificate: bool = verify_ssl_certificate
        self.logger: Logger | None = logger
        self.echo: bool = echo
        # Support for persisting cookies
        self._cookie_jar: CookieJar = CookieJar()
        self.__opener: OpenerDirector | None = None
        self._oauth2_authorization_expires: int = 0

    @property
    def _opener(self) -> OpenerDirector:
        if self.__opener is None:
            self.__opener = build_opener(
                HTTPSHandler(
                    context=SSLContext(
                        check_hostname=self.verify_ssl_certificate
                    )
                ),
                HTTPCookieProcessor(self._cookie_jar),
            )
        return self.__opener

    @classmethod
    def _resurrect_client(cls, *args: typing.Any) -> Client:
        """
        This function is for use with the `.__reduce__` method of
        `oapi.client.Client` and its sub-classes, in order to properly
        un-pickle instances which have been pickled (such as for use in
        multiprocessing, etc.).
        """
        warn(
            (
                "Your client module appears to be out of date. "
                "Client pickling/un-pickling, as of OAPI version "
                "1.62, is performed through `__getstate__` and "
                "`__setstate__`. Remodel your client to "
                "remedy. This method will be removed in OAPI 2.0."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        init_parameters: list[typing.Any] = list(args)
        oauth2_authorization_expires: int = init_parameters.pop()
        cookie_jar: CookieJar = init_parameters.pop()
        client: Client = cls(*init_parameters)
        client._cookie_jar = cookie_jar  # noqa: SLF001
        client._oauth2_authorization_expires = (  # noqa: SLF001
            oauth2_authorization_expires
        )
        return client

    def __getstate__(self) -> dict[str, typing.Any]:
        # Get a dictionary of attributes for pickling
        slot: str
        return {
            slot: getattr(self, slot)
            for slot in filter(
                lambda slot: slot != "__opener",
                # Get all inherited slots
                chain.from_iterable(
                    getattr(cls, "__slots__", ()) for cls in type(self).__mro__
                ),
            )
        }

    def __setstate__(self, state: dict[str, typing.Any]) -> None:
        # Unpickle an instance of `oapi.client.Client` from a state dictionary
        # Determine which state keys are parameters for the `__init__` method
        parameters: collections.abc.Iterable[tuple[str, inspect.Parameter]] = (
            inspect.signature(
                self.__init__  # type: ignore
            ).parameters.items()
        )
        item: tuple[str, inspect.Parameter]
        parameter_names: set[str] = set(
            map(
                _get_first,
                filter(
                    lambda item: item[1].kind
                    not in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.POSITIONAL_ONLY,
                    ),
                    parameters,
                ),
            )
        )
        state_keys: set[str] = set(state.keys())
        kwargs: dict[str, typing.Any] = {}
        key: str
        value: typing.Any
        for key in state_keys & parameter_names:
            kwargs[key] = state.pop(key)
        self.__init__(**kwargs)  # type: ignore
        # Set the remaining state slots
        deque(
            (
                setattr(self, *item)  # type: ignore
                for item in state.items()
            ),
            maxlen=0,
        )

    def _get_request_response_callback(
        self, error: HTTPError | None = None
    ) -> typing.Callable:
        def callback(text: str) -> None:
            text = _censor_long_json_strings(text)
            if self.logger is not None:
                if error:
                    self.logger.error(text)
                else:
                    self.logger.info(text)
            if error is not None:
                sob.errors.append_exception_text(error, f"\n{text}")
            elif self.echo:
                print(text)  # noqa: T201

        return callback

    def request(
        self,
        path: str,
        method: str,
        *,
        json: str | bytes | sob.abc.Model | None = None,
        data: collections.abc.Mapping[str, sob.abc.MarshallableTypes]
        | collections.abc.Sequence[tuple[str, sob.abc.MarshallableTypes]] = (),
        query: collections.abc.Mapping[str, sob.abc.MarshallableTypes]
        | collections.abc.Sequence[tuple[str, sob.abc.MarshallableTypes]] = (),
        headers: collections.abc.Mapping[str, sob.abc.MarshallableTypes]
        | collections.abc.Sequence[tuple[str, sob.abc.MarshallableTypes]] = (),
        multipart: bool = False,
        multipart_data_headers: collections.abc.Mapping[
            str, collections.abc.MutableMapping[str, str]
        ]
        | collections.abc.Sequence[
            tuple[str, collections.abc.MutableMapping[str, str]]
        ] = (),
        timeout: int = 0,
    ) -> sob.abc.Readable:
        """
        Construct and submit an HTTP request and return the response
        (an instance of `http.client.HTTPResponse`).

        Parameters:
            path: This is the path of the request, relative to the server
                base URL
            query:
            json: JSON data to be conveyed in the body of the request
            data: Form data to be conveyed
                in the body of the request
            multipart: If `True`, `data` should be conveyed
                as a multipart request.
            query: A dictionary from which to assemble the
                query string.
            headers:
            multipart_data_headers:
            timeout:
        """
        # For backwards compatibility...
        if isinstance(data, (str, bytes, sob.abc.Model)) or (data is None):
            json = data
            data = ()
        request: typing.Callable[
            [
                str,
                str,
                str | bytes | sob.abc.Model | None,
                collections.abc.Mapping[str, sob.abc.MarshallableTypes]
                | collections.abc.Sequence[
                    tuple[str, sob.abc.MarshallableTypes]
                ],
                collections.abc.Mapping[str, sob.abc.MarshallableTypes]
                | collections.abc.Sequence[
                    tuple[str, sob.abc.MarshallableTypes]
                ],
                collections.abc.Mapping[str, sob.abc.MarshallableTypes]
                | collections.abc.Sequence[
                    tuple[str, sob.abc.MarshallableTypes]
                ],
                bool,
                collections.abc.Mapping[
                    str, collections.abc.MutableMapping[str, str]
                ]
                | collections.abc.Sequence[
                    tuple[str, collections.abc.MutableMapping[str, str]]
                ],
                int,
            ],
            sob.abc.Readable,
        ] = self._request
        # Wrap the _request method with a retry decorator if more
        # than one attempt is specified in the config
        if self.retry_number_of_attempts > 1:
            request = retry(
                errors=self.retry_for_errors,
                number_of_attempts=self.retry_number_of_attempts,
                retry_hook=self.retry_hook,
                logger=self.logger,
            )(self._request)
        return request(
            path,
            method,
            json,
            data,
            query,
            headers,
            multipart,
            multipart_data_headers,
            timeout,
        )

    def _request_callback(self, request: Request) -> None:
        curl_options: str = "-i"
        content_encoding: str
        for content_encoding in request.headers.get(
            "Content-encoding", ""
        ).split(","):
            content_encoding = (  # noqa: PLW2901
                content_encoding.strip().lower()
            )
            if content_encoding and content_encoding == "gzip":
                curl_options = f"{curl_options} --compressed"
        if not self.verify_ssl_certificate:
            curl_options = f"{curl_options} -k"
        self._get_request_response_callback()(
            get_request_curl(request, options=curl_options)
        )

    def _request_oauth2_password_authorization(
        self,
    ) -> sob.abc.Readable:
        message: str
        if self.oauth2_token_url is None:
            message = "No OAuth2 token URL was provided."
            raise RuntimeError(message)
        if self.oauth2_username is None:
            message = "No OAuth2 username was provided."
            raise RuntimeError(message)
        if self.oauth2_password is None:
            message = "No OAuth2 password was provided."
            raise RuntimeError(message)
        try:
            data_dict: dict[str, str | tuple[str, ...] | None] = {
                "grant_type": "password",
                "client_id": self.oauth2_client_id,
                "username": self.oauth2_username,
                "password": self.oauth2_password,
            }
            if self.oauth2_scope is not None:
                data_dict.update(scope=self.oauth2_scope)
            return self._opener.open(  # type: ignore
                Request(  # noqa: S310
                    self.oauth2_token_url,
                    headers={"Host": urlparse(self.oauth2_token_url).netloc},
                    method="POST",
                    data=bytes(
                        urlencode(data_dict),
                        encoding="ascii",
                    ),
                )
            )
        except HTTPError as error:
            location: str = error.headers.get(
                "Location", self.oauth2_token_url
            )
            if location != self.oauth2_token_url:
                self.oauth2_token_url = location
                return self._request_oauth2_password_authorization()
            raise

    def _request_oauth2_client_credentials_authorization(
        self,
    ) -> sob.abc.Readable:
        message: str
        if self.oauth2_token_url is None:
            message = "No OAuth2 token URL was provided."
            raise RuntimeError(message)
        if self.oauth2_client_id is None:
            message = "No OAuth2 client ID was provided."
            raise RuntimeError(message)
        if self.oauth2_client_secret is None:
            message = "No OAuth2 client secret was provided."
            raise RuntimeError(message)
        try:
            data_dict: dict[str, str | tuple[str, ...] | None] = {
                "grant_type": "client_credentials",
                "client_id": self.oauth2_client_id,
                "client_secret": self.oauth2_client_secret,
            }
            if self.oauth2_scope is not None:
                data_dict.update(scope=self.oauth2_scope)
            data: str = urlencode(data_dict)
            request: Request = Request(  # noqa: S310
                self.oauth2_token_url,
                headers={"Host": urlparse(self.oauth2_token_url).netloc},
                method="POST",
                data=bytes(
                    data,
                    encoding="ascii",
                ),
            )
            self._request_callback(request)
            return self._opener.open(  # type: ignore
                request
            )
        except HTTPError as error:
            location: str | None = error.headers.get(
                "Location", self.oauth2_token_url
            )
            if (location is not None) and location != self.oauth2_token_url:
                self.oauth2_token_url = location
                return self._request_oauth2_client_credentials_authorization()
            raise

    def _get_oauth2_client_credentials_authorization(self) -> str:
        if self._oauth2_authorization_expires < int(time.time()) or (
            "Authorization" not in self.headers
        ):
            # If our authorization has expired, get a new token
            with (
                self._request_oauth2_client_credentials_authorization()
            ) as response:
                data: bytes | str = response.read()
                response_data: dict[str, str] = json.loads(
                    data.decode("utf-8") if isinstance(data, bytes) else data
                )
                self._oauth2_authorization_expires = (
                    int(time.time()) + int(response_data["expires_in"]) - 1
                )
                self.headers["Authorization"] = (
                    f'{response_data["token_type"]} '
                    f'{response_data["access_token"]}'
                )
        return self.headers["Authorization"]

    def _get_oauth2_password_authorization(self) -> str:
        if self._oauth2_authorization_expires < int(time.time()) or (
            "Authorization" not in self.headers
        ):
            # If our authorization has expired, get a new token
            with self._request_oauth2_password_authorization() as response:
                data: bytes | str = response.read()
                response_data: dict[str, str] = json.loads(
                    data.decode("utf-8") if isinstance(data, bytes) else data
                )
                self._oauth2_authorization_expires = (
                    int(time.time()) + int(response_data["expires_in"]) - 1
                )
                self.headers["Authorization"] = (
                    f'{response_data["token_type"]} '
                    f'{response_data["access_token"]}'
                )
        return self.headers["Authorization"]

    def _oauth2_authenticate_request(self, request: Request) -> None:
        if self.oauth2_client_id and self.oauth2_client_secret:
            # A client ID and client secret are only applicable to the
            # client credentials flow, so we can infer that is the correct
            # flow to use (regardless of whether it is specified in the flows).
            request.add_header(
                "Authorization",
                self._get_oauth2_client_credentials_authorization(),
            )
        elif (
            self.oauth2_client_id
            and self.oauth2_username
            and self.oauth2_password
        ):
            # A client ID and client secret are only applicable to the
            # client credentials flow, so we can infer that is the correct
            # flow to use (regardless of whether it is specified in the flows).
            request.add_header(
                "Authorization",
                self._get_oauth2_password_authorization(),
            )
        elif self.oauth2_flows:
            if "implicit" in self.oauth2_flows:
                # TODO: implicit OAuth2 flow
                warn(
                    'The "implicit" OAuth2 flow is not currently implemented.',
                    stacklevel=2,
                )
            if "password" in self.oauth2_flows:
                warn(
                    'The "password" OAuth2 flow requires the client be '
                    "initialized with `oauth2_client_id`, `oauth2_username`, "
                    "and `oauth2_password` arguments.",
                    stacklevel=2,
                )
            if "clientCredentials" in self.oauth2_flows:
                warn(
                    'The "clientCredentials" OAuth2 flow requires the client '
                    "be initialized with `oauth2_client_id`, "
                    "`oauth2_username`, and `oauth2_password` arguments.",
                    stacklevel=2,
                )
            if "authorizationCode" in self.oauth2_flows:
                # TODO: authorizationCode OAuth2 flow
                warn(
                    'The "authorizationCode" OAuth2 flow is not currently '
                    "implemented.",
                    stacklevel=2,
                )

    def _api_key_authenticate_request(self, request: Request) -> None:
        # API key authentication:
        # https://swagger.io/docs/specification/v3_0/authentication/api-keys/
        message: str
        if self.api_key_in == "cookie":
            cookie_header: str = request.get_header("Cookie", "")
            if cookie_header:
                cookie_header = f"{cookie_header}; "
            cookie_header = (
                f"{cookie_header}" f"{self.api_key_name}" f"={self.api_key}"
            )
            request.add_header("Cookie", cookie_header)
        elif self.api_key_in == "query":
            if self.api_key is None:
                message = "No API key has been provided."
                raise RuntimeError(message)
            api_key_query_assignment: str = (
                f"{self.api_key_name}={quote(self.api_key)}"
            )
            parse_result: ParseResult = urlparse(request.full_url)
            parse_result_dictionary: dict[str, str] = parse_result._asdict()
            parse_result_dictionary["query"] = (
                f"{parse_result.query}&{api_key_query_assignment}"
                if parse_result.query
                else api_key_query_assignment
            )
            request.full_url = urlunparse(
                ParseResult(**parse_result_dictionary)
            )
        else:
            if not self.api_key_in == "header":
                raise ValueError(self.api_key_in)
            if self.api_key is None:
                message = "No API key has been provided."
                raise RuntimeError(message)
            request.add_header(self.api_key_name, self.api_key)

    def _authenticate_request(self, request: Request) -> None:
        """
        Determine the applicable authentication scheme and authenticate a
        request.

        Parameters:
            request:
        """
        # TODO: [Implement additional HTTP authentication schemes]
        # (https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml)
        if self.user and self.password:
            # [Basic authentication]
            # (https://swagger.io/docs/specification/v3_0/authentication/basic-authentication/)
            login: str = str(
                b64encode(
                    bytes(f"{self.user}:{self.password}", encoding="utf-8")
                ),
                encoding="ascii",
            )
            request.add_header("Authorization", f"Basic {login}")
        if self.bearer_token:
            # [Bearer authentication]
            # (https://swagger.io/docs/specification/v3_0/authentication/bearer-authentication/)
            request.add_header("Authorization", f"Bearer {self.bearer_token}")
        # API Key & Cookie Authentication schemes
        if self.api_key:
            self._api_key_authenticate_request(request)
        # OAuth2 Authentication schemes
        if (
            (self.oauth2_client_id and self.oauth2_client_secret)
            or (
                self.oauth2_client_id
                and self.oauth2_username
                and self.oauth2_password
            )
            or self.oauth2_flows
        ):
            self._oauth2_authenticate_request(request)

    def _request(  # noqa: C901
        self,
        path: str,
        method: str,
        json: str | bytes | sob.abc.Model | None = None,
        data: collections.abc.Mapping[str, sob.abc.MarshallableTypes]
        | collections.abc.Sequence[tuple[str, sob.abc.MarshallableTypes]] = (),
        query: collections.abc.Mapping[str, sob.abc.MarshallableTypes]
        | collections.abc.Sequence[tuple[str, sob.abc.MarshallableTypes]] = (),
        headers: collections.abc.Mapping[str, sob.abc.MarshallableTypes]
        | collections.abc.Sequence[tuple[str, sob.abc.MarshallableTypes]] = (),
        multipart: bool = False,  # noqa: FBT001 FBT002
        multipart_data_headers: collections.abc.Mapping[
            str, collections.abc.MutableMapping[str, str]
        ]
        | collections.abc.Sequence[
            tuple[str, collections.abc.MutableMapping[str, str]]
        ] = (),
        timeout: int = 0,
    ) -> sob.abc.Readable:
        if query:
            query = _remove_none(query)
        if query:
            path = f"{path}?{urlencode(query)}"
        # Prepend the base URL, if the URL is relative
        parse_result: ParseResult = urlparse(path)
        if parse_result.scheme:
            url = path
        else:
            if not path[0] == "/":
                raise ValueError(path)
            url = f"{self.url}{path}"
        request_headers: dict[str, str] = dict(self.headers)
        if headers:
            key: str
            value: str
            request_headers.update(
                **{  # type: ignore
                    key: value
                    for key, value in (
                        headers.items()
                        if isinstance(headers, collections.abc.Mapping)
                        else headers
                    )
                    if key and value
                }
            )
        # Assemble the request
        request = _assemble_request(
            url=url,
            method=method,
            headers=request_headers,
            json=json,
            data=dict(data),
            multipart=multipart,
            multipart_data_headers=dict(multipart_data_headers),
        )
        # Authenticate the request
        self._authenticate_request(request)
        # Assemble keyword arguments for passing to the opener
        open_kwargs: dict[str, typing.Any] = {}
        if timeout:
            open_kwargs.update(timeout=timeout)
        elif self.timeout:
            open_kwargs.update(timeout=self.timeout)
        # Set request callback
        self._request_callback(request)
        # Process the request
        response: HTTPResponse
        try:
            response = self._opener.open(request, **open_kwargs)
            # Add callback
            _set_response_callback(
                response, self._get_request_response_callback()
            )
        except HTTPError as error:
            error_response: HTTPResponse | None = getattr(error, "file", None)
            if error_response is not None:
                sob.errors.append_exception_text(
                    error,
                    "\n\n{}".format(
                        _censor_long_json_strings(
                            _represent_http_response(error_response)
                        )
                    ),
                )
            raise
        if not isinstance(response, sob.abc.Readable):
            raise TypeError(response)
        return response


# For backwards compatibility
CLIENT_SLOTS: tuple[str, ...] = Client.__slots__  # type: ignore

# endregion


def _get_path_open_api(path: str) -> OpenAPI:
    with open(path) as open_api_io:
        if not isinstance(open_api_io, sob.abc.Readable):
            raise TypeError(open_api_io)
        return _get_io_open_api(open_api_io)


def _get_url_open_api(url: str) -> OpenAPI:
    with urlopen(url) as open_api_io:  # noqa: S310
        return _get_io_open_api(open_api_io)


def _get_io_open_api(model_io: sob.abc.Readable) -> OpenAPI:
    return OpenAPI(model_io)


def _iter_path_item_operations(
    path_item: PathItem,
) -> collections.abc.Iterable[tuple[str, Operation]]:
    """
    Yield all operations on a path as a tuple of the operation name
    ("get", "put", "post", "patch", etc.) and the object representing that
    operation (an instance of `oapi.oas.model.Operation`).

    Parameters:
        path_item:
    """
    name_: str
    name: str
    value: sob.abc.MarshallableTypes
    for name, value in (
        (name_, getattr(path_item, name_))
        for name_ in (
            "get",
            "put",
            "post",
            "delete",
            "options",
            "head",
            "patch",
            "trace",
        )
    ):
        if value is not None:
            if not isinstance(value, Operation):
                raise TypeError(value)
            yield name, value


def _get_relative_module_path(
    from_path: str | Path, to_path: str | Path
) -> str:
    """
    Get a relative import based on module file paths

    Examples:

    >>> _get_relative_module_path("a/b/c.py", "d/e/f.py")
    '...a.b.c'

    >>> _get_relative_module_path("a/b/c.py", "a/b/f.py")
    '.c'
    """
    if isinstance(from_path, Path):
        from_path = str(from_path)
    if isinstance(to_path, Path):
        to_path = str(to_path)
    return re.sub(
        r".py$",
        "",
        re.sub(
            "^../",
            ".",
            os.path.relpath(
                from_path.replace("/__init__.py", ".py").replace(
                    "\\__init__.py", ".py"
                ),
                to_path,
            ).replace("\\", "/"),
        )
        .replace("../", ".")
        .replace("/", "."),
    )


def _get_relative_module_import(
    from_path: str | Path, to_path: str | Path
) -> str:
    """
    Get a relative import based on module file paths

    Examples:

    >>> _get_relative_module_import("a/b/c.py", "d/e/f.py")
    'from ...a.b import c'

    >>> _get_relative_module_import("a/b/c.py", "a/b/f.py")
    'from . import c'
    """
    relative_module_path: str = _get_relative_module_path(
        from_path=from_path, to_path=to_path
    )
    matched: Match | None = re.match(  # type: ignore
        r"^(\.*)(?:(.*)\.)?([^.]+)", relative_module_path
    )
    if matched is None:
        raise ValueError((from_path, to_path, relative_module_path))
    groups: tuple[str, str, str] = matched.groups()
    if len(groups) != 3:  # noqa: PLR2004
        raise ValueError(relative_module_path)
    return f"from {groups[0] or ''}{groups[1] or ''} import {groups[2]}"


def _schema_defines_model(schema: Schema | Parameter) -> bool:
    return schema.type_ in (
        "object",
        "array",
    )


@dataclass
class _Parameter:
    index: int = 0
    name: str = ""
    types: sob.abc.Types = field(default_factory=sob.types.Types)
    explode: bool = False
    style: str = ""
    description: str = ""
    content_type: str = ""
    headers: collections.abc.Mapping[str, Header | Reference] = field(
        default_factory=dict
    )


@dataclass
class _ParameterLocations:
    """
    Properties:
        total_count: The total number of parameters accounted for.
        header: A mapping of header parameter
            names to information about each parameter.
        body: A parameter representing the body
            of a request in JSON format.
        form_data: A mapping of form data
            parameter names to information about the parameter.
        multipart: Indicates that the form data is multipart.
        path: A mapping of path
            parameter names to information about each parameter.
        query: A mapping of query string
            parameter names to information about each parameter.
        cookie: A mapping of cookie
            parameter names to information about each parameter.
    """

    total_count: int = 0
    header: dict[str, _Parameter] = field(default_factory=dict)
    body: _Parameter | None = None
    path: dict[str, _Parameter] = field(default_factory=dict)
    query: dict[str, _Parameter] = field(default_factory=dict)
    form_data: dict[str, _Parameter] = field(default_factory=dict)
    multipart: bool = False
    cookie: dict[str, _Parameter] = field(default_factory=dict)


def _iter_parameters(
    parameter_locations: _ParameterLocations,
) -> collections.abc.Iterable[tuple[str, _Parameter]]:
    if parameter_locations.body:
        yield parameter_locations.body.name, parameter_locations.body
    yield from chain(
        parameter_locations.header.items(),
        parameter_locations.path.items(),
        parameter_locations.query.items(),
        parameter_locations.form_data.items(),
        parameter_locations.cookie.items(),
    )


def _iter_sorted_parameters(
    parameter_locations: _ParameterLocations,
) -> collections.abc.Iterable[tuple[str, _Parameter]]:
    item: tuple[str, _Parameter]
    return sorted(
        _iter_parameters(parameter_locations), key=lambda item: item[1].index
    )


def _iter_request_path_representation(
    path: str, parameter_locations: _ParameterLocations
) -> collections.abc.Iterable[str]:
    path_representation: str = sob.utilities.represent(path)
    if parameter_locations.path:
        yield f"            {path_representation}.format(**{{"
        name: str
        parameter: _Parameter
        for name, parameter in parameter_locations.path.items():
            yield _represent_dictionary_parameter(
                name, parameter, value_type="str"
            )
        yield "            }),"
    else:
        yield f"            {path_representation},"


def _represent_dictionary_parameter(
    name: str,
    parameter: _Parameter,
    *,
    use_kwargs: bool = False,
    multipart: bool = False,
    value_type: str = "",
) -> str:
    represent_style: str = sob.utilities.represent(parameter.style)
    parameter_name: str = parameter.name
    if parameter.style == "matrix":
        parameter_name = f";{parameter_name}"
    if use_kwargs:
        name = f'kwargs.get("{name}", None)'
    represent_multipart_argument: str = ""
    if multipart:
        represent_multipart_argument = "                    multipart=True,\n"

    return (
        f'                "{parameter_name}": '
        "{}oapi.client.format_argument_value(\n"
        f'                    "{parameter_name}",\n'
        f"                    {name},\n"
        f"                    style={represent_style},\n"
        f"                    explode={parameter.explode!r},\n"
        f"{represent_multipart_argument}"
        "                ){},"
    ).format(f"{value_type}(" if value_type else "", ")" if value_type else "")


def _iter_cookie_dictionary_parameter_representation(
    names_parameters: dict[str, _Parameter],
) -> collections.abc.Iterable[str]:
    if names_parameters:
        yield '                "Cookie": "; ".join(('
        name: str
        parameter: _Parameter
        for name, parameter in names_parameters.items():
            represent_style: str = sob.utilities.represent(parameter.style)
            represent_explode: str = sob.utilities.represent(parameter.explode)
            yield "                    oapi.client.urlencode({"
            yield f'                        "{parameter.name}":'
            yield "                        oapi.client.format_argument_value("
            yield f'                            "{parameter.name}",'
            yield f"                            {name},"
            yield f"                            style={represent_style},"
            yield f"                            explode={represent_explode}"
            yield "                        ),"
            yield "                    }),"
        yield "                ))"


def _iter_request_headers_representation(
    parameter_locations: _ParameterLocations, *, use_kwargs: bool = False
) -> collections.abc.Iterable[str]:
    if parameter_locations.header or parameter_locations.cookie:
        yield "            headers={"
        if parameter_locations.header:
            name: str
            parameter: _Parameter
            for name, parameter in parameter_locations.header.items():
                yield _represent_dictionary_parameter(
                    name, parameter, use_kwargs=use_kwargs
                )
        if parameter_locations.cookie:
            yield from _iter_cookie_dictionary_parameter_representation(
                parameter_locations.cookie
            )
        yield "            },"


def _iter_request_body_representation(
    parameter_locations: _ParameterLocations, *, use_kwargs: bool = False
) -> collections.abc.Iterable[str]:
    if parameter_locations.body:
        name: str = parameter_locations.body.name
        if use_kwargs:
            name = f'kwargs.get("{name}", None)'
        yield (f"            json={name},")


def _iter_request_query_representation(
    parameter_locations: _ParameterLocations, *, use_kwargs: bool = False
) -> collections.abc.Iterable[str]:
    if parameter_locations.query:
        yield "            query={"
        name: str
        parameter: _Parameter
        for name, parameter in parameter_locations.query.items():
            yield _represent_dictionary_parameter(
                name, parameter, use_kwargs=use_kwargs
            )
        yield "            },"


def _iter_request_form_data_representation(
    parameter_locations: _ParameterLocations,
    *,
    use_kwargs: bool = False,
) -> collections.abc.Iterable[str]:
    if parameter_locations.form_data:
        yield "            data={"
        name: str
        parameter: _Parameter
        for name, parameter in parameter_locations.form_data.items():
            yield _represent_dictionary_parameter(
                name,
                parameter,
                use_kwargs=use_kwargs,
                multipart=parameter_locations.multipart,
            )
        yield "            },"


def _strip_def_decorators(source: str) -> str:
    return re.sub(r"^(\s*)@(?:.|\n)*?(\bdef )", r"\1\2", source)


def get_default_method_name_from_path_method_operation(
    path: str, method: str, operation_id: str | None
) -> str:
    method_name: str
    if operation_id:
        method_name = sob.utilities.get_property_name(operation_id)
    else:
        part: str
        method_name = "{}_{}".format(
            method.lower(),
            "_".join(
                sob.utilities.get_property_name(part)
                for part in path.strip("/ ").split("/")
            ),
        )
    return method_name.rstrip("_")


class ClientModule:
    """
    This class parses an Open API document and outputs a module defining
    a client class for interfacing with the API described by an OpenAPI
    document.
    """

    def __init__(
        self,
        open_api: str | sob.abc.Readable | OpenAPI,
        model_path: str | Path,
        *,
        class_name: str = "Client",
        base_class: type[Client] = Client,
        imports: str | tuple[str, ...] = (),
        init_decorator: str = "",
        include_init_parameters: str | tuple[str, ...] = (),
        add_init_parameters: str | tuple[str, ...] = (),
        add_init_parameter_docs: str | tuple[str, ...] = (),
        init_parameter_defaults: collections.abc.Mapping[str, typing.Any]
        | collections.abc.Sequence[tuple[str, typing.Any]] = (),
        init_parameter_defaults_source: collections.abc.Mapping[
            str, typing.Any
        ]
        | collections.abc.Sequence[tuple[str, typing.Any]] = (),
        get_method_name_from_path_method_operation: typing.Callable[
            [str, str, str | None], str
        ] = get_default_method_name_from_path_method_operation,
        use_operation_id: bool = False,
    ) -> None:
        """
        Parameters:
            open_api: An OpenAPI document. This can be a URL, file-path, an
                HTTP response (`http.client.HTTPResponse`), a file object, or
                an instance of `oapi.oas.model.OpenAPI`.
            model_path: The file path where the data model for this
                client can be found. This must be a model generated using
                `oapi.model`, and must be part of the same project that this
                client will be saved into.
            class_name:
            base_class: The base class to use for the client. If provided,
                this must be a sub-class of `oapi.client.Client`.
            imports: One or more import statements to include
                (in addition to those generated automatically).
            init_decorator:  A decorator to apply to the client class
                `.__init__` method. If used, make sure to include any modules
                referenced in your `imports`. For example:
                "@decorator_function(argument_a=1, argument_b=2)".
            include_init_parameters: The name of all parameters to
                include for the client's `.__init__` method.
            add_init_parameters: Additional parameter
                declarations to add to the client's `.__init__` method.
                These should include a type hint and default value (not just
                the parameter name). For example:
                'additional_parameter_name: str | None = None'. Note:
                additional parameters will not do anything without the use of a
                decorator which utilizes the additional parameters, so use of
                this parameter should be accompanied by an `init_decorator`.
            add_init_parameter_docs:
            init_parameter_defaults: A mapping of
                parameter names to default values for the parameter.
            init_parameter_defaults_source: A mapping of
                parameter names to default values for the parameter *expressed
                as source code*. This is to allow for the passing of imported
                constants, expressions, etc.
        """
        message: str
        if isinstance(model_path, Path):
            model_path = str(model_path)
        # Ensure a valid model path has been provided
        if not os.path.exists(model_path):
            raise ValueError(model_path)
        # Get an OpenAPI document
        if isinstance(open_api, str):
            if os.path.exists(open_api):
                open_api = _get_path_open_api(open_api)
            else:
                open_api = _get_url_open_api(open_api)
        elif isinstance(open_api, sob.abc.Readable):
            open_api = _get_io_open_api(open_api)
        elif not isinstance(open_api, OpenAPI):
            message = (
                f"`{sob.utilities.get_calling_function_qualified_name()}` "
                "requires an instance of `str`, "
                f"`{sob.utilities.get_qualified_name(OpenAPI)}`, or a "
                "file-like object for the `open_api` parameter--not "
                f"{open_api!r}"
            )
            raise TypeError(message)
        # Ensure all elements have URLs and JSON pointers
        sob.set_model_url(open_api, sob.get_model_url(open_api))
        sob.set_model_pointer(open_api, sob.get_model_pointer(open_api) or "")
        self.open_api: OpenAPI = open_api
        init_decorator = init_decorator.strip()
        if init_decorator and not init_decorator.startswith("@"):
            raise ValueError(init_decorator)
        self._init_decorator: str = init_decorator.strip()
        self._include_init_parameters: tuple[str, ...] = (
            (include_init_parameters,)
            if isinstance(include_init_parameters, str)
            else include_init_parameters
        )
        self._add_init_parameters: tuple[str, ...] = (
            (add_init_parameters,)
            if isinstance(add_init_parameters, str)
            else add_init_parameters
        )
        self._add_init_parameter_docs: tuple[str, ...] = (
            (add_init_parameter_docs,)
            if isinstance(add_init_parameter_docs, str)
            else add_init_parameter_docs
        )
        self._init_parameter_defaults: dict[str, typing.Any] = dict(
            init_parameter_defaults
        )
        self._init_parameter_defaults_source: dict[str, typing.Any] = dict(
            init_parameter_defaults_source
        )
        self._resolver: Resolver = Resolver(open_api)
        self._model_path: str = model_path
        self._base_class: type[Client] = base_class
        self._class_name: str = class_name
        # This keeps track of used names in the global namespace
        self._names: set[str] = {
            "sob",
            "oapi",
            "typing",
            "Logger",
            self._class_name,
        }
        self._imports: set[str] = {
            "from __future__ import annotations",
            "import typing",
            "import oapi",
            "import sob",
            "from logging import Logger",
        } | set(
            filter(None, (imports,) if isinstance(imports, str) else imports)
        )
        if "headers" not in self._iter_excluded_parameter_names():
            # `collections.abc` is only referenced if `headers` is used
            self._imports.add("import collections.abc")
            self._names.add("collections")
        self.get_method_name_from_path_method_operation = (
            get_method_name_from_path_method_operation
        )
        self.use_operation_id = use_operation_id

    def _get_open_api_major_version(self) -> int:
        return int(
            (self.open_api.swagger or self.open_api.openapi or "0")
            .split(".")[0]
            .strip()
        )

    def _resolve_media_type(
        self, media_type: MediaType | Reference
    ) -> MediaType:
        if isinstance(media_type, Reference):
            resolved_media_type: sob.abc.Model = (
                self._resolver.resolve_reference(
                    media_type, types=(MediaType,)
                )
            )
            if not isinstance(resolved_media_type, MediaType):
                raise TypeError(resolved_media_type)
            media_type = resolved_media_type
        return media_type

    def _resolve_response(self, response: Response | Reference) -> Response:
        if isinstance(response, Reference):
            resolved_response: sob.abc.Model = (
                self._resolver.resolve_reference(response, types=(Response,))
            )
            if not isinstance(resolved_response, Response):
                raise TypeError(resolved_response)
            response = resolved_response
        return response

    def _resolve_parameter(
        self, parameter: Parameter | Reference
    ) -> Parameter:
        if isinstance(parameter, Reference):
            resolved_parameter: sob.abc.Model = (
                self._resolver.resolve_reference(parameter, types=(Parameter,))
            )
            if not isinstance(resolved_parameter, Parameter):
                raise TypeError(resolved_parameter)
            parameter = resolved_parameter
        return parameter

    def _resolve_schema(self, schema: Reference | Schema) -> Schema:
        if isinstance(schema, Reference):
            resolved_schema: sob.abc.Model = self._resolver.resolve_reference(
                schema, types=(Schema,)
            )
            if not isinstance(resolved_schema, Schema):
                raise TypeError(resolved_schema)
            schema = resolved_schema
        return schema

    def _resolve_operation(
        self, operation: Reference | Operation
    ) -> Operation:
        if isinstance(operation, Reference):
            resolved_operation: sob.abc.Model = (
                self._resolver.resolve_reference(operation, types=(Operation,))
            )
            if not isinstance(resolved_operation, Operation):
                raise TypeError(resolved_operation)
            operation = resolved_operation
        return operation

    def _resolve_path_item(self, path_item: Reference | PathItem) -> PathItem:
        if isinstance(path_item, Reference):
            resolved_path_item: sob.abc.Model = (
                self._resolver.resolve_reference(path_item, types=(PathItem,))
            )
            if not isinstance(resolved_path_item, PathItem):
                raise TypeError(resolved_path_item)
            path_item = resolved_path_item
        return path_item

    def _resolve_request_body(
        self, request_body: Reference | RequestBody
    ) -> RequestBody:
        if isinstance(request_body, Reference):
            resolved_request_body: sob.abc.Model = (
                self._resolver.resolve_reference(
                    request_body, types=(RequestBody,)
                )
            )
            if not isinstance(resolved_request_body, RequestBody):
                raise TypeError(resolved_request_body)
            request_body = resolved_request_body
        return request_body

    def _resolve_encoding(self, encoding: Reference | Encoding) -> Encoding:
        if isinstance(encoding, Reference):
            resolved_encoding: sob.abc.Model = (
                self._resolver.resolve_reference(encoding, types=(Encoding,))
            )
            if not isinstance(resolved_encoding, Encoding):
                raise TypeError(resolved_encoding)
            encoding = resolved_encoding
        return encoding

    @property  # type: ignore
    @_dict_str_model_lru_cache()
    def _pointers_classes(self) -> dict[str, type[sob.abc.Model]]:
        path: str = os.path.abspath(self._model_path)
        current_directory: str = os.path.abspath(os.curdir)
        namespace: dict[str, typing.Any] = {"__file__": path}
        os.chdir(os.path.dirname(path))
        try:
            with open(path) as module_io:
                exec(module_io.read(), namespace)  # noqa: S102
        finally:
            os.chdir(current_directory)
        return namespace.get("_POINTERS_CLASSES")  # type: ignore

    def _iter_imports(self) -> collections.abc.Iterable[str]:
        """
        Yield sorted import statements. This is used to ensure consistent
        output (no unwarranted diffs).
        """
        import_statement: str
        return sorted(
            self._imports,
            key=lambda import_statement: (
                (0, import_statement)
                if import_statement.startswith("from __future__")
                else (2, import_statement)
                if import_statement.startswith("from ")
                else (1, import_statement)
            ),
        )

    @_str_lru_cache()
    def _get_model_module_name(self) -> str:
        """
        Get a unique local name to use for the model module
        """
        self._get_client_base_class_name()
        model_module_name: str = os.path.basename(self._model_path).partition(
            "."
        )[0]
        while model_module_name in self._names:
            model_module_name = f"_{model_module_name}"
        self._names.add(model_module_name)
        return model_module_name

    def _get_model_module_import(self, client_module_path: str | Path) -> str:
        relative_import: str = _get_relative_module_import(
            self._model_path, client_module_path
        )
        model_module_name: str = self._get_model_module_name()
        if model_module_name != relative_import.rpartition(" ")[2]:
            relative_import = f"{relative_import} as {model_module_name}"
        return relative_import

    @_str_lru_cache()
    def _get_client_base_class_name(self) -> str:
        """
        Get a unique local name to use for the client base class
        """
        if self._base_class is Client:
            return f"{Client.__module__}.{Client.__name__}"
        base_class_name: str = self._base_class.__name__
        while base_class_name in self._names:
            base_class_name = f"_{base_class_name}"
        self._names.add(base_class_name)
        return base_class_name

    @_str_lru_cache()
    def _get_client_base_class_import(
        self, client_module_path: str | Path
    ) -> str:
        if self._base_class is Client:
            return ""
        base_class_name: str = self._get_client_base_class_name()
        as_: str = (
            ""
            if base_class_name == self._base_class.__name__
            else f" as {base_class_name}"
        )
        base_class_module: str = self._base_class.__module__
        if base_class_module in sys.modules:
            base_class_path: str = inspect.getfile(
                sys.modules[base_class_module]
            )
            try:
                relative_base_class_module: str = _get_relative_module_path(
                    base_class_path, client_module_path
                )
                # If these are in the same package, the relative module path
                # should be more succinct than the absolute module path
                if len(relative_base_class_module) < len(base_class_module):
                    base_class_module = relative_base_class_module
            except Exception:  # noqa: S110 BLE001
                pass
        return (
            f"from {base_class_module} "
            f"import {self._base_class.__name__}{as_}"
        )

    def _get_security_schemes(self) -> SecuritySchemes | None:
        return (
            self.open_api.security_definitions
            or self.open_api.components.security_schemes
            if self.open_api.components
            else None
        )

    def _iter_security_schemes(
        self,
    ) -> collections.abc.Iterable[SecurityScheme]:
        security_schemes: SecuritySchemes | None = self._get_security_schemes()
        yield from (security_schemes or {}).values()

    @_lru_cache()
    def _get_api_key_in(self) -> str:
        """
        Determine the location where an API key should be provided
        (header, query, or cookie) (see [API keys
        ](https://swagger.io/docs/specification/v3_0/authentication/api-keys/)
        ).
        """
        security_scheme: SecurityScheme
        for security_scheme in self._iter_security_schemes():
            # Use the first API key security scheme which has a name
            # (as without a name the scheme is effectively moot)
            if security_scheme.type_ == "apiKey" and security_scheme.name:
                return security_scheme.in_ or "header"
        return "header"

    @_lru_cache()
    def _get_api_key_name(self) -> str:
        """
        Determine the name for the header, cookie parameter, or query parameter
        where an API key should be provided (see [API keys
        ](https://swagger.io/docs/specification/v3_0/authentication/api-keys/)
        ).
        """
        security_scheme: SecurityScheme
        for security_scheme in self._iter_security_schemes():
            # Use the first API key security scheme
            if security_scheme.type_ == "apiKey" and security_scheme.name:
                return security_scheme.name
        return "X-API-KEY"

    def _iter_oauth2_flows(
        self,
    ) -> collections.abc.Iterable[tuple[str, OAuthFlow | None]]:
        security_scheme: SecurityScheme
        for security_scheme in self._iter_security_schemes():
            # Use the first API key security scheme
            if security_scheme.type_ == "oauth2":
                if security_scheme.flows:
                    yield from filter(
                        None,
                        sob.utilities.iter_properties_values(
                            security_scheme.flows
                        ),
                    )
                if security_scheme.flow:
                    yield (
                        (
                            "authorizationCode"
                            if security_scheme.flow == "accessCode"
                            else (
                                "clientCredentials"
                                if security_scheme.flow == "application"
                                else security_scheme.flow
                            )
                        ),
                        None,
                    )

    @_lru_cache()
    def _get_oauth2_authorization_url(self) -> str:
        """
        Get the OAuth2 authorization URL, if one is provided
        (see [OAuth 2
        ](https://swagger.io/docs/specification/v3_0/authentication/oauth2/)).
        """
        name: str
        flow: OAuthFlow | None
        for _name, flow in self._iter_oauth2_flows():
            if flow and flow.authorization_url:
                return flow.authorization_url
        security_scheme: SecurityScheme
        # OpenAPI 2x compatibility
        for security_scheme in self._iter_security_schemes():
            if security_scheme.authorization_url:
                return security_scheme.authorization_url
        return ""

    @_lru_cache()
    def _get_oauth2_token_url(self) -> str:
        """
        Get the OAuth2 token URL, if one is provided
        (see [OAuth 2
        ](https://swagger.io/docs/specification/v3_0/authentication/oauth2/)).
        """
        name: str
        flow: OAuthFlow | None
        for _name, flow in self._iter_oauth2_flows():
            if flow and flow.token_url:
                return flow.token_url
        # OpenAPI 2x compatibility
        for security_scheme in self._iter_security_schemes():
            if security_scheme.token_url:
                return security_scheme.token_url
        return ""

    @_lru_cache()
    def _get_oauth2_refresh_url(self) -> str:
        """
        Get the OAuth2 refresh URL, if one is provided
        (see [OAuth 2
        ](https://swagger.io/docs/specification/v3_0/authentication/oauth2/)).
        """
        name: str
        flow: OAuthFlow | None
        for _name, flow in self._iter_oauth2_flows():
            if flow and flow.refresh_url:
                return flow.refresh_url
        return ""

    @_lru_cache()
    def _get_oauth2_flow_names(self) -> tuple[str, ...]:
        """
        Get a `tuple` of [supported OAuth2 flow names
        ](https://swagger.io/docs/specification/v3_0/authentication/oauth2/).
        """
        item: tuple[str, OAuthFlow | None]
        return tuple(
            sorted(
                iter_distinct(item[0] for item in self._iter_oauth2_flows())
            )
        )

    @_lru_cache()
    def _get_open_id_connect_url(self) -> str:
        """
        Get the OpenID Connect URL, if one is provided (see [OAuth 2
        ](https://swagger.io/docs/specification/v3_0/authentication/oauth2/)).
        """
        security_scheme: SecurityScheme
        for security_scheme in self._iter_security_schemes():
            if security_scheme.open_id_connect_url:
                return security_scheme.open_id_connect_url
        return ""

    def _iter_class_init_docstring_source(
        self,
    ) -> collections.abc.Iterable[str]:
        message: str
        if Client.__init__.__doc__:
            docstring: str = Client.__init__.__doc__
            if self._include_init_parameters:
                matched: Match | None = re.match(
                    (
                        r"^((?:.|\n)*?\n        Parameters:\n)"
                        r"((?:.|\n)*?)(\n+        (?:[^ ](?:.|\n)*)?)$"
                    ),
                    docstring,
                )
                if not matched:
                    raise ValueError(docstring)
                prefix: str
                parameter_documentation: str
                suffix: str
                prefix, parameter_documentation, suffix = matched.groups()
                parameter_name: str
                for parameter_name in self._iter_excluded_parameter_names():
                    pattern: str = (
                        f"\\n            {parameter_name}:(?:.|\\n)*?"
                        r"(\n            (?=[^\s])|(\n|\s)*$)"
                    )
                    if not re.search(pattern, parameter_documentation):
                        message = (
                            f"The pattern `{pattern!r}` was not found in "
                            "the parameter documentation:\n"
                            f"{parameter_documentation}"
                        )
                        raise ValueError(message)
                    parameter_documentation = re.sub(
                        pattern, r"\1", parameter_documentation
                    )
                parameter_doc: str
                for parameter_doc in self._add_init_parameter_docs:
                    parameter_doc = sob.utilities.indent(  # noqa: PLW2901
                        parameter_doc.lstrip(" "), number_of_spaces=16, start=0
                    )
                    parameter_doc = (  # noqa: PLW2901
                        sob.utilities.split_long_docstring_lines(parameter_doc)
                    ).lstrip()
                    parameter_documentation = (
                        f"{parameter_documentation}"
                        f"\n            {parameter_doc}"
                    )
                yield (
                    f'        """{prefix}{parameter_documentation}'
                    f'{suffix or ""}"""'
                )
            else:
                yield f'        """{docstring}"""'
            yield ""

    def _iter_class_declaration_source(self) -> collections.abc.Iterable[str]:
        class_declaration: str = (
            f"class {self._class_name}"
            f"({self._get_client_base_class_name()}):"
        )
        if len(class_declaration) > sob.utilities.MAX_LINE_LENGTH:
            class_declaration = (
                f"class {self._class_name}(\n"
                f"    {self._get_client_base_class_name()}\n"
                "):"
            )
        yield class_declaration
        yield ""

    def _get_schema_class(
        self, schema: Schema | Parameter
    ) -> type[sob.abc.Model]:
        relative_url: str = self._resolver.get_relative_url(
            sob.get_model_url(schema) or ""
        )
        pointer: str = (sob.get_model_pointer(schema) or "").lstrip("#")
        relative_url_pointer: str = f"{relative_url}#{pointer}"
        try:
            return self._pointers_classes[relative_url_pointer]
        except KeyError:
            if schema.type_ == "object" or (
                isinstance(schema, Schema)
                and (schema.properties or schema.additional_properties)
            ):
                return sob.Dictionary
            if schema.type_ == "array" or schema.items:
                return sob.Array
            raise

    def _get_schema_type(
        self,
        schema: Schema | Parameter,
        default_type: type[sob.abc.Property] = sob.Property,
    ) -> type[sob.abc.Model] | sob.abc.Property:
        try:
            return self._get_schema_class(schema)
        except KeyError:
            if schema.type_ == "object" or (
                isinstance(schema, Schema)
                and schema.type_ is None
                and (schema.properties or schema.additional_properties)
            ):
                return sob.Dictionary
            if schema.type_ == "array" or (
                (schema.type_ is None) and schema.items
            ):
                return sob.Array
            if schema.type_ == "number":
                self._names.add("decimal")
                self._imports.add("import decimal")
            return get_type_format_property(
                type_=schema.type_,
                format_=schema.format_,
                content_media_type=(
                    schema.content_media_type
                    if isinstance(schema, Schema)
                    else None
                ),
                content_encoding=(
                    schema.content_encoding
                    if isinstance(schema, Schema)
                    else None
                ),
                default_type=default_type,
            )

    def _iter_schema_types(
        self,
        schema: Schema,
        default_type: type[sob.abc.Property] = sob.Property,
    ) -> collections.abc.Iterable[type[sob.abc.Model] | sob.abc.Property]:
        if schema.any_of or schema.one_of:
            schema_: Reference | Schema
            if schema.any_of:
                for schema_ in schema.any_of:
                    schema_ = self._resolve_schema(schema_)  # noqa: PLW2901
                    yield from self._iter_schema_types(
                        schema_, default_type=default_type
                    )
            if schema.one_of:
                for schema_ in schema.one_of:
                    schema_ = self._resolve_schema(schema_)  # noqa: PLW2901
                    yield from self._iter_schema_types(
                        schema_, default_type=default_type
                    )
        else:
            yield self._get_schema_type(schema, default_type=default_type)

    def _get_parameter_or_schema_type(
        self,
        schema: Schema | Parameter,
        default_type: type[sob.abc.Property] = sob.Property,
    ) -> type[sob.abc.Model] | sob.abc.Property:
        if isinstance(schema, Parameter):
            if schema.schema:
                return self._get_parameter_or_schema_type(
                    self._resolve_schema(schema.schema),
                    default_type=default_type,
                )
            if schema.content:
                media_type: MediaType = next(  # type: ignore
                    iter(schema.content.values())
                )
                if media_type.schema:
                    return self._get_parameter_or_schema_type(
                        self._resolve_schema(media_type.schema),
                        default_type=sob.BytesProperty,
                    )
        return self._get_schema_type(schema, default_type=default_type)

    def _iter_response_types(
        self, response: Response
    ) -> collections.abc.Iterable[type[sob.abc.Model] | sob.abc.Property]:
        schema: Schema
        resolved_schema: sob.abc.Model
        if response.schema:
            schema = self._resolve_schema(response.schema)
            yield from self._iter_schema_types(
                schema, default_type=sob.BytesProperty
            )
        if response.content:
            media_type_name: str
            media_type: MediaType | Reference
            for media_type in response.content.values():
                media_type = self._resolve_media_type(  # noqa: PLW2901
                    media_type
                )
                if media_type.schema is not None:
                    schema = self._resolve_schema(media_type.schema)
                    yield from self._iter_schema_types(
                        schema, default_type=sob.BytesProperty
                    )

    def _iter_operation_response_types(
        self, operation: Operation
    ) -> collections.abc.Iterable[type[sob.abc.Model] | sob.abc.Property]:
        """
        Yield classes for all responses with a status code in the 200-299 range
        """
        if operation.responses:
            code: str
            response: Response | Reference
            for code, response in operation.responses.items():
                if code.startswith("2"):
                    yield from self._iter_response_types(
                        self._resolve_response(response)
                    )

    def _iter_type_types_names(
        self, type_: sob.abc.Property
    ) -> collections.abc.Iterable[str]:
        if type_.types:
            yield from chain(*map(self._iter_type_names, type_.types))
        else:
            yield "typing.Any"

    def _iter_enumerated_type_names(
        self, type_: sob.abc.EnumeratedProperty
    ) -> collections.abc.Iterable[str]:
        if type_.types:
            yield from chain(*map(self._iter_type_names, type_.types))
        elif type_.values:
            yield from chain(
                *map(self._iter_type_names, map(type, type_.values))
            )
        else:
            yield "typing.Any"

    def _iter_type_names(  # noqa: C901
        self, type_: type | sob.abc.Property
    ) -> collections.abc.Iterable[str]:
        if isinstance(type_, sob.abc.EnumeratedProperty):
            yield from self._iter_enumerated_type_names(type_)
        elif isinstance(type_, sob.abc.NumberProperty) or (
            isinstance(type_, type)
            and issubclass(type_, (decimal.Decimal, float, int))
        ):
            self._imports.add("import decimal")
            self._names.add("decimal")
            yield from ("int", "float", "decimal.Decimal")
        elif isinstance(type_, sob.abc.StringProperty) or (
            isinstance(type_, type) and issubclass(type_, str)
        ):
            yield "str"
        elif isinstance(type_, sob.abc.DateTimeProperty) or (
            isinstance(type_, type) and issubclass(type_, datetime)
        ):
            self._imports.add("import datetime")
            yield "datetime.datetime"
        elif isinstance(type_, sob.abc.DateProperty) or (
            isinstance(type_, type) and issubclass(type_, date)
        ):
            self._imports.add("import datetime")
            yield "datetime.date"
        elif isinstance(type_, sob.abc.IntegerProperty) or (
            isinstance(type_, type) and issubclass(type_, int)
        ):
            yield "int"
        elif isinstance(type_, sob.abc.BooleanProperty) or (
            isinstance(type_, type) and issubclass(type_, bool)
        ):
            yield "bool"
        elif isinstance(type_, sob.abc.BytesProperty) or (
            isinstance(type_, type) and issubclass(type_, bytes)
        ):
            yield "typing.IO[bytes] | bytes"
        elif isinstance(type_, sob.abc.Property):
            yield from self._iter_type_types_names(type_)
        else:
            if not isinstance(type_, type) and issubclass(
                type_, sob.abc.Model
            ):
                raise TypeError(type_)
            model_module_name: str = (
                "sob.abc"
                if type_.__module__ in ("sob.model", "sob.abc", "sob")
                else self._get_model_module_name()
            )
            yield f"{model_module_name}.{type_.__name__}"

    def _iter_schema_type_names(
        self,
        schema: Schema | Parameter,
        default_type: type[sob.abc.Property] = sob.Property,
    ) -> collections.abc.Iterable[str]:
        yield from self._iter_type_names(
            self._get_parameter_or_schema_type(
                schema,
                default_type=default_type,
            )
        )

    def _get_schema_type_hint(
        self,
        schema: Schema | Parameter,
        *,
        required: bool = False,
        default_type: type[sob.abc.Property] = sob.Property,
    ) -> str:
        type_names: tuple[str, ...] = tuple(
            self._iter_schema_type_names(schema, default_type=default_type)
        )
        if not type_names:
            raise ValueError(schema)
        type_hint: str
        if not required:
            type_names += ("None",)
        if all(map(functools.partial(hasattr, builtins), type_names)):
            type_hint = " | ".join(type_names)
        else:
            type_hint = "(\n            {}\n        )".format(
                "\n            | ".join(type_names)
            )
        if not required:
            type_hint = f"{type_hint} = None"
        return type_hint

    def _get_parameter_type_hint(self, parameter: Parameter) -> str:
        schema: Parameter | Schema = parameter
        if parameter.schema:
            schema = self._resolve_schema(parameter.schema)
        return self._get_schema_type_hint(
            schema,
            required=parameter.required or False,
            default_type=sob.BytesProperty,
        )

    def _iter_parameter_method_source(  # noqa: C901
        self,
        parameter: Parameter,
        parameter_locations: _ParameterLocations,
        parameter_names: set[str] | None = None,
        content_type: str = "",
        headers: collections.abc.Mapping[str, Header | Reference]
        | None = None,
    ) -> collections.abc.Iterable[str]:
        """
        Yield lines for a parameter declaration.
        """
        message: str
        if (
            parameter.name
            and parameter.in_
            and not (
                (
                    parameter.in_ == "header"
                    and parameter.name.lower()
                    in (
                        # See:
                        # https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#parameter-object
                        "accept",
                        "content-type",
                        "authorization",
                    )
                )
                # Skip API key parameter definitions, as these
                # should not be included in the method parameters
                or (
                    parameter.in_ in ("header", "query", "cookie")
                    and parameter.name.lower()
                    == self._get_api_key_name().lower()
                )
            )
        ):
            parameter_name: str = sob.utilities.get_property_name(
                parameter.name
            ).rstrip("_")
            # If a set of parameter names was provided, make sure
            # this one does not duplicate any
            if parameter_names is not None:
                while parameter_name in parameter_names:
                    parameter_name = f"{parameter_name}_"
                parameter_names.add(parameter_name)
            # See:
            # https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#fixed-fields-for-use-with-schema
            style: str = parameter.style or (
                "form"
                if (
                    parameter.in_ in ("query", "cookie")
                    # OpenAPI 2x compatibility
                    or (
                        parameter.collection_format == "multi"
                        and parameter.in_ in ("query", "formData")
                    )
                )
                else ("simple" if parameter.in_ in ("path", "header") else "")
            )
            explode: bool = (
                (
                    bool(
                        style in ("form", "deepObject")
                        # OpenAPI 2x compatibility
                        or parameter.collection_format == "multi"
                    )
                )
                if parameter.explode is None
                else parameter.explode
            )
            # OpenAPI 2x compatibility
            if parameter.collection_format == "ssv":
                style = "spaceDelimited"
                explode = False
            elif parameter.collection_format == "pipe":
                style = "pipeDelimited"
                explode = False
            elif parameter.collection_format == "multi":
                style = "form"
                explode = True
            elif parameter.collection_format == "csv" or (
                parameter.collection_format is None
                and self._get_open_api_major_version() == 2  # noqa: PLR2004
            ):
                style = "form"
                explode = False
            parameter_: _Parameter = _Parameter(
                name=parameter.name,
                types=sob.types.Types(
                    [self._get_parameter_or_schema_type(parameter)]
                ),
                # See:
                # https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#fixed-fields-for-use-with-schema
                explode=explode,
                style=style,
                description=parameter.description or "",
                index=parameter_locations.total_count,
                content_type=content_type,
            )
            if headers:
                parameter_.headers = headers
            parameter_in: str = sob.utilities.get_property_name(parameter.in_)
            if parameter_in == "body":
                if parameter_locations.body is not None:
                    message = 'Only one "body" parameter is permitted'
                    raise ValueError(message)
                parameter_.name = parameter_name
                parameter_locations.body = parameter_
            else:
                getattr(
                    parameter_locations,
                    parameter_in,
                )[parameter_name] = parameter_
            parameter_locations.total_count += 1
            type_hint: str = self._get_parameter_type_hint(parameter)
            yield f"        {parameter_name}: {type_hint},"

    def _represent_type(
        self, type_: type[sob.abc.Model] | sob.abc.Property
    ) -> str:
        if isinstance(type_, sob.abc.Property):
            return sob.utilities.represent(type_)
        if not (isinstance(type_, type) and issubclass(type_, sob.abc.Model)):
            raise TypeError(type_)
        if type_.__module__.startswith("sob.") or type_.__module__ == "sob":
            return f"{type_.__module__}.{type_.__name__}"
        return f"{self._get_model_module_name()}.{type_.__name__}"

    def _iter_operation_method_definition(
        self,
        path: str,
        method: str,
        operation: Operation,
        parameter_locations: _ParameterLocations,
    ) -> collections.abc.Iterable[str]:
        operation_response_types: tuple[
            type[sob.abc.Model] | sob.abc.Property, ...
        ] = tuple(self._iter_operation_response_types(operation))
        if operation_response_types:
            yield "        response: sob.abc.Readable = self.request("
        else:
            yield "        self.request("
        yield from _iter_request_path_representation(path, parameter_locations)
        yield f'            method="{method.upper()}",'
        # If more than 254 arguments are needed, we must use `**kwargs``
        use_kwargs: bool = (
            len(tuple(_iter_parameters(parameter_locations))) > 254  # noqa: PLR2004
        )
        yield from _iter_request_headers_representation(
            parameter_locations, use_kwargs=use_kwargs
        )
        yield from _iter_request_query_representation(
            parameter_locations, use_kwargs=use_kwargs
        )
        yield from _iter_request_form_data_representation(
            parameter_locations,
            use_kwargs=use_kwargs,
        )
        yield from _iter_request_body_representation(
            parameter_locations, use_kwargs=use_kwargs
        )
        if parameter_locations.multipart:
            yield "            multipart=True,"
        yield "        )"
        if operation_response_types:
            response_types_representation: str = ",\n                ".join(
                iter_distinct(
                    map(self._represent_type, operation_response_types)
                )
            )
            yield "        return sob.unmarshal(  # type: ignore"
            yield "            sob.deserialize(response),"
            yield "            types=("
            yield f"                {response_types_representation},"
            yield "            )"
            yield "        )"
        yield ""

    def _iter_operation_method_docstring(
        self, operation: Operation, parameter_locations: _ParameterLocations
    ) -> collections.abc.Iterable[str]:
        yield '        """'
        if operation.description or operation.summary:
            yield sob.utilities.split_long_docstring_lines(
                "\n{}        ".format(
                    sob.utilities.indent(
                        (
                            operation.description or operation.summary or ""
                        ).strip(),
                        number_of_spaces=8,
                        start=0,
                    )
                )
            ).lstrip("\n")
        sorted_parameters: tuple[tuple[str, _Parameter], ...] = tuple(
            _iter_sorted_parameters(parameter_locations)
        )
        if sorted_parameters:
            if operation.description or operation.summary:
                yield ""
            yield "        Parameters:"
            name: str
            parameter: _Parameter
            for name, parameter in sorted_parameters:
                parameter_docstring: str
                if parameter.description:
                    description: str = re.sub(
                        r"\n[\s\n]*\n+", "\n", parameter.description.strip()
                    )
                    parameter_docstring = (
                        sob.utilities.split_long_docstring_lines(
                            sob.utilities.indent(
                                f"{name}: {description}", 16, start=0
                            )
                        )[4:]
                    )
                else:
                    parameter_docstring = f"            {name}:"
                yield parameter_docstring
        yield '        """'

    def _iter_operation_method_source(
        self,
        path: str,
        method: str,
        operation: Operation,
        path_item: PathItem,
    ) -> collections.abc.Iterable[str]:
        # This dictionary will be passed to
        # `self._iter_operation_method_declaration()`
        # in order to capture information about the parameters
        parameter_locations: _ParameterLocations = _ParameterLocations()
        operation_method_declaration: tuple[str, ...] = tuple(
            self._iter_operation_method_declaration(
                path=path,
                method=method,
                operation=operation,
                path_item=path_item,
                parameter_locations=parameter_locations,
            )
        )
        # Functions can only have up to 255 arguments
        # (one is taken by `self`, but 4 lines are not arguments)
        if len(operation_method_declaration) > 258:  # noqa: PLR2004
            try:
                star_index: int = operation_method_declaration.index(
                    "        *,"
                )
                yield from operation_method_declaration[:star_index]
            except ValueError:
                yield from operation_method_declaration[:2]
            yield "        **kwargs: typing.Any,"
            yield operation_method_declaration[-1]
        else:
            yield from operation_method_declaration
        yield from self._iter_operation_method_docstring(
            operation, parameter_locations
        )
        yield from self._iter_operation_method_definition(
            path=path,
            method=method,
            operation=operation,
            parameter_locations=parameter_locations,
        )

    def _get_request_body_json_parameter_source(
        self,
        media_type: MediaType,
        *,
        parameter_locations: _ParameterLocations,
        parameter_names: set[str],
        required: bool = False,
    ) -> str:
        message: str
        type_hint: str
        if not media_type.schema:
            message = f"Media type missing schema: {media_type}"
            raise ValueError(message)
        schema = self._resolve_schema(media_type.schema)
        schema_type: type[sob.abc.Model] | sob.abc.Property = (
            self._get_parameter_or_schema_type(schema)
        )
        parameter_name: str
        if isinstance(schema_type, type):
            parameter_name = sob.utilities.get_property_name(
                schema_type.__name__
            )
            # Ensure the parameter name is unique
            while parameter_name in parameter_names:
                parameter_name = f"{parameter_name}_"
            parameter_names.add(parameter_name)
        else:
            parameter_name = "data_"
        parameter_locations.body = _Parameter(
            name=parameter_name,
            types=sob.types.Types([schema_type]),
            index=parameter_locations.total_count,
            description=schema.description or "",
        )
        parameter_locations.total_count += 1
        type_hint = self._get_schema_type_hint(schema, required=required)
        return f"        {parameter_name}: {type_hint},"

    def _iter_request_body_form_parameters_source(  # noqa: C901
        self,
        media_type: MediaType,
        *,
        parameter_locations: _ParameterLocations,
        parameter_names: set[str],
        required: bool = False,
    ) -> collections.abc.Iterable[str]:
        message: str
        if not media_type.schema:
            message = f"Media type missing schema: {media_type}"
            raise ValueError(message)
        schema = self._resolve_schema(media_type.schema)
        # Form data parameters cannot be open-ended
        if (not schema.properties) or schema.additional_properties:
            message = "Form data parameters cannot be open-ended: " f"{schema}"
            raise ValueError(message)
        properties: Properties = schema.properties
        # Get parameter encodings
        encoding: Reference | Encoding | None
        parameters_encodings: dict[str, Encoding] = {}
        if media_type.encoding:
            name: str
            for name, encoding in media_type.encoding.items():
                if name not in properties:
                    message = (
                        f"Encoding {name} not in properties: {properties!r}"
                    )
                    raise ValueError(message)
                parameters_encodings[name] = self._resolve_encoding(encoding)
        # Create a parameter for each property
        key: str
        property_schema: Reference | Schema
        for key, property_schema in properties.items():
            property_schema = self._resolve_schema(  # noqa: PLW2901
                property_schema
            )
            parameter: Parameter = Parameter(
                name=key,
                in_="formData",
                schema=property_schema,
                required=required,
                description=property_schema.description or "",
                style="form",
                explode=True,
            )
            encoding = parameters_encodings.get(key)
            kwargs: dict[
                str, str | collections.abc.Mapping[str, Header | Reference]
            ] = {}
            if property_schema.content_media_type:
                kwargs.update(content_type=property_schema.content_media_type)
            if encoding:
                encoding = self._resolve_encoding(encoding)
                if encoding.explode is not None:
                    parameter.explode = encoding.explode
                if encoding.style is not None:
                    parameter.style = encoding.style
                if encoding.content_type:
                    kwargs.update(content_type=encoding.content_type)
                if encoding.headers:
                    kwargs.update(headers=encoding.headers)
            yield from self._iter_parameter_method_source(
                parameter,
                parameter_locations=parameter_locations,
                parameter_names=parameter_names,
                **kwargs,  # type: ignore
            )

    def _iter_request_body_parameters_source(
        self,
        request_body: RequestBody,
        parameter_locations: _ParameterLocations,
        parameter_names: set[str],
    ) -> collections.abc.Iterable[str]:
        media_type: MediaType
        media_type_name: str
        required: bool = bool(request_body.required)
        if request_body.content:
            for media_type_name, media_type in request_body.content.items():
                if media_type_name == "application/json":
                    yield self._get_request_body_json_parameter_source(
                        media_type,
                        parameter_locations=parameter_locations,
                        parameter_names=parameter_names,
                        required=required,
                    )
                elif (
                    media_type_name.startswith("multipart")
                    or media_type_name == "application/x-www-form-urlencoded"
                ):
                    if media_type_name.startswith("multipart"):
                        parameter_locations.multipart = True
                    try:
                        yield from (
                            self._iter_request_body_form_parameters_source(
                                media_type,
                                parameter_locations=parameter_locations,
                                parameter_names=parameter_names,
                                required=required,
                            )
                        )
                    except Exception as error:
                        sob.errors.append_exception_text(
                            error,
                            "\nErrors were encountered while generating "
                            "form parameters for media type: "
                            f"{media_type_name}",
                        )
                        raise
                else:
                    raise NotImplementedError(media_type_name)

    def _get_parameter_name(self, parameter: Parameter | Reference) -> str:
        resolved_parameter: Parameter = self._resolve_parameter(parameter)
        return resolved_parameter.name or ""

    def _get_operation_response_type_hint(self, operation: Operation) -> str:
        response_type_hint: str = "None"
        response_types: tuple[type[sob.abc.Model] | sob.abc.Property, ...] = (
            tuple(self._iter_operation_response_types(operation))
        )
        if response_types:
            response_type_names: tuple[str, ...] = tuple(
                iter_distinct(
                    chain(*map(self._iter_type_names, response_types))
                )
            )
            if not response_type_names:
                raise ValueError(response_types)
            if len(response_type_names) > 1:
                response_class_names: str = "        | ".join(
                    response_type_names
                )
                response_type_hint = (
                    f"(\n        {response_class_names}\n    )"
                )
            else:
                response_type_hint = response_type_names[0]
        return response_type_hint

    def _iter_operation_method_declaration(
        self,
        path: str,
        method: str,
        operation: Operation,
        path_item: PathItem,
        parameter_locations: _ParameterLocations,
    ) -> collections.abc.Iterable[str]:
        parameter: Parameter
        previous_parameter_required: bool = True
        method_name: str = self.get_method_name_from_path_method_operation(
            path,
            method,
            (operation.operation_id if self.use_operation_id else None),
        )
        yield f"    def {method_name}("
        yield "        self,"
        # Request Body
        request_body: RequestBody | None = None
        parameter_names: set[str] = set(
            map(
                sob.utilities.get_property_name,
                filter(
                    None,
                    map(
                        self._get_parameter_name,
                        chain(
                            operation.parameters or (),
                            path_item.parameters or (),
                        ),
                    ),
                ),
            )
        )
        if operation.request_body:
            request_body = self._resolve_request_body(operation.request_body)
            if request_body.required:
                yield from self._iter_request_body_parameters_source(
                    request_body,
                    parameter_locations=parameter_locations,
                    parameter_names=parameter_names,
                )
        # Parameters
        if operation.parameters or path_item.parameters:
            # We keep track of traversed parameter names to avoid doubling
            # up if the same parameter is defined for the path item and
            # the operation
            traversed_parameters: set[str] = set()
            for parameter in sorted(
                map(
                    self._resolve_parameter,
                    chain(
                        operation.parameters or (), path_item.parameters or ()
                    ),
                ),
                key=lambda parameter: 0 if parameter.required else 1,
            ):
                if not parameter.name:
                    raise ValueError(parameter)
                if parameter.name not in traversed_parameters:
                    parameter_method_source: tuple[str, ...] = tuple(
                        self._iter_parameter_method_source(
                            parameter,
                            parameter_locations=parameter_locations,
                        )
                    )
                    if (
                        parameter_method_source
                        and previous_parameter_required
                        and not parameter.required
                    ):
                        yield "        *,"
                    yield from parameter_method_source
                    traversed_parameters.add(parameter.name)
                    previous_parameter_required = bool(parameter.required)
        # If the request body is not *required*, yield it last instead of first
        if request_body and not request_body.required:
            if previous_parameter_required:
                yield "        *,"
            yield from self._iter_request_body_parameters_source(
                request_body,
                parameter_locations=parameter_locations,
                parameter_names=parameter_names,
            )
        # Response type hint
        response_type_hint: str = self._get_operation_response_type_hint(
            operation
        )
        yield f"    ) -> {response_type_hint}:"

    def _iter_path_methods_source(
        self, path: str, path_item: PathItem
    ) -> collections.abc.Iterable[str]:
        name: str
        operation: Operation | Reference
        for name, operation in _iter_path_item_operations(path_item):
            try:
                yield from self._iter_operation_method_source(
                    path,
                    name,
                    self._resolve_operation(operation),
                    path_item=path_item,
                )
            except Exception as error:
                sob.errors.append_exception_text(
                    error,
                    "\nErrors were encountered while generating a method "
                    f"for the operation: {name}",
                )
                raise

    def _iter_excluded_parameter_names(self) -> collections.abc.Iterable[str]:
        if self._include_init_parameters:
            parameter_name: str
            for parameter_name in inspect.signature(
                Client.__init__
            ).parameters:
                if parameter_name != "self" and (
                    parameter_name not in self._include_init_parameters
                ):
                    yield parameter_name

    def _remove_unused_init_parameters(
        self, init_declaration_source: str
    ) -> str:
        parameter_name: str
        for parameter_name in self._iter_excluded_parameter_names():
            init_declaration_source = re.sub(
                (
                    f"\\n\\s*{parameter_name}:(?:.|\\n)*?"
                    r"(\n\s*(?:[\w_]+|\)):)"
                ),
                r"\1",
                init_declaration_source,
            )
        return init_declaration_source

    def _replace_init_parameter_defaults(
        self, init_declaration_source: str
    ) -> str:
        # Infer some defaults from the spec, if no explicit default is
        # provided for the same parameter
        default_value: typing.Any
        parameter_name: str
        for parameter_name, default_value in (
            ("oauth2_authorization_url", self._get_oauth2_authorization_url()),
            ("oauth2_token_url", self._get_oauth2_token_url()),
            ("oauth2_refresh_url", self._get_oauth2_refresh_url()),
            ("oauth2_flows", self._get_oauth2_flow_names()),
            ("open_id_connect_url", self._get_open_id_connect_url()),
            ("api_key_in", self._get_api_key_in()),
            ("api_key_name", self._get_api_key_name()),
        ):
            if default_value and (
                parameter_name not in self._init_parameter_defaults
            ):
                self._init_parameter_defaults[parameter_name] = default_value
        default_representation: str
        item: tuple[str, typing.Any]
        for parameter_name, default_representation in chain(
            (
                (
                    item[0],
                    sob.utilities.represent(item[1]),
                )
                for item in filter(
                    _item_is_not_empty,
                    self._init_parameter_defaults.items(),
                )
            ),
            self._init_parameter_defaults_source.items(),
        ):
            pattern: Pattern = re.compile(
                f"(\\n\\s*{parameter_name}:"
                r"(?:.|\n)*?=\s*)((?:.|\n)*?)"
                r"(,?\n\s*(?:[\w_]+|\)):)"
            )
            matched: Match | None = pattern.search(init_declaration_source)
            if matched:
                if (
                    sum(map(len, matched.groups()[:-1]))
                    # Characters needed for the default value
                    + len(default_representation)
                    # Characters needed for the assignment operator
                    + (3 if parameter_name == "url" else 0)
                ) > sob.utilities.MAX_LINE_LENGTH:
                    default_representation = (  # noqa: PLW2901
                        sob.utilities.indent(
                            default_representation,
                            number_of_spaces=12,
                            start=0,
                        )
                    )
                    default_representation = (  # noqa: PLW2901
                        f"(\n{default_representation}\n        )"
                    )
                else:
                    default_representation = (  # noqa: PLW2901
                        sob.utilities.indent(
                            default_representation, number_of_spaces=8
                        )
                    )
                init_declaration_source = pattern.sub(
                    f"\\g<1>{default_representation}\\g<3>",
                    init_declaration_source,
                )
        return init_declaration_source

    def _insert_add_init_parameters(self, init_source: str) -> str:
        if self._add_init_parameters:
            if "\n    ) -> None:" not in init_source:
                raise ValueError(init_source)
            partitions: tuple[str, str, str] = init_source.rpartition(
                "\n    ) -> None:"
            )
            parameter_declaration: str
            init_source = "".join(
                chain(
                    partitions[:1],
                    (
                        (
                            "\n        {},".format(
                                parameter_declaration.lstrip().rstrip(" ,\n")
                            )
                        )
                        for parameter_declaration in self._add_init_parameters
                    ),
                    partitions[1:],
                )
            )
        return init_source

    def _resolve_source_namespace_discrepancies(self, source: str) -> str:
        return re.sub(
            (
                r'(?:"|\b)('
                "SSLContext|default_retry_hook|DEFAULT_RETRY_FOR_EXCEPTIONS|"
                "DEFAULT_RETRY_FOR_ERRORS|Client"
                r')(?:"|\b)'
            ),
            r"oapi.client.\1",
            source.replace("  # Force line-break retention\n", "\n"),
        )

    def _iter_init_method_source(self) -> collections.abc.Iterable[str]:
        if self._init_decorator:
            yield sob.utilities.indent(self._init_decorator, start=0)
        # Resolve namespace discrepancies between `oap.client` and the
        # generated client module
        init_declaration_source: str = (
            self._resolve_source_namespace_discrepancies(
                _strip_def_decorators(
                    sob.utilities.get_source(Client.__init__)
                )
            )
        )
        init_declaration_source = "".join(
            init_declaration_source.rpartition(") -> None:")[:-1]
        )
        yield self._insert_add_init_parameters(
            self._replace_init_parameter_defaults(
                self._remove_unused_init_parameters(init_declaration_source)
            )
        )
        yield from self._iter_class_init_docstring_source()
        yield "        super().__init__("
        for parameter_name in inspect.signature(Client).parameters:
            if parameter_name != "self" and (
                (not self._include_init_parameters)
                or (parameter_name in self._include_init_parameters)
            ):
                yield f"            {parameter_name}={parameter_name},"
        yield "        )"
        yield ""

    def _iter_paths_operations_methods_source(
        self,
    ) -> collections.abc.Iterable[str]:
        path: str
        path_item: PathItem | Reference
        if self.open_api.paths:
            for path, path_item in self.open_api.paths.items():
                try:
                    yield from self._iter_path_methods_source(
                        path, self._resolve_path_item(path_item)
                    )
                except Exception as error:
                    sob.errors.append_exception_text(
                        error,
                        "\nErrors were encountered while generating a method "
                        f"for the path: {path}",
                    )
                    raise

    def get_source(self, path: str | Path) -> str:
        """
        This generates source code for the client module.

        Parameters:
            path: The file path for the client module. This is needed
                in order to determine the relative import for the model module.
        """
        source: str = "\n".join(
            chain(
                self._iter_class_declaration_source(),
                self._iter_init_method_source(),
                self._iter_paths_operations_methods_source(),
                ("",),
            )
        )
        # The model module import couldn't be generated until we
        # knew the client module path, so we add it now
        self._imports |= {
            self._get_model_module_import(path),
            self._get_client_base_class_import(path),
        }
        # Imports need to be generated last
        imports: str = "\n".join(self._iter_imports())
        return sob.utilities.suffix_long_lines(
            f"{imports}\n\n\n{source.rstrip()}\n"
        )

    def save(self, path: str | Path) -> None:
        """
        This method will save the generated module to a given path.
        """
        client_source: str = self.get_source(path=path)
        # Save the module
        with open(path, "w") as model_io:
            model_io.write(client_source)

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._model_path == other._model_path
            and self.open_api == other.open_api
        )


Module = deprecated(
    "`oapi.client.Module` is deprecated and will be removed in oapi 3. "
    "Please use `oapi.ClientModule` instead."
)(ClientModule)


def write_client_module(
    client_path: str | Path,
    *,
    open_api: str | sob.abc.Readable | OpenAPI,
    model_path: str | Path,
    class_name: str = "Client",
    base_class: type[Client] = Client,
    imports: str | tuple[str, ...] = (),
    init_decorator: str = "",
    include_init_parameters: str | tuple[str, ...] = (),
    add_init_parameters: str | tuple[str, ...] = (),
    add_init_parameter_docs: str | tuple[str, ...] = (),
    init_parameter_defaults: collections.abc.Mapping[str, typing.Any]
    | collections.abc.Sequence[tuple[str, typing.Any]] = (),
    init_parameter_defaults_source: collections.abc.Mapping[str, typing.Any]
    | collections.abc.Sequence[tuple[str, typing.Any]] = (),
    get_method_name_from_path_method_operation: typing.Callable[
        [str, str, str | None], str
    ] = get_default_method_name_from_path_method_operation,
    use_operation_id: bool = False,
) -> None:
    """
    This function parses an Open API document and outputs a module defining
    a client class for interfacing with the API described by an OpenAPI
    document.

    Parameters:
        client_path: The file path where the client module will be saved
            (created or updated).
        open_api: An OpenAPI document. This can be a URL, file-path, an
            HTTP response (`http.client.HTTPResponse`), a file object, or
            an instance of `oapi.oas.model.OpenAPI`.
        model_path: The file path where the data model for this
            client can be found. This must be a model generated using
            `oapi.model`, and must be part of the same project that this
            client will be saved into.
        class_name:
        base_class: The base class to use for the client. If provided,
            this must be a sub-class of `oapi.client.Client`.
        imports: One or more import statements to include
            (in addition to those generated automatically).
        init_decorator:  A decorator to apply to the client class
            `.__init__` method. If used, make sure to include any modules
            referenced in your `imports`. For example:
            "@decorator_function(argument_a=1, argument_b=2)".
        include_init_parameters: The name of all parameters to
            include for the client's `.__init__` method.
        add_init_parameters: Additional parameter
            declarations to add to the client's `.__init__` method.
            These should include a type hint and default value (not just
            the parameter name). For example:
            'additional_parameter_name: str | None = None'. Note:
            additional parameters will not do anything without the use of a
            decorator which utilizes the additional parameters, so use of
            this parameter should be accompanied by an `init_decorator`.
        add_init_parameter_docs:
        init_parameter_defaults: A mapping of
            parameter names to default values for the parameter.
        init_parameter_defaults_source: A mapping of
            parameter names to default values for the parameter *expressed
            as source code*. This is to allow for the passing of imported
            constants, expressions, etc.
    """
    locals_: dict[str, typing.Any] = dict(locals())
    locals_.pop("client_path")
    client_module: ClientModule = ClientModule(**locals_)
    client_module.save(client_path)
