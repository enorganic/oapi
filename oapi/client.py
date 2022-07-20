import copyreg
import decimal
import gzip
import inspect
import json
import shlex
import re
import ssl
import sys
import threading
import time
import sob
import os
import functools
from base64 import b64encode
from datetime import date, datetime
from more_itertools import unique_everseen
from http.cookiejar import CookieJar
from ssl import SSLError
from itertools import chain
from collections import OrderedDict
from dataclasses import field, dataclass
from warnings import warn
from abc import ABC
from http.client import HTTPResponse
from logging import Logger, getLogger
from time import sleep
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Match,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    Pattern,
)
from urllib.error import HTTPError, URLError
from urllib.parse import (
    ParseResult,
    quote,
    urlencode as _urlencode,
    urlparse,
    urlunparse,
)
from urllib.request import (
    HTTPCookieProcessor,
    HTTPSHandler,
    OpenerDirector,
    Request,
    build_opener,
    urlopen,
)
from .oas.references import Resolver
from .oas.model import (
    MediaType,
    OAuthFlow,
    OpenAPI,
    Operation,
    Parameter,
    PathItem,
    Reference,
    RequestBody,
    Response,
    Schema,
    Encoding,
    SecuritySchemes,
    SecurityScheme,
)

_str_lru_cache: Callable[
    [], Callable[..., Callable[..., str]]
] = functools.lru_cache  # type: ignore
_dict_str_model_lru_cache: Callable[
    [], Callable[..., Callable[..., Dict[str, Type[sob.abc.Model]]]]
] = functools.lru_cache  # type: ignore
_lru_cache: Callable[
    [], Callable[..., Callable[..., Any]]
] = functools.lru_cache  # type: ignore

# region Client ABC


def urlencode(
    query: Union[Mapping[str, Any], Sequence[Tuple[str, Any]]],
    doseq: bool = True,
    safe: str = "|;,/=+",
    encoding: str = "utf-8",
    errors: str = "",
    quote_via: Callable[[str, Union[bytes, str], str, str], str] = quote,
) -> str:
    """
    This function wraps `urllib.parse.urlencode`, but has different default
    argument values. Additionally, when a mapping/dictionary is passed for a
    query value, that dictionary/mapping performs an update to the query
    dictionary.

    Parameters:

    - query ({str: typing.Any}|[(str, typing.Any)])
    - doseq (bool) = True
    - safe (str) = "|;,/=+"
    - encoding (str) = "utf-8"
    - errors (str) = ""
    - quote_via
    """
    items: List[Tuple[str, Any]] = []
    for item in query.items() if isinstance(query, Mapping) else query:
        if isinstance(item, Mapping):
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


def _censor_long_json_strings(text: str, limit: int = 2000) -> str:
    """
    Replace JSON strings (such as base-64 encoded images) longer than `limit`
    with "...".
    """
    limit_expression: str = '[^"]' * limit
    return re.sub(f'"{limit_expression}[^"]*"', '"..."', text)


_PRIMITIVE_VALUE_TYPES: Tuple[type, ...] = (
    str,
    bool,
    int,
    float,
    decimal.Decimal,
    date,
    datetime,
)
_PrimitiveValueTypes = Union[
    None, str, bool, int, float, decimal.Decimal, date, datetime
]


def _format_primitive_value(value: _PrimitiveValueTypes) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, float, decimal.Decimal)):
        return str(value)
    else:
        assert isinstance(value, (datetime, date)), repr(value)
        return value.isoformat()


def _format_simple_argument_value(
    value: sob.abc.MarshallableTypes,
    explode: bool = False,
) -> str:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    item: Tuple[str, _PrimitiveValueTypes]
    if isinstance(value, Dict):
        if explode:
            return ",".join(
                map(
                    lambda item: (
                        f"{item[0]}={_format_primitive_value(item[1])}"
                    ),
                    value,
                )
            )
        else:
            return ",".join(
                map(
                    _format_primitive_value,  # type: ignore
                    chain(*value.items()),
                )
            )
    elif isinstance(value, Sequence):
        return ",".join(map(_format_primitive_value, value))  # type: ignore
    else:
        raise ValueError(value)


def _format_label_argument_value(
    value: sob.abc.MarshallableTypes,
    explode: bool = False,
) -> str:
    argument_value: str
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        argument_value = _format_primitive_value(value)  # type: ignore
    else:
        if explode:
            item: Tuple[str, _PrimitiveValueTypes]
            if isinstance(value, Dict):
                argument_value = ".".join(
                    map(
                        lambda item: (
                            f"{item[0]}=" f"{_format_primitive_value(item[1])}"
                        ),
                        value,
                    )
                )
            elif isinstance(value, Sequence):
                argument_value = ".".join(
                    map(_format_primitive_value, value)  # type: ignore
                )
            else:
                raise ValueError(value)
        else:
            argument_value = _format_simple_argument_value(
                value, explode=False
            )
    return f".{argument_value}"


def _format_matrix_argument_value(
    name: str,
    value: sob.abc.MarshallableTypes,
    explode: bool = False,
) -> Union[str, Dict[str, str], Sequence[str], None]:
    argument_value: str
    if value is None:
        return None
    elif isinstance(value, _PRIMITIVE_VALUE_TYPES):
        argument_value = (
            f";{name}={_format_primitive_value(value)}"  # type: ignore
        )
    else:
        if explode:
            item: Tuple[str, _PrimitiveValueTypes]
            if isinstance(value, Dict):
                argument_value = "".join(
                    map(
                        lambda item: (
                            f";{item[0]}="
                            f"{_format_primitive_value(item[1])}"
                        ),
                        value,
                    )
                )
            elif isinstance(value, Sequence):
                value_: _PrimitiveValueTypes
                argument_value = "".join(
                    map(
                        lambda value_: (
                            f";{name}={_format_primitive_value(value_)}"
                        ),
                        value,
                    )
                )
            else:
                raise ValueError(value)
        else:
            argument_value = _format_simple_argument_value(
                value, explode=False
            )
            argument_value = f";{name}={argument_value}"
    return argument_value


def _format_form_argument_value(
    value: sob.abc.MarshallableTypes,
    explode: bool = False,
) -> Union[str, Dict[str, str], Sequence[str], None]:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    if explode:
        if isinstance(value, Mapping):
            key: str
            value_: sob.abc.MarshallableTypes
            return OrderedDict(
                [
                    (
                        key,  # type: ignore
                        _format_primitive_value(value_),  # type: ignore
                    )
                    for key, value_ in value.items()
                ]
            )
        elif isinstance(value, Sequence):
            return tuple(map(_format_primitive_value, value))  # type: ignore
        else:
            raise ValueError(value)
    else:
        return _format_simple_argument_value(value)


def _format_space_delimited_argument_value(
    value: sob.abc.MarshallableTypes,
    explode: bool = False,
) -> Union[str, Dict[str, str], Sequence[str], None]:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    elif explode:
        return _format_form_argument_value(value, explode=explode)
    else:
        if isinstance(value, Sequence):
            return " ".join(
                map(_format_primitive_value, value)  # type: ignore
            )
        else:
            # This style is only valid for arrays
            raise ValueError(value)


def _format_pipe_delimited_argument_value(
    value: sob.abc.MarshallableTypes,
    explode: bool = False,
) -> Union[str, Dict[str, str], Sequence[str], None]:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    elif explode:
        return _format_form_argument_value(value, explode=explode)
    else:
        if isinstance(value, Sequence):
            return "|".join(
                map(_format_primitive_value, value)  # type: ignore
            )
        else:
            # This style is only valid for arrays
            raise ValueError(value)


def _format_deep_object_argument_value(
    name: str,
    value: sob.abc.MarshallableTypes,
    explode: bool = False,
) -> Union[str, Dict[str, str], Sequence[str], None]:
    if value is None or isinstance(value, _PRIMITIVE_VALUE_TYPES):
        return _format_primitive_value(value)  # type: ignore
    else:
        assert explode
        if isinstance(value, Mapping):
            key: str
            value_: sob.abc.MarshallableTypes
            return OrderedDict(
                [
                    (
                        f"{name}[{key}]",  # type: ignore
                        _format_primitive_value(value_),  # type: ignore
                    )
                    for key, value_ in value.items()
                ]
            )
        else:
            # This style is only valid for dictionaries
            raise ValueError(value)


def format_argument_value(
    name: str,
    value: sob.abc.MarshallableTypes,
    style: str,
    explode: bool = False,
) -> Union[str, Dict[str, str], Sequence[str], None]:
    """
    Format an argument value for use in a path, query, cookie, header, etc.

    Parameters:

    - value (
        str|bool|int|float|decimal.Decimal|{str: typing.Any}|[typing.Any]|None
      )
    - style (str)
    - explode (bool) = False
    - in_ (str) = ""

    See: https://swagger.io/docs/specification/serialization/
    """
    if isinstance(value, sob.abc.Model):
        value = sob.model.marshal(value)  # type: ignore
    if style == "simple":
        return _format_simple_argument_value(value, explode=explode)
    elif style == "label":
        return _format_label_argument_value(value, explode=explode)
    elif style == "matrix":
        return _format_matrix_argument_value(name, value, explode=explode)
    elif style == "form":
        return _format_form_argument_value(value, explode=explode)
    elif style == "spaceDelimited":
        return _format_space_delimited_argument_value(value, explode=explode)
    elif style == "pipeDelimited":
        return _format_pipe_delimited_argument_value(value, explode=explode)
    elif style == "deepObject":
        return _format_deep_object_argument_value(name, value, explode=explode)
    else:
        raise ValueError(style)


