import gzip
import json
import pipes
import re
import ssl
import urllib
from warnings import warn
import sob
import os
from abc import ABC, abstractmethod
from functools import wraps
from http.client import HTTPResponse
from logging import Logger
from time import sleep
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, urlencode, urlparse
from urllib.request import Request, urlopen
from .oas.model import OpenAPI

# region Client ABC


class SSLContext(ssl.SSLContext):
    """
    This class is a wrapper for `ssl.SSLContext` which makes it possible to
    pickle a client.
    """

    def __init__(self, check_hostname: bool = True) -> None:
        if check_hostname:
            self.load_default_certs()
        else:
            self.check_hostname = False
            self.verify_mode = ssl.CERT_NONE
        super().__init__()

    def __reduce__(self) -> Tuple:
        """
        A pickled instance of this class will just be an entirely new
        instance.
        """
        return SSLContext, (self.check_hostname,)


SSL_CONTEXT: SSLContext = SSLContext(check_hostname=True)


def _censor_long_json_strings(text: str, limit: int = 2000) -> str:
    """
    Replace JSON strings (such as base-64 encoded images) longer than `limit`
    with "...".
    """
    return re.sub('"%s[^"]*"' % ('[^"]' * limit), '"..."', text)


def get_request_curl(
    request: Request,
    options: str = "-i --compressed",
    censored_headers: Iterable[str] = (
        "X-api-key",
        "Authorization",
    ),
) -> str:
    """
    Render an instance of `urllib.Request` as a `curl` command.

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
        return "-H {}".format(pipes.quote(f"{key}: {value}"))

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
                (
                    f"-d {pipes.quote(request.data.decode('utf-8'))}"
                    if request.data
                    else ""
                ),
                pipes.quote(request.full_url),
            ),
        )
    )


def _set_request_callback(
    request: Request, callback: Callable = print
) -> None:
    """
    Perform a callback on an HTTP request at the time it is submitted
    """
    callback(get_request_curl(request))


def _set_response_callback(
    response: HTTPResponse, callback: Callable = print
) -> None:
    """
    Perform a callback on an HTTP response at the time it is read
    """

    def response_read(amt: Optional[int] = None) -> bytes:
        data: bytes = HTTPResponse.read(response, amt)
        content_encoding: str
        for content_encoding in response.getheader(
            "Contents-encoding", ""
        ).split(","):
            content_encoding = content_encoding.strip().lower()
            if content_encoding and content_encoding == "gzip":
                data = gzip.decompress(data)
        headers: str = "\n".join(
            f"{key}: {value}" for key, value in response.headers.items()
        )
        body: str = (
            f'\n\n{str(data, encoding="utf-8", errors="ignore")}'
            if data
            else ""
        )
        callback(
            f"{response.geturl()}\n"
            f"Status: {response.getcode()}\n"
            f"{headers}"
            f"{body}"
        )
        return data

    response.read = response_read  # type: ignore


def _default_retry_hook(error: Exception) -> bool:
    assert error
    return True


def retry(
    errors: Union[Tuple[Type[Exception], ...], Type[Exception]] = Exception,
    retry_hook: Callable[[Exception], bool] = _default_retry_hook,
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

        @wraps(function)
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


class Config:
    def __init__(
        self,
        timeout: int = 0,
        retry_number_of_attempts: int = 1,
        retry_for_exceptions: Tuple[Type[Exception], ...] = (
            HTTPError,
            ssl.SSLError,
            URLError,
            ConnectionError,
            TimeoutError,
        ),
        retry_hook: Callable[[Exception], bool] = _default_retry_hook,
    ) -> None:
        self.timeout = timeout
        self.retry_number_of_attempts = retry_number_of_attempts
        self.retry_for_errors = retry_for_exceptions
        self.retry_hook = retry_hook

    def __reduce__(
        self,
    ) -> Tuple[
        Type["Config"],
        Tuple[
            int, int, Tuple[Type[Exception], ...], Callable[[Exception], bool]
        ],
    ]:
        return self.__class__, (
            self.timeout,
            self.retry_number_of_attempts,
            self.retry_for_errors,
            self.retry_hook,
        )

    def authenticate(self, request: Request) -> None:
        pass


def _format_request_data(
    data: Optional[Union[str, bytes, sob.abc.Model, Mapping]]
) -> Optional[bytes]:
    # Cast `data` as a `str`
    if isinstance(data, sob.abc.Model):
        data = sob.model.serialize(data, "json")
    elif isinstance(data, Mapping):
        data = json.dumps(data)
    # Convert `str` data to `bytes`
    formatted_data: Optional[bytes]
    if isinstance(data, str):
        formatted_data = bytes(data, encoding="utf-8")
    else:
        formatted_data = data
    return formatted_data


class Client(ABC):
    """
    This is an abstract base class, descendants of which represent a
    client connection
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        logger: Optional[Logger] = None,
        echo: bool = False,
        url: str = "",
    ) -> None:
        """
        Parameters:

        - config (oapi.client.Config):
          This is an object denoting configurations needed to create requests,
          and which is responsible for authenticating requests.
        - logger (logging.Logger|None) = None:
          A `logging.Logger` to which requests should be logged.
        - echo (bool) = False: If `True`, requests/responses are printed as
          they occur
        - url (str) = "": If provided, this value will be used as the base
          URL for API requests.
        """
        self.config: Config = config or Config()
        self.logger: Optional[Logger] = logger
        self.echo: bool = echo
        self._url: str = url

    @property
    @abstractmethod
    def url(self) -> str:
        """
        This is the base URL for the API, and must be overridden by
        sub-classes.
        """
        return self._url

    def __reduce__(
        self,
    ) -> Tuple[Type["Client"], Tuple[Config, Optional[Logger], bool, str]]:
        return self.__class__, (self.config, self.logger, self.echo, self._url)

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
        data: Optional[Union[str, bytes, sob.abc.Model, Mapping]] = None,
        query: Union[Mapping[str, str], Sequence[Tuple[str, str]]] = (),
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
                Optional[Union[str, bytes, sob.abc.Model, Mapping]],
                Union[Mapping[str, str], Sequence[Tuple[str, str]]],
                int,
            ],
            sob.abc.Readable,
        ] = self._request
        # Wrap the _request method with a retry decorator if more
        # than one attempt is specified in the config
        if self.config.retry_number_of_attempts > 1:
            request = retry(
                errors=self.config.retry_for_errors,
                number_of_attempts=self.config.retry_number_of_attempts,
                retry_hook=self.config.retry_hook,
                logger=self.logger,
            )(self._request)
        return request(path, method, data, query, timeout)

    def _request(
        self,
        path: str,
        method: str,
        data: Optional[Union[str, bytes, sob.abc.Model, Mapping]] = None,
        query: Union[Mapping[str, str], Sequence[Tuple[str, str]]] = (),
        timeout: int = 0,
    ) -> sob.abc.Readable:
        if query:
            path = f"{path}?{urlencode(query)}"
        # Prepend the base URL, if the URL is relative
        parse_result: ParseResult = urlparse(path)
        if parse_result.scheme:
            url = path
        else:
            assert path[0] == "/"
            url = "{}{}".format(self.url, path)
        # Assemble the request
        request = Request(url, data=_format_request_data(data), method=method)
        # Authenticate the request
        self.config.authenticate(request)
        # Default headers
        if "Accept" not in request.headers:
            request.headers["Accept"] = "application/json"
        if "Content-type" not in request.headers:
            request.headers["Content-type"] = "application/json"
        # Assemble keyword arguments for passing to `urllib.request.urlopen`
        request_keywords: Dict[str, Any] = {"context": SSL_CONTEXT}
        if timeout:
            request_keywords.update(timeout=timeout)
        elif self.config.timeout:
            request_keywords.update(timeout=self.config.timeout)
        # Add callback
        _set_request_callback(request, self._get_request_response_callback())
        response: HTTPResponse
        # Process the request
        try:
            response = urllib.request.urlopen(request, **request_keywords)
            # Add callback
            _set_response_callback(
                response, self._get_request_response_callback()
            )
        except urllib.error.HTTPError as error:
            response = getattr(error, "file")
            # Add callback
            _set_response_callback(
                response, self._get_request_response_callback(error=error)
            )
            # Invoke callback
            response.read()
            raise
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
    """

    def __init__(
        self, open_api: Union[str, sob.abc.Readable, OpenAPI], model_path: str
    ) -> None:
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
        assert os.path.exists(model_path)
        self.open_api: OpenAPI = open_api
        self.model_path: str = model_path