def get_request_curl(
    request: Request,
    options: str = "-i",
    censored_headers: Iterable[str] = (
        "X-api-key",
        "Authorization",
    ),
) -> str:
    """
    Render an instance of `urllib.request.Request` as a `curl` command.

    Parameters:

    - options (str): Any additional parameters to pass to `curl`,
      (such as "--compressed", "--insecure", etc.)
    """
    lowercase_excluded_headers: Tuple[str, ...] = tuple(
        map(str.lower, censored_headers)
    )

    def _get_request_curl_header_item(item: Tuple[str, str]) -> str:
        key: str
        value: str
        key, value = item
        if key.lower() in lowercase_excluded_headers:
            value = "***"
        return "-H {}".format(shlex.quote(f"{key}: {value}"))

    data: bytes = (
        request.data
        if isinstance(request.data, bytes)
        else request.data.read()  # type: ignore
        if isinstance(request.data, sob.abc.Readable)
        else b"".join(request.data)  # type: ignore
        if request.data
        else b""
    )
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
                (f"-d {shlex.quote(data.decode('utf-8'))}" if data else ""),
                shlex.quote(request.full_url),
            ),
        )
    )


def _represent_http_response(
    response: HTTPResponse, data: Optional[bytes] = None
) -> str:
    data = HTTPResponse.read(response) if data is None else data
    content_encoding: str
    for content_encoding in response.getheader("Contents-encoding", "").split(
        ","
    ):
        content_encoding = content_encoding.strip().lower()
        if content_encoding and content_encoding == "gzip":
            data = gzip.decompress(data)
    headers: str = "\n".join(
        f"{key}: {value}" for key, value in response.headers.items()
    )
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
    response: HTTPResponse, callback: Callable = print
) -> None:
    """
    Perform a callback on an HTTP response at the time it is read
    """

    @functools.wraps(response.read)
    def response_read(amt: Optional[int] = None) -> bytes:
        data: bytes = HTTPResponse.read(response, amt)
        callback(_represent_http_response(response, data))
        return data

    response.read = response_read  # type: ignore


def default_retry_hook(error: Exception) -> bool:
    assert error
    return True


def retry(
    errors: Union[Tuple[Type[Exception], ...], Type[Exception]] = Exception,
    retry_hook: Callable[[Exception], bool] = default_retry_hook,
    number_of_attempts: int = 1,
    logger: Optional[Logger] = None,
) -> Callable:
    """
    This function decorates another, and causes the decorated function
    to be re-attempted a specified number of times, with exponential
    backoff, until the decorated function is successful or the maximum
    number of attempts is reached (in which case an exception is raised).

    Parameters:

    - errors: A sub-class of `Exception`, or a tuple of one or more
      sub-classes of `Exception`. The default is `Exception`, causing
      *all* errors to trigger a retry.
    - retry_hook: A function accepting as it's only argument the handled
      exception, and returning a boolean value indicating whether or not to
      retry the function.
    - number_of_attempts (int) = 1: The maximum number of times to attempt
      execution of the function, *including* the first execution. Please
      note that, because the default for this parameter is 1, this decorator
      will do *nothing* if this argument is not provided.
    """

    def decorating_function(function: Callable) -> Callable:
        attempt_number: int = 1

        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal attempt_number
            nonlocal number_of_attempts
            if number_of_attempts - attempt_number:
                try:
                    return function(*args, **kwargs)
                except errors as error:
                    if not retry_hook(error):
                        raise
                    warning_message: str = (
                        f"Attempt # {str(attempt_number)}:\n"
                        f"{sob.errors.get_exception_text()}"
                    )
                    warn(warning_message)
                    if logger is not None:
                        logger.warning(warning_message)
                    sleep(2**attempt_number)
                    attempt_number += 1
                    return wrapper(*args, **kwargs)
            return function(*args, **kwargs)

        return wrapper

    return decorating_function


def _remove_none(
    items: Union[Mapping[str, Any], Sequence[Tuple[str, Any]]]
) -> Sequence[Tuple[str, Any]]:
    if isinstance(items, Mapping):
        items = tuple(items.items())
    item: Tuple[str, Any]
    return tuple(filter(lambda item: item[1] is not None, items))


def _format_request_data(
    data: Union[str, bytes, sob.abc.Model, None],
    form_data: Union[Mapping[str, Any], Sequence[Tuple[str, Any]]],
) -> Optional[bytes]:
    if form_data:
        form_data = _remove_none(form_data)
    formatted_data: Optional[bytes] = None
    if data:
        assert not form_data
        # Cast `data` as a `str`
        if isinstance(data, sob.abc.Model):
            data = sob.model.serialize(data)
        # Convert `str` data to `bytes`
        if isinstance(data, str):
            formatted_data = bytes(data, encoding="utf-8")
        else:
            formatted_data = data
    elif form_data:
        assert form_data
        formatted_data = bytes(urlencode(form_data), encoding="utf-8")
    return formatted_data


def _make_thread_locks_pickleable() -> None:
    """
    This makes it so that thread-locked connections can be pickled
    """
    LockType: type = type(threading.Lock())
    RLockType: type = type(threading.RLock())
    copyreg.pickle(LockType, lambda lock: (threading.Lock, ()))  # type: ignore
    copyreg.pickle(
        RLockType, lambda rlock: (threading.RLock, ())  # type: ignore
    )


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


DEFAULT_RETRY_FOR_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    HTTPError,
    SSLError,
    URLError,
    ConnectionError,
    TimeoutError,
)
CLIENT_SLOTS: Tuple[str, ...] = (
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
    "oauth2_refresh_url",
    "oauth2_flows",
    "open_id_connect_url",
    "headers",
    "timeout",
    "retry_number_of_attempts",
    "retry_for_errors",
    "retry_hook",
    "_verify_ssl_certificate",
    "logger",
    "echo",
    "_cookie_jar",
    "_opener",
    "_oauth2_authorization_expires",
)


class _SSLContext(ssl.SSLContext):
    """
    This class is a wrapper for `ssl.SSLContext` which makes it possible to
    connect to hosts which have an unverified SSL certificate.
    """

    def __init__(self, check_hostname: bool = True) -> None:
        if check_hostname:
            self.load_default_certs()
        else:
            self.check_hostname: bool = False
            self.verify_mode: ssl.VerifyMode = ssl.CERT_NONE
        super().__init__()

    def __reduce__(self) -> Tuple:
        """
        A pickled instance of this class will just be an entirely new
        instance.
        """
        return _SSLContext, (self.check_hostname,)


class Client(ABC):
    """
    A base class for OpenAPI clients.

    Initialization Parameters:

    - url (str): The base URL for API requests.
    - user (str) = "": A user name for use with HTTP basic authentication.
    - password (str) = "":  A password for use with HTTP basic authentication.
    - bearer_token (str) = "": A token for use with HTTP bearer authentication.
    - api_key (str) = "": An API key with which to authenticate requests.
    - api_key_in (str) = "header": Where the API key should be conveyed:
      "header", "query" or "cookie".
    - api_key_name (str) = "": The name of the header, query parameter, or
      cookie parameter in which to convey the API key.
    - oauth2_client_id (str) = "": An OAuth2 client ID.
    - oauth2_client_secret (str) = "": An OAuth2 client secret.
    - oauth2_username (str) = "": A *username* for the "password" OAuth2 grant
      type.
    - oauth2_password (str) = "": A *password* for the "password" OAuth2 grant
      type.
    - oauth2_authorization_url (str) = "": The authorization URL to use for an
      OAuth2 flow. Can be relative to `url`.
    - oauth2_token_url (str) = "": The token URL to use for OAuth2
      authentication.
      Can be relative to `url`.
    - oauth2_refresh_url (str) = "": The URL to be used for obtaining refresh
      tokens for OAuth2 authentication.
    - oauth2_flows ((str,)) = (): A tuple containing one or more of the
      following: "authorizationCode", "implicit", "password" and/or
      "clientCredentials".
    - open_id_connect_url (str) = "": An OpenID connect URL where a JSON
      web token containing OAuth2 information can be found.
    - headers ({str: str}): Default headers to include with all requests.
      Method-specific header arguments will override or modify these, where
      applicable, as will dynamically modified headers such as content-length,
      authorization, cookie, etc.
    - timeout (int): The number of seconds before a request will timeout
      and throw an error. If this is 0 (the default), the system default
      timeout will be used.
    - retry_number_of_attempts (int) = 1: The number of times to retry
      a request which results in an error.
    - retry_for_errors: A tuple of one or more exception types
      on which to retry a request. To retry for *all* errors,
      pass `(Exception,)` for this argument.
    - retry_hook: A function, accepting one argument (an Exception),
      and returning a boolean value indicating whether to retry the
      request (if retries have not been exhausted). This hook applies
      *only* for exceptions which are a sub-class of an exception
      included in `retry_for_errors`.
    - verify_ssl_certificate (bool) = True: If `True`, SSL certificates
      are verified, per usual. If `False`, SSL certificates are *not*
      verified.
    - logger (logging.Logger|None) = None:
      A `logging.Logger` to which requests should be logged.
    - echo (bool) = False: If `True`, requests/responses are printed as
      they occur.
    """

    __slots__: Tuple[str, ...] = CLIENT_SLOTS

    def __init__(
        self,
        url: str,
        user: str = "",
        password: str = "",
        bearer_token: str = "",
        api_key: str = "",
        api_key_in: str = "header",
        api_key_name: str = "X-API-KEY",
        oauth2_client_id: str = "",
        oauth2_client_secret: str = "",
        oauth2_username: str = "",
        oauth2_password: str = "",
        oauth2_authorization_url: str = "",
        oauth2_token_url: str = "",
        oauth2_refresh_url: str = "",
        oauth2_flows: Tuple[str, ...] = (),
        open_id_connect_url: str = "",
        headers: Union[  # Force line-break retention
            Mapping[str, str], Sequence[Tuple[str, str]]
        ] = (
            ("Accept", "application/json"),
            ("Content-type", "application/json"),
        ),
        timeout: int = 0,
        retry_number_of_attempts: int = 1,
        retry_for_errors: Tuple[
            Type[Exception], ...
        ] = DEFAULT_RETRY_FOR_EXCEPTIONS,
        retry_hook: Callable[  # Force line-break retention
            [Exception], bool
        ] = default_retry_hook,
        verify_ssl_certificate: bool = True,
        logger: Optional[Logger] = None,
        echo: bool = False,
    ) -> None:
        # Ensure the API key location is valid
        assert api_key_in in ("header", "query", "cookie"), (
            f"Invalid input for `api_key_in`:  {repr(api_key_in)}\n"
            'Valid values are "header", "query" or "cookie".'
        )
        # Translate OpenAPI 2x OAuth2 flow names
        flow: str
        oauth2_flows = tuple(
            map(
                lambda flow: (
                    "authorizationCode"
                    if flow == "accessCode"
                    else "clientCredentials"
                    if flow == "application"
                    else flow
                ),
                oauth2_flows,
            )
        )
        # Ensure OAuth2 flows are valid
        assert all(
            map(
                lambda flow: flow
                in {
                    "authorizationCode",
                    "implicit",
                    "password",
                    "clientCredentials",
                },
                oauth2_flows,
            )
        ), (
            f"Invalid value(s) for `oauth2_flows`:  {repr(api_key_in)}\n"
            'Valid values are "authorizationCode", "implicit", "password", '
            'or "clientCredentials".'
        )
        # Set properties
        self.url = url
        self.user = user
        self.password = password
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_key_in = api_key_in
        self.api_key_name = api_key_name
        self.oauth2_client_id = oauth2_client_id
        self.oauth2_client_secret = oauth2_client_secret
        self.oauth2_username = oauth2_username
        self.oauth2_password = oauth2_password
        self.oauth2_authorization_url = oauth2_authorization_url
        self.oauth2_token_url = oauth2_token_url
        self.oauth2_refresh_url = oauth2_refresh_url
        self.oauth2_flows = oauth2_flows
        self.open_id_connect_url = open_id_connect_url
        self.headers: Dict[str, str] = dict(headers)
        self.timeout = timeout
        self.retry_number_of_attempts = retry_number_of_attempts
        self.retry_for_errors = retry_for_errors
        self.retry_hook = retry_hook
        self._verify_ssl_certificate = verify_ssl_certificate
        self.logger = logger
        self.echo = echo
        # Support for persisting cookies
        self._cookie_jar: CookieJar = CookieJar()
        self._opener: OpenerDirector = build_opener(
            HTTPSHandler(
                context=_SSLContext(check_hostname=verify_ssl_certificate)
            ),
            HTTPCookieProcessor(self._cookie_jar),
        )
        self._oauth2_authorization_expires: int = 0

    @classmethod
    def _resurrect_client(cls, *args: Any) -> "Client":
        """
        This function is for use with the `.__reduce__` method of
        `oapi.client.Client` and its sub-classes, in order to properly
        un-pickle instances which have been pickled (such as for use in
        multiprocessing, etc.).
        """
        init_parameters: List[Any] = list(args)
        oauth2_authorization_expires: int = init_parameters.pop()
        cookie_jar: CookieJar = init_parameters.pop()
        client: Client = cls(*init_parameters)
        client._cookie_jar = cookie_jar
        client._oauth2_authorization_expires = oauth2_authorization_expires
        return client

    def __reduce__(
        self,
    ) -> Tuple[  # Force line-break retention
        Callable[..., "Client"], Tuple[Any, ...]
    ]:
        return self._resurrect_client, (
            # Initialization Parameters
            self.url,
            self.user,
            self.password,
            self.bearer_token,
            self.api_key,
            self.api_key_in,
            self.api_key_name,
            self.oauth2_client_id,
            self.oauth2_client_secret,
            self.oauth2_username,
            self.oauth2_password,
            self.oauth2_authorization_url,
            self.oauth2_token_url,
            self.oauth2_refresh_url,
            self.oauth2_flows,
            self.open_id_connect_url,
            self.headers,
            self.timeout,
            self.retry_number_of_attempts,
            self.retry_for_errors,
            self.retry_hook,
            self._verify_ssl_certificate,
            self.logger,
            self.echo,
            # Not Initialization Parameters
            self._cookie_jar,
            self._oauth2_authorization_expires,
        )

    def _get_request_response_callback(
        self, error: Optional[HTTPError] = None
    ) -> Callable:
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
                print(text)

        return callback

    def request(
        self,
        path: str,
        method: str,
        data: Union[str, bytes, sob.abc.Model, None] = None,
        form_data: Union[
            Mapping[
                str,
                sob.abc.MarshallableTypes,
            ],
            Sequence[
                Tuple[
                    str,
                    sob.abc.MarshallableTypes,
                ]
            ],
        ] = (),
        query: Union[
            Mapping[
                str,
                sob.abc.MarshallableTypes,
            ],
            Sequence[
                Tuple[
                    str,
                    sob.abc.MarshallableTypes,
                ]
            ],
        ] = (),
        headers: Union[
            Mapping[
                str,
                sob.abc.MarshallableTypes,
            ],
            Sequence[
                Tuple[
                    str,
                    sob.abc.MarshallableTypes,
                ]
            ],
        ] = (),
        timeout: int = 0,
    ) -> sob.abc.Readable:
        """
        Construct and submit an HTTP request and return the response
        (an instance of `http.client.HTTPResponse`).

        Parameters:

        - path (str): This is the path of the request, relative to the server
          base URL
        - query ({str: str}|[(str,str)])
        - data (str): This the data to be conveyed in the body of the request
        - timeout (int)
        """
        request: Callable[
            [
                str,
                str,
                Optional[Union[str, bytes, sob.abc.Model]],
                Union[
                    Mapping[
                        str,
                        sob.abc.MarshallableTypes,
                    ],
                    Sequence[
                        Tuple[
                            str,
                            sob.abc.MarshallableTypes,
                        ]
                    ],
                ],
                Union[
                    Mapping[
                        str,
                        sob.abc.MarshallableTypes,
                    ],
                    Sequence[
                        Tuple[
                            str,
                            sob.abc.MarshallableTypes,
                        ]
                    ],
                ],
                Union[
                    Mapping[
                        str,
                        sob.abc.MarshallableTypes,
                    ],
                    Sequence[
                        Tuple[
                            str,
                            sob.abc.MarshallableTypes,
                        ]
                    ],
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
        return request(path, method, data, form_data, query, headers, timeout)

    def _request_callback(self, request: Request) -> None:
        curl_options: str = "-i"
        content_encoding: str
        for content_encoding in request.headers.get(
            "Content-encoding", ""
        ).split(","):
            content_encoding = content_encoding.strip().lower()
            if content_encoding and content_encoding == "gzip":
                curl_options = f"{curl_options} --compressed"
        self._get_request_response_callback()(
            get_request_curl(request, options=curl_options)
        )

    def _request_oauth2_password_authorization(
        self,
    ) -> sob.abc.Readable:
        try:
            return self._opener.open(  # type: ignore
                Request(
                    self.oauth2_token_url,
                    headers={"Host": urlparse(self.oauth2_token_url).netloc},
                    method="POST",
                    data=bytes(
                        urlencode(
                            dict(
                                grant_type="password",
                                client_id=self.oauth2_client_id,
                                username=self.oauth2_username,
                                password=self.oauth2_password,
                            )
                        ),
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
            else:
                raise

    def _request_oauth2_client_credentials_authorization(
        self,
    ) -> sob.abc.Readable:
        try:
            return self._opener.open(  # type: ignore
                Request(
                    self.oauth2_token_url,
                    headers={"Host": urlparse(self.oauth2_token_url).netloc},
                    method="POST",
                    data=bytes(
                        urlencode(
                            dict(
                                grant_type="client_credentials",
                                client_id=self.oauth2_client_id,
                                client_secret=self.oauth2_client_secret,
                            )
                        ),
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
                return self._request_oauth2_client_credentials_authorization()
            else:
                raise

    def _get_oauth2_client_credentials_authorization(self) -> str:
        if self._oauth2_authorization_expires < int(time.time()) or (
            "Authorization" not in self.headers
        ):
            # If our authorization has expired, get a new token
            with (
                self._request_oauth2_client_credentials_authorization()
            ) as response:
                response_data: Dict[str, str] = json.loads(
                    str(response.read(), encoding="utf-8")
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
            with (self._request_oauth2_password_authorization()) as response:
                response_data: Dict[str, str] = json.loads(
                    str(response.read(), encoding="utf-8")
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
                # TODO implicit OAuth2 flow
                warn(
                    'The "implicit" OAuth2 flow is not currently implemented.'
                )
            if "password" in self.oauth2_flows:
                warn(
                    'The "password" OAuth2 flow requires the client be '
                    "initialized with `oauth2_client_id`, `oauth2_username`, "
                    "and `oauth2_password` arguments."
                )
            if "clientCredentials" in self.oauth2_flows:
                # TODO password OAuth2 flow
                warn(
                    'The "clientCredentials" OAuth2 flow requires the client '
                    "be initialized with `oauth2_client_id`, "
                    "`oauth2_username`, and `oauth2_password` arguments."
                )
            if "authorizationCode" in self.oauth2_flows:
                # TODO authorizationCode OAuth2 flow
                warn(
                    'The "authorizationCode" OAuth2 flow is not currently '
                    "implemented."
                )

    def _api_key_authenticate_request(self, request: Request) -> None:
        # API key authentication: https://bit.ly/3Jrvd8Q
        if self.api_key_in == "cookie":
            cookie_header: str = request.get_header("Cookie", "")
            if cookie_header:
                cookie_header = f"{cookie_header}; "
            cookie_header = (
                f"{cookie_header}" f"{self.api_key_name}" f"={self.api_key}"
            )
            request.add_header("Cookie", cookie_header)
        elif self.api_key_in == "query":
            api_key_query_assignment: str = (
                f"{self.api_key_name}={quote(self.api_key)}"
            )
            parse_result: ParseResult = urlparse(request.full_url)
            parse_result_dictionary: Dict[str, str] = parse_result._asdict()
            parse_result_dictionary["query"] = (
                f"{parse_result.query}&{api_key_query_assignment}"
                if parse_result.query
                else api_key_query_assignment
            )
            request.full_url = urlunparse(
                ParseResult(**parse_result_dictionary)
            )
        else:
            assert self.api_key_in == "header", repr(self.api_key_in)
            request.add_header(self.api_key_name, self.api_key)

    def _authenticate_request(self, request: Request) -> None:
        """
        Determine the applicable authentication scheme and authenticate a
        request.

        Parameters:

        - request (urllib.request.Request)
        """
        # HTTP authentication schemes
        # TODO: Implement additional HTTP authentication schemes
        # (https://bit.ly/35VOGRu)
        if self.user and self.password:
            # Basic authentication: https://bit.ly/3Ob0LDV
            login: str = str(
                b64encode(
                    bytes(f"{self.user}:{self.password}", encoding="utf-8")
                ),
                encoding="ascii",
            )
            request.add_header("Authorization", f"Basic {login}")
        if self.bearer_token:
            # Bearer authentication: https://bit.ly/3O3ciFg
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

    def _request(
        self,
        path: str,
        method: str,
        data: Union[str, bytes, sob.abc.Model, None] = None,
        form_data: Union[
            Mapping[
                str,
                sob.abc.MarshallableTypes,
            ],
            Sequence[
                Tuple[
                    str,
                    sob.abc.MarshallableTypes,
                ]
            ],
        ] = (),
        query: Union[
            Mapping[
                str,
                sob.abc.MarshallableTypes,
            ],
            Sequence[
                Tuple[
                    str,
                    sob.abc.MarshallableTypes,
                ]
            ],
        ] = (),
        headers: Union[
            Mapping[
                str,
                sob.abc.MarshallableTypes,
            ],
            Sequence[
                Tuple[
                    str,
                    sob.abc.MarshallableTypes,
                ]
            ],
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
            assert path[0] == "/"
            url = f"{self.url}{path}"
        request_headers: Dict[str, str] = dict(self.headers)
        if headers:
            key: str
            value: str
            request_headers.update(
                **{  # type: ignore
                    key: value
                    for key, value in (
                        headers.items()
                        if isinstance(headers, Mapping)
                        else headers
                    )
                    if key and value
                }
            )
        # Assemble the request
        request = Request(
            url,
            data=_format_request_data(data, form_data),
            method=method.upper(),
            headers=request_headers,
        )
        # Authenticate the request
        self._authenticate_request(request)
        # Assemble keyword arguments for passing to the opener
        open_kwargs: Dict[str, Any] = {}
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
            error_response: Optional[HTTPResponse] = getattr(
                error, "file", None
            )
            if error_response is not None:
                sob.errors.append_exception_text(
                    error,
                    "\n\n{}".format(
                        _censor_long_json_strings(
                            _represent_http_response(error_response)
                        )
                    ),
                )
            raise error
        assert isinstance(response, sob.abc.Readable)
        return response


# endregion


def _get_path_open_api(path: str) -> OpenAPI:
    with open(path, "r") as open_api_io:
        assert isinstance(open_api_io, sob.abc.Readable)
        return _get_io_open_api(open_api_io)


def _get_url_open_api(url: str) -> OpenAPI:
    with urlopen(url) as open_api_io:
        return _get_io_open_api(open_api_io)


def _get_io_open_api(model_io: sob.abc.Readable) -> OpenAPI:
    return OpenAPI(model_io)


def _iter_path_item_operations(
    path_item: PathItem,
) -> Iterable[Tuple[str, Operation]]:
    """
    Yield all operations on a path as a tuple of the operation name
    ("get", "put", "post", "patch", etc.) and the object representing that
    operation (an instance of `oapi.oas.model.Operation`).

    Parameters:

    - path_item (oapi.oas.model.PathItem)
    """
    name_: str
    name: str
    value: sob.abc.MarshallableTypes
    for name, value in map(
        lambda name_: (name_, getattr(path_item, name_)),
        ("get", "put", "post", "delete", "options", "head", "patch", "trace"),
    ):
        if value is not None:
            assert isinstance(value, Operation)
            yield name, value


def _get_relative_module_path(from_path: str, to_path: str) -> str:
    """
    Get a relative import based on module file paths

    Examples:

    >>> _get_relative_module_path("a/b/c.py", "d/e/f.py")
    '...a.b.c'

    >>> _get_relative_module_path("a/b/c.py", "a/b/f.py")
    '.c'
    """
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


def _get_relative_module_import(from_path: str, to_path: str) -> str:
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
    groups: Tuple[str, str, str] = re.match(  # type: ignore
        r"^(\.*)(?:(.*)\.)?([^.]+)", relative_module_path
    ).groups()
    assert len(groups) == 3
    return f"from {groups[0] or ''}{groups[1] or ''} import {groups[2]}"


def _schema_defines_model(schema: Union[Schema, Parameter]) -> bool:
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


@dataclass
class _ParameterLocations:
    total_count: int = 0
    header: Dict[str, _Parameter] = field(default_factory=OrderedDict)
    body: Optional[_Parameter] = None
    path: Dict[str, _Parameter] = field(default_factory=OrderedDict)
    query: Dict[str, _Parameter] = field(default_factory=OrderedDict)
    form_data: Dict[str, _Parameter] = field(default_factory=OrderedDict)
    cookie: Dict[str, _Parameter] = field(default_factory=OrderedDict)


def _iter_parameters(
    parameter_locations: _ParameterLocations,
) -> Iterable[Tuple[str, _Parameter]]:
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
) -> Iterable[Tuple[str, _Parameter]]:
    item: Tuple[str, _Parameter]
    return sorted(
        _iter_parameters(parameter_locations), key=lambda item: item[1].index
    )


def _iter_request_path_representation(
    path: str, parameter_locations: _ParameterLocations
) -> Iterable[str]:
    path_representation: str = sob.utilities.inspect.represent(path)
    if parameter_locations.path:
        yield f"            {path_representation}.format(**{{"
        name: str
        parameter: _Parameter
        for name, parameter in parameter_locations.path.items():
            yield _represent_dictionary_parameter(name, parameter)
        yield "            }),"
    else:
        yield f"            {path_representation},"


def _represent_dictionary_parameter(
    name: str, parameter: _Parameter, use_kwargs: bool = False
) -> str:
    represent_style: str = sob.utilities.inspect.represent(parameter.style)
    represent_explode: str = sob.utilities.inspect.represent(parameter.explode)
    parameter_name: str = parameter.name
    if parameter.style == "matrix":
        parameter_name = f";{parameter_name}"
    if use_kwargs:
        name = f'kwargs.get("{name}", None)'
    return (
        f'                "{parameter_name}": '
        "oapi.client.format_argument_value(\n"
        f'                    "{parameter_name}",\n'
        f"                    {name},\n"
        f"                    style={represent_style},\n"
        f"                    explode={represent_explode}\n"
        "                ),"
    )


def _iter_cookie_dictionary_parameter_representation(
    names_parameters: Dict[str, _Parameter]
) -> Iterable[str]:
    if names_parameters:
        yield '                "Cookie": "; ".join(('
        name: str
        parameter: _Parameter
        for name, parameter in names_parameters.items():
            represent_style: str = sob.utilities.inspect.represent(
                parameter.style
            )
            represent_explode: str = sob.utilities.inspect.represent(
                parameter.explode
            )
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
    parameter_locations: _ParameterLocations, use_kwargs: bool = False
) -> Iterable[str]:
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
    parameter_locations: _ParameterLocations, use_kwargs: bool = False
) -> Iterable[str]:
    if parameter_locations.body:
        # Form data and a request body cannot co-exist
        assert not parameter_locations.form_data
        name: str = parameter_locations.body.name
        if use_kwargs:
            name = f'kwargs.get("{name}", None)'
        yield (f"            data={name},")


def _iter_request_query_representation(
    parameter_locations: _ParameterLocations, use_kwargs: bool = False
) -> Iterable[str]:
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
    parameter_locations: _ParameterLocations, use_kwargs: bool = False
) -> Iterable[str]:
    if parameter_locations.form_data:
        yield "            form_data={"
        name: str
        parameter: _Parameter
        for name, parameter in parameter_locations.form_data.items():
            if use_kwargs:
                name = f'kwargs.get("{name}", None)'
            parameter_representation = (
                f'                "{parameter.name}": {name},'
            )
            if (
                len(parameter_representation)
                > sob.utilities.string.MAX_LINE_LENGTH
            ):
                parameter_representation = (
                    f'                "{parameter.name}":\n'
                    f"                {name},"
                )
            yield parameter_representation
        yield "            },"


class Module:
    """
    This class parses an Open API document and outputs a module defining
    a client class for interfacing with the API described by an OpenAPI
    document.

    Initialization Parameters:

    - open_api: An OpenAPI document. This can be a URL, file-path, an
      HTTP response (`http.client.HTTPResponse`), a file object, or an
      instance of `oapi.oas.model.OpenAPI`.
    - model_path (str): The file path where the data model for this client
      can be found. This must be a model generated using `oapi.model`,
      and must be part of the same project that this client will be saved into.
    - class_name (str) = "Client"
    - base_class (typing.Type[oapi.client.Client]) = oapi.client.Client:
      The base class to use for the client. If provided, this must
      be a sub-class of `oapi.client.Client`.
    - imports ([str]) = (): One or more import statements to include
      (in addition to those generated automatically).
    - init_decorator (str) = "":  A decorator to apply to the client
      class `.__init__` method. If used, make sure to include any modules
      referenced in your `imports`. For example:
      "@decorator_function(argument_a=1, argument_b=2)".
    - include_init_parameters ([str]) = (): The name of all parameters to
      include for the client's `.__init__` method.
    - add_init_parameters ([str]) = (): Additional parameter
      declarations to add to the client's `.__init__` method.
      These should include a type hint and default value (not just the
      parameter name). For example:
      'additional_parameter_name: typing.Optional[str] = None'. Note:
      additional parameters will not do anything without the use of a
      decorator which utilizes the additional parameters, so use of this
      parameter should be accompanied by an `init_decorator`.
    - add_init_parameter_docs ([str])
    - init_parameter_defaults ({str: typing.Any}): A mapping of
      parameter names to default values for the parameter.
    - init_parameter_defaults_source ({str: str}): A mapping of
      parameter names to default values for the parameter *expressed as
      source code*. This is to allow for the passing of imported constants,
      expressions, etc.
    """

    def __init__(
        self,
        open_api: Union[str, sob.abc.Readable, OpenAPI],
        model_path: str,
        class_name: str = "Client",
        base_class: Type[Client] = Client,
        imports: Union[str, Tuple[str, ...]] = (),
        init_decorator: str = "",
        include_init_parameters: Union[str, Tuple[str, ...]] = (),
        add_init_parameters: Union[str, Tuple[str, ...]] = (),
        add_init_parameter_docs: Union[str, Tuple[str, ...]] = (),
        init_parameter_defaults: Union[
            Mapping[str, Any], Sequence[Tuple[str, Any]]
        ] = (),
        init_parameter_defaults_source: Union[
            Mapping[str, Any], Sequence[Tuple[str, Any]]
        ] = (),
    ) -> None:
        # Ensure a valid model path has been provided
        assert os.path.exists(model_path)
        # Get an OpenAPI document
        if isinstance(open_api, str):
            if os.path.exists(open_api):
                open_api = _get_path_open_api(open_api)
            else:
                open_api = _get_url_open_api(open_api)
        elif isinstance(open_api, sob.abc.Readable):
            open_api = _get_io_open_api(open_api)
        elif not isinstance(open_api, OpenAPI):
            raise TypeError(
                f"`{sob.utilities.inspect.calling_function_qualified_name()}` "
                "requires an instance of `str`, "
                f"`{sob.utilities.inspect.qualified_name(OpenAPI)}`, or a "
                "file-like object for the `open_api` parameter--not "
                f"{repr(open_api)}"
            )
        # Ensure all elements have URLs and JSON pointers
        sob.meta.set_url(open_api, sob.meta.get_url(open_api))
        sob.meta.set_pointer(open_api, sob.meta.get_pointer(open_api) or "")
        self.open_api: OpenAPI = open_api
        init_decorator = init_decorator.strip()
        if init_decorator and not init_decorator.startswith("@"):
            raise ValueError(init_decorator)
        self._init_decorator: str = init_decorator.strip()
        self._include_init_parameters: Tuple[str, ...] = (
            (include_init_parameters,)
            if isinstance(include_init_parameters, str)
            else include_init_parameters
        )
        self._add_init_parameters: Tuple[str, ...] = (
            (add_init_parameters,)
            if isinstance(add_init_parameters, str)
            else add_init_parameters
        )
        self._add_init_parameter_docs: Tuple[str, ...] = (
            (add_init_parameter_docs,)
            if isinstance(add_init_parameter_docs, str)
            else add_init_parameter_docs
        )
        self._init_parameter_defaults: Dict[str, Any] = dict(
            init_parameter_defaults
        )
        self._init_parameter_defaults_source: Dict[str, Any] = dict(
            init_parameter_defaults_source
        )
        self._resolver: Resolver = Resolver(open_api)
        self._model_path: str = model_path
        self._base_class: Type[Client] = base_class
        self._class_name: str = class_name
        # This keeps track of used names in the global namespace
        self._names: Set[str] = {
            "sob",
            "oapi",
            "typing",
            "decimal",
            "Logger",
            self._class_name,
        }
        self._imports: Set[str] = set(
            filter(
                None,
                (
                    (
                        "import typing",
                        "import sob",
                        "import oapi",
                        "from logging import Logger",
                    )
                    + ((imports,) if isinstance(imports, str) else imports)
                ),
            )
        )

    def _get_open_api_major_version(self) -> int:
        return int(
            (self.open_api.swagger or self.open_api.openapi or "0")
            .split(".")[0]
            .strip()
        )

    def _resolve_media_type(
        self, media_type: Union[MediaType, Reference]
    ) -> MediaType:
        if isinstance(media_type, Reference):
            resolved_media_type: sob.abc.Model = (
                self._resolver.resolve_reference(
                    media_type, types=(MediaType,)
                )
            )
            assert isinstance(resolved_media_type, MediaType)
            media_type = resolved_media_type
        return media_type

    def _resolve_response(
        self, response: Union[Response, Reference]
    ) -> Response:
        if isinstance(response, Reference):
            resolved_response: sob.abc.Model = (
                self._resolver.resolve_reference(response, types=(Response,))
            )
            assert isinstance(resolved_response, Response)
            response = resolved_response
        return response

    def _resolve_parameter(
        self, parameter: Union[Parameter, Reference]
    ) -> Parameter:
        if isinstance(parameter, Reference):
            resolved_parameter: sob.abc.Model = (
                self._resolver.resolve_reference(parameter, types=(Parameter,))
            )
            assert isinstance(resolved_parameter, Parameter)
            parameter = resolved_parameter
        return parameter

    def _resolve_schema(self, schema: Union[Reference, Schema]) -> Schema:
        if isinstance(schema, Reference):
            resolved_schema: sob.abc.Model = self._resolver.resolve_reference(
                schema, types=(Schema,)
            )
            assert isinstance(resolved_schema, Schema)
            schema = resolved_schema
        return schema

    def _resolve_operation(
        self, operation: Union[Reference, Operation]
    ) -> Operation:
        if isinstance(operation, Reference):
            resolved_operation: sob.abc.Model = (
                self._resolver.resolve_reference(operation, types=(Operation,))
            )
            assert isinstance(resolved_operation, Operation)
            operation = resolved_operation
        return operation

    def _resolve_path_item(
        self, path_item: Union[Reference, PathItem]
    ) -> PathItem:
        if isinstance(path_item, Reference):
            resolved_path_item: sob.abc.Model = (
                self._resolver.resolve_reference(path_item, types=(PathItem,))
            )
            assert isinstance(resolved_path_item, PathItem)
            path_item = resolved_path_item
        return path_item

    def _resolve_request_body(
        self, request_body: Union[Reference, RequestBody]
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

    def _resolve_encoding(
        self, encoding: Union[Reference, Encoding]
    ) -> Encoding:
        if isinstance(encoding, Reference):
            resolved_encoding: sob.abc.Model = (
                self._resolver.resolve_reference(encoding, types=(Encoding,))
            )
            assert isinstance(resolved_encoding, Encoding)
            encoding = resolved_encoding
        return encoding

    @property  # type: ignore
    @_dict_str_model_lru_cache()
    def _pointers_classes(self) -> Dict[str, Type[sob.abc.Model]]:
        path: str = os.path.abspath(self._model_path)
        current_directory: str = os.path.abspath(os.curdir)
        namespace: Dict[str, Any] = {"__file__": path}
        os.chdir(os.path.dirname(path))
        try:
            with open(path) as module_io:
                exec(module_io.read(), namespace)
        finally:
            os.chdir(current_directory)
        return namespace.get("_POINTERS_CLASSES")  # type: ignore

    def _iter_imports(self) -> Iterable[str]:
        """
        Return an iterable of sorted import statements
        """
        import_statement: str
        return sorted(
            self._imports,
            key=lambda import_statement: (
                (1, import_statement)
                if import_statement.startswith("from ")
                else (0, import_statement)
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

    def _get_model_module_import(self, client_module_path: str) -> str:
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
    def _get_client_base_class_import(self, client_module_path: str) -> str:
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
            except Exception:
                pass
        return (
            f"from {base_class_module} "
            f"import {self._base_class.__name__}{as_}"
        )

    def _get_security_schemes(self) -> Optional[SecuritySchemes]:
        return (
            self.open_api.security_definitions
            or self.open_api.components.security_schemes
            if self.open_api.components
            else None
        )

    def _iter_security_schemes(self) -> Iterable[SecurityScheme]:
        security_schemes: Optional[
            SecuritySchemes
        ] = self._get_security_schemes()
        yield from (security_schemes or {}).values()

    @_lru_cache()
    def _get_api_key_in(self) -> str:
        """
        Determine the location where an API key should be provided
        (header, query, or cookie) (see https://bit.ly/3LQua3X).
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
        where an API key should be provided (see https://bit.ly/3LQua3X).
        """
        security_scheme: SecurityScheme
        for security_scheme in self._iter_security_schemes():
            # Use the first API key security scheme
            if security_scheme.type_ == "apiKey" and security_scheme.name:
                return security_scheme.name
        return "X-API-KEY"

    def _iter_oauth2_flows(self) -> Iterable[Tuple[str, Optional[OAuthFlow]]]:
        security_scheme: SecurityScheme
        for security_scheme in self._iter_security_schemes():
            # Use the first API key security scheme
            if security_scheme.type_ == "oauth2":
                if security_scheme.flows:
                    yield from filter(
                        None,
                        sob.utilities.inspect.properties_values(
                            security_scheme.flows
                        ),
                    )
                if security_scheme.flow:
                    yield (
                        "authorizationCode"
                        if security_scheme.flow == "accessCode"
                        else "clientCredentials"
                        if security_scheme.flow == "application"
                        else security_scheme.flow
                    ), None

    @_lru_cache()
    def _get_oauth2_authorization_url(self) -> str:
        """
        Get the OAuth2 authorization URL, if one is provided
        (https://bit.ly/3DYK7Cx).
        """
        name: str
        flow: Optional[OAuthFlow]
        for name, flow in self._iter_oauth2_flows():
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
        (https://bit.ly/3DYK7Cx).
        """
        name: str
        flow: Optional[OAuthFlow]
        for name, flow in self._iter_oauth2_flows():
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
        (https://bit.ly/3DYK7Cx).
        """
        name: str
        flow: Optional[OAuthFlow]
        for name, flow in self._iter_oauth2_flows():
            if flow and flow.refresh_url:
                return flow.refresh_url
        return ""

    @_lru_cache()
    def _get_oauth2_flow_names(self) -> Tuple[str, ...]:
        """
        Get a `tuple` of supported OAuth2 flow names (https://bit.ly/3v96JfA).
        """
        item: Tuple[str, Optional[OAuthFlow]]
        return tuple(
            sorted(
                unique_everseen(
                    map(lambda item: item[0], self._iter_oauth2_flows())
                )
            )
        )

    @_lru_cache()
    def _get_open_id_connect_url(self) -> str:
        """
        Get the OpenID Connect URL, if one is provided
        (https://bit.ly/3DYK7Cx).
        """
        security_scheme: SecurityScheme
        for security_scheme in self._iter_security_schemes():
            if security_scheme.open_id_connect_url:
                return security_scheme.open_id_connect_url
        return ""

    def _iter_class_docstring_source(self) -> Iterable[str]:
        if Client.__doc__:
            docstring: str = re.sub(
                r"\n.*base class.*\n+", r"\n", Client.__doc__
            )
            if self._include_init_parameters:
                matched: Optional[Match] = re.match(
                    (
                        r"^((?:.|\n)*?\n    Initialization Parameters:\n)"
                        r"((?:.|\n)*?)(\n+    (?:[^ -](?:.|\n)*)?)$"
                    ),
                    docstring,
                )
                assert matched
                prefix: str
                parameter_documentation: str
                suffix: str
                prefix, parameter_documentation, suffix = matched.groups()
                parameter_name: str
                for parameter_name in self._iter_excluded_parameter_names():
                    pattern: str = (
                        f"\\n    - {parameter_name}\\b(?:.|\\n)*?"
                        r"(\n    - |(\n|\s)*$)"
                    )
                    assert re.search(pattern, parameter_documentation), pattern
                    parameter_documentation = re.sub(
                        pattern, r"\1", parameter_documentation
                    )
                parameter_doc: str
                for parameter_doc in self._add_init_parameter_docs:
                    parameter_doc = sob.utilities.string.indent(
                        parameter_doc.lstrip(" -"), number_of_spaces=6, start=0
                    )
                    parameter_doc = (
                        sob.utilities.string.split_long_docstring_lines(
                            parameter_doc
                        )
                    ).lstrip()
                    parameter_documentation = (
                        f"{parameter_documentation}\n    - {parameter_doc}"
                    )
                yield (
                    f'    """{prefix}{parameter_documentation}'
                    f'{suffix or ""}"""'
                )
            else:
                yield f'    """{docstring}"""'
            yield ""

    def _iter_class_declaration_source(self) -> Iterable[str]:
        class_declaration: str = (
            f"class {self._class_name}"
            f"({self._get_client_base_class_name()}):"
        )
        if len(class_declaration) > sob.utilities.string.MAX_LINE_LENGTH:
            class_declaration = (
                f"class {self._class_name}(\n"
                f"    {self._get_client_base_class_name()}\n"
                "):"
            )
        yield class_declaration
        yield from self._iter_class_docstring_source()
        yield (
            "    __slots__: typing.Tuple[str, ...] = "
            "oapi.client.CLIENT_SLOTS"
        )
        yield ""

    def _get_schema_class(
        self, schema: Union[Schema, Parameter]
    ) -> Type[sob.abc.Model]:
        relative_url: str = self._resolver.get_relative_url(
            sob.meta.get_url(schema) or ""
        )
        pointer: str = (sob.meta.get_pointer(schema) or "").lstrip("#")
        relative_url_pointer: str = f"{relative_url}#{pointer}"
        try:
            return self._pointers_classes[relative_url_pointer]
        except KeyError:
            if schema.type_ == "object" or (
                isinstance(schema, Schema)
                and (schema.properties or schema.additional_properties)
            ):
                return sob.model.Dictionary
            elif schema.type_ == "array" or schema.items:
                return sob.model.Array
            else:
                raise

    def _get_schema_type(
        self, schema: Union[Schema, Parameter]
    ) -> Union[Type[sob.abc.Model], sob.abc.Property]:
        try:
            return self._get_schema_class(schema)
        except KeyError:
            if schema.type_ == "object" or (
                isinstance(schema, Schema)
                and schema.type_ is None
                and (schema.properties or schema.additional_properties)
            ):
                return sob.model.Dictionary
            elif schema.type_ == "array" or (
                (schema.type_ is None) and schema.items
            ):
                return sob.model.Array
            elif schema.type_ == "number":
                self._imports.add("import decimal")
                return sob.properties.Number()
            elif schema.type_ == "string":
                return sob.properties.String()
            elif schema.type_ == "integer":
                return sob.properties.Integer()
            elif schema.type_ == "boolean":
                return sob.properties.Boolean()
            elif schema.type_ == "file":
                return sob.properties.Bytes()
            else:
                raise ValueError(f"Missing `type_`: {repr(schema)}")

    def _get_parameter_or_schema_type(
        self, schema: Union[Schema, Parameter]
    ) -> Union[Type[sob.abc.Model], sob.abc.Property]:
        if isinstance(schema, Parameter):
            if schema.schema:
                return self._get_parameter_or_schema_type(
                    self._resolve_schema(schema.schema)
                )
            else:
                if schema.content:
                    media_type: MediaType = next(  # type: ignore
                        iter(schema.content.values())
                    )
                    if media_type.schema:
                        return self._get_parameter_or_schema_type(
                            self._resolve_schema(media_type.schema)
                        )
        return self._get_schema_type(schema)

    def _iter_response_types(
        self, response: Response
    ) -> Iterable[Union[Type[sob.abc.Model], sob.abc.Property]]:
        schema: Schema
        resolved_schema: sob.abc.Model
        if response.schema:
            schema = self._resolve_schema(response.schema)
            yield self._get_parameter_or_schema_type(schema)
        if response.content:
            media_type_name: str
            media_type: Union[MediaType, Reference]
            for media_type_name, media_type in response.content.items():
                media_type = self._resolve_media_type(media_type)
                if media_type.schema:
                    schema = self._resolve_schema(media_type.schema)
                    yield self._get_parameter_or_schema_type(schema)

    def _iter_operation_response_types(
        self, operation: Operation
    ) -> Iterable[Union[Type[sob.abc.Model], sob.abc.Property]]:
        """
        Yield classes for all responses with a status code in the 200-299 range
        """
        if operation.responses:
            code: str
            response: Union[Response, Reference]
            for code, response in operation.responses.items():
                if code.startswith("2"):
                    yield from self._iter_response_types(
                        self._resolve_response(response)
                    )

    def _iter_type_names(
        self, type_: Union[Type[sob.abc.Model], sob.abc.Property]
    ) -> Iterable[str]:
        if isinstance(type_, sob.abc.Number):
            self._imports.add("import decimal")
            yield from ("int", "float", "decimal.Decimal")
        elif isinstance(type_, sob.abc.String):
            yield "str"
        elif isinstance(type_, sob.abc.Integer):
            yield "int"
        elif isinstance(type_, sob.abc.Boolean):
            yield "bool"
        elif isinstance(type_, sob.abc.Bytes):
            yield "bytes"
        else:
            assert isinstance(type_, type) and issubclass(type_, sob.abc.Model)
            model_module_name: str = (
                "sob.abc"
                if type_.__module__ in ("sob.model", "sob.abc")
                else self._get_model_module_name()
            )
            yield f"{model_module_name}.{type_.__name__}"

    def _iter_schema_type_names(
        self, schema: Union[Schema, Parameter]
    ) -> Iterable[str]:
        yield from self._iter_type_names(
            self._get_parameter_or_schema_type(schema)
        )

    def _get_simple_schema_type_hint(self, type_: Optional[str]) -> str:
        if type_ == "number":
            self._imports.add("import decimal")
            return (
                "typing.Union[\n"
                "        int,\n"
                "        float,\n"
                "        decimal.Decimal\n"
                "    ]"
            )
        elif type_ == "string":
            return "str"
        elif type_ == "integer":
            return "int"
        elif type_ == "boolean":
            return "bool"
        elif type_ == "file":
            return "typing.IO[bytes]"
        else:
            raise ValueError(type_)

    def _get_schema_type_hint(
        self, schema: Union[Schema, Parameter], required: bool = False
    ) -> str:
        type_names: Tuple[str, ...] = tuple(
            self._iter_schema_type_names(schema)
        )
        assert type_names
        type_hint: str
        if required:
            if len(type_names) == 1:
                type_hint = type_names[0]
            else:
                type_hint = ",\n            ".join(type_names)
                type_hint = "typing.Union[\n"
                f"            {type_hint}\n"
                "        ]"
        else:
            if len(type_names) == 1:
                type_hint = (
                    "typing.Optional[\n"
                    f"            {type_names[0]}\n"
                    "        ] = None"
                )
            else:
                type_names += ("None",)
                type_hint = ",\n            ".join(type_names)
                type_hint = (
                    "typing.Union[\n"
                    f"            {type_hint}\n"
                    "        ] = None"
                )
        return type_hint

    def _get_parameter_type_hint(self, parameter: Parameter) -> str:
        schema: Union[Parameter, Schema] = parameter
        if parameter.schema:
            schema = self._resolve_schema(parameter.schema)
        return self._get_schema_type_hint(
            schema, required=bool(parameter.required)
        )

    def _iter_parameter_method_source(
        self,
        parameter: Parameter,
        parameter_locations: _ParameterLocations,
    ) -> Iterable[str]:
        """
        Yield lines for a parameter declaration
        """
        if parameter.name:
            parameter_name: str = sob.utilities.string.property_name(
                parameter.name
            ).rstrip("_")
            if parameter.in_ and not (
                (
                    parameter.in_ == "header"
                    and parameter.name.lower()
                    in (
                        # See: https://bit.ly/3iUmvVZ
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
            ):
                # See: https://bit.ly/3uetijD
                style: str = parameter.style or (
                    "form"
                    if parameter.in_ in ("query", "cookie")
                    else "simple"
                    if parameter.in_ in ("path", "header")
                    else ""
                )
                explode: bool = (
                    (True if style in ("form", "deepObject") else False)
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
                    and self._get_open_api_major_version() == 2
                ):
                    style = "form"
                    explode = False
                getattr(
                    parameter_locations,
                    sob.utilities.string.property_name(parameter.in_),
                )[parameter_name] = _Parameter(
                    name=parameter.name,
                    types=sob.types.Types(
                        [self._get_parameter_or_schema_type(parameter)]
                    ),
                    # See: https://bit.ly/3JaCXMF
                    explode=explode,
                    style=style,
                    description=parameter.description or "",
                    index=parameter_locations.total_count,
                )
                parameter_locations.total_count += 1
                type_hint: str = self._get_parameter_type_hint(parameter)
                yield f"        {parameter_name}: {type_hint},"

    def _represent_type(
        self, type_: Union[Type[sob.abc.Model], sob.abc.Property]
    ) -> str:
        if isinstance(type_, sob.abc.Property):
            return sob.utilities.inspect.represent(type_)
        assert isinstance(type_, type) and issubclass(type_, sob.abc.Model)
        if type_.__module__.startswith("sob."):
            return f"{type_.__module__}.{type_.__name__}"
        else:
            return f"{self._get_model_module_name()}.{type_.__name__}"

    def _iter_operation_method_definition(
        self,
        path: str,
        method: str,
        operation: Operation,
        parameter_locations: _ParameterLocations,
    ) -> Iterable[str]:
        operation_response_types: Tuple[
            Union[Type[sob.abc.Model], sob.abc.Property], ...
        ] = tuple(self._iter_operation_response_types(operation))
        if operation_response_types:
            yield "        response: sob.abc.Readable = self.request("
        else:
            yield "        self.request("
        yield from _iter_request_path_representation(path, parameter_locations)
        yield f'            method="{method.upper()}",'
        # If more than 254 arguments are needed, we must use `**kwargs``
        use_kwargs: bool = (
            len(tuple(_iter_parameters(parameter_locations))) > 254
        )
        yield from _iter_request_headers_representation(
            parameter_locations, use_kwargs=use_kwargs
        )
        yield from _iter_request_query_representation(
            parameter_locations, use_kwargs=use_kwargs
        )
        yield from _iter_request_form_data_representation(
            parameter_locations, use_kwargs=use_kwargs
        )
        yield from _iter_request_body_representation(
            parameter_locations, use_kwargs=use_kwargs
        )
        yield "        )"
        if operation_response_types:
            response_types_representation: str = ",\n                ".join(
                unique_everseen(
                    map(self._represent_type, operation_response_types)
                )
            )
            yield "        return sob.model.unmarshal(  # type: ignore"
            yield "            sob.model.deserialize(response),"
            yield "            types=("
            yield f"                {response_types_representation},"
            yield "            )"
            yield "        )"
        yield ""

    def _iter_operation_method_docstring(
        self, operation: Operation, parameter_locations: _ParameterLocations
    ) -> Iterable[str]:
        yield '        """'
        if operation.description or operation.summary:
            yield sob.utilities.string.split_long_docstring_lines(
                "\n{}        ".format(
                    sob.utilities.string.indent(
                        (
                            operation.description or operation.summary or ""
                        ).strip(),
                        number_of_spaces=8,
                        start=0,
                    )
                )
            ).lstrip("\n")
        sorted_parameters: Tuple[Tuple[str, _Parameter], ...] = tuple(
            _iter_sorted_parameters(parameter_locations)
        )
        if sorted_parameters:
            if operation.description or operation.summary:
                yield ""
            yield "        Parameters:"
            yield ""
            name: str
            parameter: _Parameter
            for name, parameter in sorted_parameters:
                parameter_docstring: str = f"        - {name}"
                if parameter.description:
                    description: str = re.sub(
                        r"\n[\s\n]*\n+", "\n", parameter.description.strip()
                    )
                    description = sob.utilities.string.indent(
                        description, 10, start=0
                    )
                    description = (
                        sob.utilities.string.split_long_docstring_lines(
                            description
                        )
                    )
                    parameter_docstring = (
                        f"{parameter_docstring}:\n{description}"
                    )
                yield parameter_docstring
        yield '        """'

    def _iter_operation_method_source(
        self,
        path: str,
        method: str,
        operation: Operation,
        path_item: PathItem,
    ) -> Iterable[str]:
        # This dictionary will be passed to
        # `self._iter_operation_method_declaration()`
        # in order to capture information about the parameters
        parameter_locations: _ParameterLocations = _ParameterLocations()
        operation_method_declaration: Tuple[str, ...] = tuple(
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
        if len(operation_method_declaration) > 258:
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

    def _iter_request_body_parameter_method_source(
        self,
        request_body: RequestBody,
        parameter_locations: _ParameterLocations,
        parameter_names: Set[str],
    ) -> Iterable[str]:
        encoding: Union[Reference, Encoding]
        schema: Schema
        media_type: MediaType
        media_type_name: str
        type_hint: str
        if request_body.content:
            for media_type_name, media_type in request_body.content.items():
                if media_type_name == "application/json":
                    assert media_type.schema
                    schema = self._resolve_schema(media_type.schema)
                    schema_type: Union[
                        Type[sob.abc.Model], sob.abc.Property
                    ] = self._get_parameter_or_schema_type(schema)
                    parameter_name: str
                    if isinstance(schema_type, type):
                        parameter_name = sob.utilities.string.property_name(
                            schema_type.__name__
                        )
                        while parameter_name in parameter_names:
                            parameter_name = f"{parameter_name}_"
                    else:
                        parameter_name = "data_"
                    parameter_locations.body = _Parameter(
                        name=parameter_name,
                        types=sob.types.Types([schema_type]),
                        index=parameter_locations.total_count,
                    )
                    parameter_locations.total_count += 1
                    type_hint = self._get_schema_type_hint(
                        schema, required=bool(request_body.required)
                    )
                    yield f"        {parameter_name}: {type_hint},"
                elif media_type_name in (
                    "multipart",
                    "application/x-www-form-urlencoded",
                ):
                    # Treat the request body as form data
                    assert media_type.encoding
                    assert media_type.schema
                    name: str
                    for name, encoding in media_type.encoding.items():
                        encoding = self._resolve_encoding(encoding)
                    schema = self._resolve_schema(media_type.schema)
                    assert schema.type_ == "object"
                    # Add each property as if it were a parameter
                    # where in == "formData"
                    # TODO
                    raise NotImplementedError(media_type_name)
                else:
                    raise NotImplementedError(media_type_name)

    def _get_parameter_name(
        self, parameter: Union[Parameter, Reference]
    ) -> str:
        resolved_parameter: Parameter = self._resolve_parameter(parameter)
        return resolved_parameter.name or ""

    def _get_operation_response_type_hint(self, operation: Operation) -> str:
        response_type_hint: str = "None"
        response_types: Tuple[
            Union[Type[sob.abc.Model], sob.abc.Property], ...
        ] = tuple(self._iter_operation_response_types(operation))
        if response_types:
            response_type_names: Tuple[str, ...] = tuple(
                unique_everseen(
                    chain(*map(self._iter_type_names, response_types))
                )
            )
            assert response_type_names
            if len(response_type_names) > 1:
                response_class_names: str = ",\n        ".join(
                    response_type_names
                )
                response_type_hint = (
                    f"typing.Union[\n        {response_class_names}\n    ]"
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
    ) -> Iterable[str]:
        parameter: Parameter
        previous_parameter_required: bool = True
        method_name: str = (
            f"{method}_{sob.utilities.string.property_name(path)}"
        ).rstrip("_")
        yield f"    def {method_name}("
        yield "        self,"
        # Request Body
        request_body: Optional[RequestBody] = None
        parameter_names: Set[str] = set(
            map(
                sob.utilities.string.property_name,
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
                yield from self._iter_request_body_parameter_method_source(
                    request_body,
                    parameter_locations=parameter_locations,
                    parameter_names=parameter_names,
                )
        # Parameters
        if operation.parameters or path_item.parameters:
            # We keep track of traversed parameter names to avoid doubling
            # up if the same parameter is defined for the path item and
            # the operation
            traversed_parameters: Set[str] = set()
            for parameter in sorted(
                map(
                    self._resolve_parameter,
                    chain(
                        operation.parameters or (), path_item.parameters or ()
                    ),
                ),
                key=lambda parameter: 0 if parameter.required else 1,
            ):
                assert parameter.name
                if parameter.name not in traversed_parameters:
                    parameter_method_source: Tuple[str, ...] = tuple(
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
            yield from self._iter_request_body_parameter_method_source(
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
    ) -> Iterable[str]:
        name: str
        operation: Union[Operation, Reference]
        for name, operation in _iter_path_item_operations(path_item):
            yield from self._iter_operation_method_source(
                path,
                name,
                self._resolve_operation(operation),
                path_item=path_item,
            )

    def _iter_excluded_parameter_names(self) -> Iterable[str]:
        if self._include_init_parameters:
            parameter_name: str
            for parameter_name in inspect.signature(
                Client.__init__
            ).parameters.keys():
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
        default_value: Any
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
        item: Tuple[str, Any]
        for parameter_name, default_representation in chain(
            map(
                lambda item: (
                    item[0],
                    sob.utilities.inspect.represent(item[1]),
                ),
                # Both key and value must resolve to `True` when cast as `bool`
                filter(
                    all,
                    self._init_parameter_defaults.items(),
                ),
            ),
            self._init_parameter_defaults_source.items(),
        ):
            pattern: Pattern
            if parameter_name == "url":
                # The `url` is our only *positional* argument
                pattern = re.compile(
                    f"(\\n\\s*{parameter_name}:"
                    r"(?:.|\n)*?)()"
                    r"(,?\n\s*(?:[\w_]+|\)):)"
                )
            else:
                pattern = re.compile(
                    f"(\\n\\s*{parameter_name}:"
                    r"(?:.|\n)*?=\s*)((?:.|\n)*?)"
                    r"(,?\n\s*(?:[\w_]+|\)):)"
                )
            matched: Optional[Match] = pattern.search(init_declaration_source)
            if matched:
                if (
                    sum(map(len, matched.groups()[:-1]))
                    # Characters needed for the default value
                    + len(default_representation)
                    # Characters needed for the assignment operator
                    + (3 if parameter_name == "url" else 0)
                ) > sob.utilities.string.MAX_LINE_LENGTH:
                    default_representation = sob.utilities.string.indent(
                        default_representation, number_of_spaces=12, start=0
                    )
                    default_representation = (
                        f"(\n{default_representation}\n        )"
                    )
                else:
                    default_representation = sob.utilities.string.indent(
                        default_representation, number_of_spaces=8
                    )
                if parameter_name == "url":
                    # The assignment operator will not have been included
                    # in the pattern match for `url`, since it is a
                    # positional argument
                    default_representation = f" = {default_representation}"
                init_declaration_source = pattern.sub(
                    f"\\g<1>{default_representation}\\g<3>",
                    init_declaration_source,
                )
        return init_declaration_source

    def _insert_add_init_parameters(self, init_source: str) -> str:
        if self._add_init_parameters:
            assert "\n    ) -> None:" in init_source
            partitions: Tuple[str, str, str] = init_source.rpartition(
                "\n    ) -> None:"
            )
            parameter_declaration: str
            init_source = "".join(
                chain(
                    partitions[:1],
                    map(
                        lambda parameter_declaration: (
                            "\n        {},".format(
                                parameter_declaration.lstrip().rstrip(" ,\n")
                            )
                        ),
                        self._add_init_parameters,
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
                "Client"
                r')(?:"|\b)'
            ),
            r"oapi.client.\1",
            re.sub(
                (
                    r"\b("
                    "Tuple|Type|Callable|Optional|Mapping|Union|Sequence|"
                    "Any"
                    r")\b"
                ),
                r"typing.\1",
                source.replace("  # Force line-break retention\n", "\n"),
            ),
        )

    def _iter_init_method_source(self) -> Iterable[str]:
        if self._init_decorator:
            yield sob.utilities.string.indent(self._init_decorator, start=0)
        # Resolve namespace discrepancies between `oap.client` and the
        # generated client module
        init_declaration_source: str = (
            self._resolve_source_namespace_discrepancies(
                sob.utilities.inspect.get_source(Client.__init__)
            )
        )
        declaration_end_marker: str = (
            '"""' if '"""' in init_declaration_source else ") -> None:"
        )
        init_declaration_source = "".join(
            init_declaration_source.rpartition(declaration_end_marker)[:-1]
        )
        yield self._insert_add_init_parameters(
            self._replace_init_parameter_defaults(
                self._remove_unused_init_parameters(init_declaration_source)
            )
        )
        yield "        super().__init__("
        for parameter_name in inspect.signature(Client).parameters.keys():
            if parameter_name != "self" and (
                (not self._include_init_parameters)
                or (parameter_name in self._include_init_parameters)
            ):
                yield f"            {parameter_name}={parameter_name},"
        yield "        )"
        yield ""

    def _iter_reduce_method_source(self) -> Iterable[str]:
        if self._include_init_parameters:
            reduce_method_source: str = (
                self._resolve_source_namespace_discrepancies(
                    sob.utilities.inspect.get_source(Client.__reduce__)
                )
            )
            parameter_name: str
            for parameter_name in self._iter_excluded_parameter_names():
                reduce_method_source = re.sub(
                    f"\\n\\s+self\\._?{parameter_name},\\n",
                    r"\n",
                    reduce_method_source,
                )
            yield f"{reduce_method_source}"

    def _iter_paths_operations_methods_source(self) -> Iterable[str]:
        path_item: Union[PathItem, Reference]
        if self.open_api.paths:
            for path, path_item in self.open_api.paths.items():
                yield from self._iter_path_methods_source(
                    path, self._resolve_path_item(path_item)
                )

    def get_source(self, path: str) -> str:
        """
        This generates source code for the client module.

        Parameters:

        - path (str): The file path for the client module. This is needed
          in order to determine the relative import for the model module.
        """
        source: str = "\n".join(
            chain(
                self._iter_class_declaration_source(),
                self._iter_init_method_source(),
                self._iter_reduce_method_source(),
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
        return sob.utilities.string.suffix_long_lines(
            f"{imports}\n\n\n{source.rstrip()}\n"
        )

    def save(self, path: str) -> None:
        """
        This method will save the generated module to a given path.
        """
        client_source: str = self.get_source(path=path)
        # Save the module
        with open(path, "w") as model_io:
            model_io.write(client_source)

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._model_path == other._model_path
            and self.open_api == other.open_api
        )
