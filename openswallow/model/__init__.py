"""
Version 2x: https://swagger.io/docs/specification/2-0/basic-structure/
Version 3x: https://swagger.io/specification
"""

import collections
import json
from collections import OrderedDict
from copy import copy
from numbers import Number
from typing import List, Union, Any

from marshmallow import missing, Schema

Missing = type(missing)


def get_schema(model):
    # type: (type) -> schemas.JSONObjectSchema
    return model.__schema__


def get_data(o):
    # type: (Union[Dict, Sequence]) -> schemas.JSONObjectSchema
    return o._data if hasattr(o, '_data') else o



class JSONObject(object):

    __schema__ = None

    def __iter__(self):
        for k in dir(self):
            if k[0] != '_':
                v = getattr(self, k)
                if not isinstance(v, (collections.Callable, Missing)):
                    yield k, v

    def __setattr__(
        self,
        attribute,
        value
    ):
        if isinstance(value, (JSONDict, JSONList, JSONObject, str, bytes, Number)):
            pass
        elif isinstance(value, dict):
            value = JSONDict(value)
        elif isinstance(value, collections.Sequence):
            value = JSONList(value)
        super().__setattr__(attribute, value)

    def __copy__(self):
        return self.__class__(**{
            k: copy(v) for k, v in self
        })

    @property
    def _data(self):
        return get_schema(self)(strict=True, many=False).dump(self, many=False).data

    def __str__(self):
        return get_schema(self)(strict=True, many=False).dumps(self, many=False).data


class JSONList(list):

    def __setitem__(self, index, value):
        # type: (str, collections.Sequence) -> None
        if isinstance(value, dict) and not isinstance(value, JSONDict):
            value = JSONDict(value)
        elif isinstance(value, collections.Sequence) and (not isinstance(value, self.__class__)):
            value = self.__class__(value)
        super().__setitems__(index, value)

    @property
    def _data(self):
        return [
            get_data(v for v in self)
        ]

    def __str__(self):
        return json.dumps(get_data(self))


class JSONDict(OrderedDict):

    def __setitem__(self, key, value):
        # type: (str, Any) -> None
        if isinstance(value, dict) and not isinstance(value, self.__class__):
            value = self.__class__(value)
        elif isinstance(value, collections.Sequence) and not isinstance(value, JSONList):
            value = JSONList(value)
        super().__setitem__(key, value)

    @property
    def _data(self):
        data = OrderedDict()
        for k, v in self.items():
            data[k] = get_data(v)
        return data

    def __str__(self):
        return json.dumps(get_data(self))


class Reference(JSONObject):

    def __init__(
        self,
        ref=missing,  # type: Union[str, Missing]
    ):
        self.ref = ref


class Info(JSONObject):
    """
    https://swagger.io/specification/#infoObject
    """

    def __init__(
        self,
        title=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        terms_of_service=missing,  # type: Union[str, Missing]
        contact=missing,  # type: Union[Contact, Missing]
        license=missing,  # type: Union[License, Missing]
        version=missing,  # type: Union[str, Missing]
    ):
        # type: (...) -> None
        self.title = title
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license = license
        self.version = version


class Tag(JSONObject):
    """
    https://swagger.io/specification/#tagObject
    """

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description


class Contact(JSONObject):
    """
    https://swagger.io/specification/#contactObject
    """

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        url=missing,  # type: Union[str, Missing]
        email=missing,  # type: Union[str, Missing]
    ):
        # type: (...) -> None
        self.name = name
        self.url = url
        self.email = email


class License(JSONObject):
    """
    https://swagger.io/specification/#licenseObject
    """

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        url=missing,  # type: Union[str, Missing]
    ):
        # type: (...) -> None
        self.name = name
        self.url = url


class Parameter(JSONObject):
    """
    https://swagger.io/specification/#parameterObject

    Properties:

        - name (str)

        - parameter_in (str):

            - "path"
            - "query"
            - "header"
            - "cookie"

        - description (str)

        - required (bool)

        - deprecated (bool)

        - allow_empty_value (bool): Sets the ability to pass empty-valued parameters. This is valid only for query
          parameters and allows sending a parameter with an empty value. The default value is ``False``. If ``style``
          is used, and if ``behavior`` is inapplicable (cannot be serialized), the value of ``allow_empty_value`` will
          be ignored.

        - style (str): Describes how the parameter value will be serialized, depending on the type of the parameter
          value.

            - "matrix": Path-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.7>`.
            - "label": Label-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.5>`.
            - "form": Form style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.8>`.
            - "simple": Simple style parameters defined by
              `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.2>`.
            - "spaceDelimited": Space separated array values.
            - "pipeDelimited": Pipe separated array values.
            - "deepObject": Provides a simple way of rendering nested objects using form parameters.

          Default values (based on value of ``location``):

            - query: "form"
            - path: "simple"
            - header: "simple"
            - cookie: "form"

          https://swagger.io/specification/#style-values-52

        - explode (bool): When this is ``True``, array or object parameter values generate separate parameters for
          each value of the array or key-value pair of the map. For other types of parameters this property has no
          effect. When ``style`` is "form", the default value is ``True``. For all other styles, the default value is
          ``False``.

        - allow_reserved (bool): Determines whether the parameter value SHOULD allow reserved characters
          :/?#[]@!$&'()*+,;= (as defined by `RFC3986 <https://tools.ietf.org/html/rfc3986#section-2.2>`) to be included
          without percent-encoding. This property only applies to parameters with a location value of "query". The
          default value is ``False``.

        - schema (Schematic): The schema defining the type used for the parameter.

        - example (Any): Example of the media type. The example should match the specified schema and encoding
          properties if present. The ``example`` parameter should not be present if ``examples`` is present. If
          referencing a ``schema`` which contains an example—*this* example overrides the example provided by the
          ``schema``. To represent examples of media types that cannot naturally be represented in JSON or YAML, a
          string value can contain the example with escaping where necessary.

        - examples (Dict[str, Example]): Examples of the media type. Each example should contain a value in the correct
          format, as specified in the parameter encoding. The ``examples`` parameter should not be present if
          ``example`` is present. If referencing a ``schema`` which contains an example—*these* example override the
          example provided by the ``schema``. To represent examples of media types that cannot naturally be represented
          in JSON or YAML, a string value can contain the example with escaping where necessary.

        - content ({str:MediaType}): A map containing the representations for the parameter. The key is the media type
          and the value describing it. The map must only contain one entry.

    ...for version 2x compatibility:

        - data_type (str)

        - enum ([Any])
    """

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        parameter_in=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        required=missing,  # type: Union[bool, Missing]
        deprecated=missing,  # type: Union[bool, Missing]
        allow_empty_value=missing, # type: Union[bool, Missing]
        style=missing,  # type: Union[str, Missing]
        explode=missing, # type: Union[bool, Missing]
        allow_reserved=missing, # type: Union[bool, Missing]
        schema=missing, # type: Union[Schematic, Missing]
        example=missing, # type: Any
        examples=missing, # type: Union[Dict[str, Example], Missing]
        content=missing,  # type: Union[Dict[str, MediaType], Missing]
        # 2x compatibility
        data_type=missing,  # type: Union[str, Missing]
        enum=missing,  # type: Union[Sequence[str], Missing]
    ):
        self.name = name
        self.parameter_in = parameter_in
        self.description = description
        self.required = required
        self.deprecated = deprecated
        self.allow_empty_value = allow_empty_value
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved
        self.schema = schema
        self.example = example
        self.examples = examples
        self.content = content
        # 2x compatibility
        self.data_type = data_type
        self.enum = enum if (enum is missing or enum is None) else list(enum)  # type: Union[Sequence[str], Missing]


class Header(JSONObject):
    """
    https://swagger.io/specification/#headerObject

     Properties:

         - description (str)

         - required (bool)

         - deprecated (bool)

         - allow_empty_value (bool): Sets the ability to pass empty-valued parameters. This is valid only for query
           parameters and allows sending a parameter with an empty value. The default value is ``False``. If ``style``
           is used, and if ``behavior`` is inapplicable (cannot be serialized), the value of ``allow_empty_value`` will
           be ignored.

         - style (str): Describes how the parameter value will be serialized, depending on the type of the parameter
           value.

             - "matrix": Path-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.7>`.
             - "label": Label-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.5>`.
             - "form": Form style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.8>`.
             - "simple": Simple style parameters defined by
               `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.2>`.
             - "spaceDelimited": Space separated array values.
             - "pipeDelimited": Pipe separated array values.
             - "deepObject": Provides a simple way of rendering nested objects using form parameters.

           Default values (based on value of ``location``):

             - query: "form"
             - path: "simple"
             - header: "simple"
             - cookie: "form"

           https://swagger.io/specification/#style-values-52

         - explode (bool): When this is ``True``, array or object parameter values generate separate parameters for
           each value of the array or key-value pair of the map. For other types of parameters this property has no
           effect. When ``style`` is "form", the default value is ``True``. For all other styles, the default value is
           ``False``.

         - allow_reserved (bool): Determines whether the parameter value SHOULD allow reserved characters
           :/?#[]@!$&'()*+,;= (as defined by `RFC3986 <https://tools.ietf.org/html/rfc3986#section-2.2>`) to be included
           without percent-encoding. This property only applies to parameters with a location value of "query". The
           default value is ``False``.

         - schema (Schematic): The schema defining the type used for the parameter.

         - example (Any): Example of the media type. The example should match the specified schema and encoding
           properties if present. The ``example`` parameter should not be present if ``examples`` is present. If
           referencing a ``schema`` which contains an example—*this* example overrides the example provided by the
           ``schema``. To represent examples of media types that cannot naturally be represented in JSON or YAML, a
           string value can contain the example with escaping where necessary.

         - examples (Dict[str, Example]): Examples of the media type. Each example should contain a value in the correct
           format, as specified in the parameter encoding. The ``examples`` parameter should not be present if
           ``example`` is present. If referencing a ``schema`` which contains an example—*these* example override the
           example provided by the ``schema``. To represent examples of media types that cannot naturally be represented
           in JSON or YAML, a string value can contain the example with escaping where necessary.

         - content ({str:MediaType}): A map containing the representations for the parameter. The key is the media type
           and the value describing it. The map must only contain one entry.
     """

    def __init__(
        self,
        description=missing,  # type: Union[str, Missing]
        required=missing,  # type: Union[bool, Missing]
        deprecated=missing,  # type: Union[bool, Missing]
        allow_empty_value=missing,  # type: Union[bool, Missing]
        style=missing,  # type: Union[str, Missing]
        explode=missing,  # type: Union[bool, Missing]
        allow_reserved=missing,  # type: Union[bool, Missing]
        schema=missing,  # type: Union[Schematic, Missing]
        example=missing,  # type: Any
        examples=missing,  # type: Union[Dict[str, Example], Missing]
        content=missing,  # type: Union[Dict[str, MediaType], Missing]
    ):
        self.description = description
        self.required = required
        self.deprecated = deprecated
        self.allow_empty_value = allow_empty_value
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved
        self.schema = schema
        self.example = example
        self.examples = examples
        self.content = content



class Encoding(JSONObject):

    """
    https://swagger.io/specification/#encodingObject
    """

    def __init__(
        self,
        content_type=missing,  # type: Union[str, Missing]
        headers=missing,  # type: Union[Dict[str, Union[Header, Reference]], Missing]
        style=missing,  # type: Union[str, Missing]
        explode=missing,  # type: Union[bool, Missing]
        allow_reserved=missing,  # type: Union[bool, Missing]
    ):
        self.content_type = content_type
        self.headers = headers
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved


class Example(JSONObject):
    """
    https://swagger.io/specification/#exampleObject
    """

    def __init__(
        self,
        summary=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        value=missing,  # type: Any
        external_value=missing,  # type: Union[str, Missing]
    ):
        self.summary = summary
        self.description = description
        self.value = value
        self.external_value = external_value


class Link(JSONObject):

    def __init__(
        self,
        operation_ref=missing,  # type: Union[str, Missing]
        operation_id=missing,  # type: Union[str, Missing]
        parameters=missing,  # type: Union[Dict[str, Any], Missing]
        request_body=missing,  # type: Any
        description=missing,  # type: Union[str, Missing]
        server=missing,  # type: Union[Server, Missing]
    ):
        self.operation_ref = operation_ref
        self.operation_id = operation_id
        self.parameters = parameters
        self.request_body = request_body
        self.description = description
        self.server = server


class MediaType(JSONObject):
    """
    https://swagger.io/specification/#mediaTypeObject
    """

    def __init__(
        self,
        schema=missing,  # type: Union[Schematic, Reference, Missing]
        example=missing,  # type: Any
        examples=missing,  # type: Union[Dict[str, Union[Example, Reference]]]
        encoding=missing,  # type: Union[Dict[str, Union[Encoding, Reference]]]
    ):
        self.schema = schema
        self.example = example
        self.examples = examples
        self.encoding = encoding


class Response(JSONObject):
    """
    https://swagger.io/specification/#responseObject

    Properties:

        - description (str): A short description of the response. `CommonMark syntax<http://spec.commonmark.org/>` may
          be used for rich text representation.

        - headers ({str:Header|Reference}): Maps a header name to its definition (mappings are case-insensitive).

        - content ({str:Content|Reference}): A mapping of media types to ``MediaType`` instances describing potential
          payloads.

        - links ({str:Link|Reference}): A map of operations links that can be followed from the response.
    """

    def __init__(
        self,
        description=missing,  # type: Union[str, Missing]
        headers=missing,  # type: Union[Dict[str, Union[Header, Reference]], Missing]
        content=missing,  # type: Union[Dict[str, Union[Content, Reference]], Missing]
        links=missing,  # type: Union[Dict[str, Union[Links, Reference]], Missing]
    ):
        # type: (...) -> None
        self.description = description
        self.headers = headers
        self.content = content
        self.links = links


class Responses(JSONObject):
    """
    Properties:

        - continue (Response): This ``Response`` instance describes an HTTP response with status code "100" (phrase
          "Continue").

        - switching_protocols (Response): This ``Response`` instance describes an HTTP response with status code "101"
          (phrase "Switching Protocols").

        - ok (Response): This ``Response`` instance describes an HTTP response with status code "200" (phrase "OK").
        - created (Response): This ``Response`` instance describes an HTTP response with status code "201" (phrase
          "Created").

        - accepted (Response): This ``Response`` instance describes an HTTP response with status code "202" (phrase
          "Accepted").

        - non_authoritative_information (Response): This ``Response`` instance describes an HTTP response with status
          code "203" (phrase "Non-Authoritative Information").

        - no_content (Response): This ``Response`` instance describes an HTTP response with status code "204" (phrase
          "No Content").

        - reset_content (Response): This ``Response`` instance describes an HTTP response with status code "205"
          (phrase "Reset Content").

        - partial_content (Response): This ``Response`` instance describes an HTTP response with status code "206"
          (phrase "Partial Content").

        - multiple_choices (Response): This ``Response`` instance describes an HTTP response with status code "300"
          (phrase "Multiple Choices").

        - moved_permanently (Response): This ``Response`` instance describes an HTTP response with status code "301"
          (phrase "Moved Permanently").

        - found (Response): This ``Response`` instance describes an HTTP response with status code "302" (phrase
          "Found").

        - see_other (Response): This ``Response`` instance describes an HTTP response with status code "303" (phrase
          "See Other").

        - not_modified (Response): This ``Response`` instance describes an HTTP response with status code "304" (phrase
          "Not Modified").

        - use_proxy (Response): This ``Response`` instance describes an HTTP response with status code "305" (phrase
          "Use Proxy").

        - temporary_redirect (Response): This ``Response`` instance describes an HTTP response with status code "307"
          (phrase "Temporary Redirect").

        - bad_request (Response): This ``Response`` instance describes an HTTP response with status code "400" (phrase
          "Bad Request").

        - unauthorized (Response): This ``Response`` instance describes an HTTP response with status code "401" (phrase
          "Unauthorized").

        - payment_required (Response): This ``Response`` instance describes an HTTP response with status code "402"
          (phrase "Payment Required").

        - forbidden (Response): This ``Response`` instance describes an HTTP response with status code "403" (phrase
          "Forbidden").

        - not_found (Response): This ``Response`` instance describes an HTTP response with status code "404" (phrase
          "Not Found").

        - method_not_allowed (Response): This ``Response`` instance describes an HTTP response with status code "405"
          (phrase "Method Not Allowed").

        - not_acceptable (Response): This ``Response`` instance describes an HTTP response with status code "406"
          (phrase "Not Acceptable").

        - proxy_authentication_required (Response): This ``Response`` instance describes an HTTP response with status
          code "407" (phrase "Proxy Authentication Required").

        - request_timeout (Response): This ``Response`` instance describes an HTTP response with status code "408"
          (phrase "Request Timeout").

        - conflict (Response): This ``Response`` instance describes an HTTP response with status code "409" (phrase
          "Conflict").

        - gone (Response): This ``Response`` instance describes an HTTP response with status code "410" (phrase "Gone").

        - length_required (Response): This ``Response`` instance describes an HTTP response with status code "411"
          (phrase "Length Required").
          
        - precondition_failed (Response): This ``Response`` instance describes an HTTP response with status code "412"
          (phrase "Precondition Failed").
        
        - payload_too_large (Response): This ``Response`` instance describes an HTTP response with status code "413"
          (phrase "Payload Too Large").
        
        - uri_too_long (Response): This ``Response`` instance describes an HTTP response with status code "414"
          (phrase "URI Too Long").
        
        - unsupported_media_type (Response): This ``Response`` instance describes an HTTP response with status code
          "415" (phrase "Unsupported Media Type").
        
        - range_not_satisfiable (Response): This ``Response`` instance describes an HTTP response with status code
          "416" (phrase "Range Not Satisfiable").
        
        - expectation_failed (Response): This ``Response`` instance describes an HTTP response with status code "417"
          (phrase "Expectation Failed").
        
        - upgrade_required (Response): This ``Response`` instance describes an HTTP response with status code "426"
          (phrase "Upgrade Required").
        
        - internal_server_error (Response): This ``Response`` instance describes an HTTP response with status code
          "500" (phrase "Internal Server Error").
        
        - not_implemented (Response): This ``Response`` instance describes an HTTP response with status code "501"
          (phrase "Not Implemented").
        
        - bad_gateway (Response): This ``Response`` instance describes an HTTP response with status code "502"
          (phrase "Bad Gateway").
        
        - service_unavailable (Response): This ``Response`` instance describes an HTTP response with status code "503"
          (phrase "Service Unavailable").
        
        - gateway_timeout (Response): This ``Response`` instance describes an HTTP response with status code "504"
          (phrase "Gateway Timeout").
        
        - http_version_not_supported (Response): This ``Response`` instance describes an HTTP response with status code
          "505" (phrase "HTTP Version Not Supported").
    """

    def __init__(
        self,
        default=missing,  # type: Union[Response, Missing]
        please_continue=missing,  # type: Union[Response, Missing]
        switching_protocols=missing,  # type: Union[Response, Missing]
        ok=missing,  # type: Union[Response, Missing]
        created=missing,  # type: Union[Response, Missing]
        accepted=missing,  # type: Union[Response, Missing]
        non_authoritative_information=missing,  # type: Union[Response, Missing]
        no_content=missing,  # type: Union[Response, Missing]
        reset_content=missing,  # type: Union[Response, Missing]
        partial_content=missing,  # type: Union[Response, Missing]
        multiple_choices=missing,  # type: Union[Response, Missing]
        moved_permanently=missing,  # type: Union[Response, Missing]
        found=missing,  # type: Union[Response, Missing]
        see_other=missing,  # type: Union[Response, Missing]
        not_modified=missing,  # type: Union[Response, Missing]
        use_proxy=missing,  # type: Union[Response, Missing]
        temporary_redirect=missing,  # type: Union[Response, Missing]
        bad_request=missing,  # type: Union[Response, Missing]
        unauthorized=missing,  # type: Union[Response, Missing]
        payment_required=missing,  # type: Union[Response, Missing]
        forbidden=missing,  # type: Union[Response, Missing]
        not_found=missing,  # type: Union[Response, Missing]
        method_not_allowed=missing,  # type: Union[Response, Missing]
        not_acceptable=missing,  # type: Union[Response, Missing]
        proxy_authentication_required=missing,  # type: Union[Response, Missing]
        request_timeout=missing,  # type: Union[Response, Missing]
        conflict=missing,  # type: Union[Response, Missing]
        gone=missing,  # type: Union[Response, Missing]
        length_required=missing,  # type: Union[Response, Missing]
        precondition_failed=missing,  # type: Union[Response, Missing]
        payload_too_large=missing,  # type: Union[Response, Missing]
        uri_too_long=missing,  # type: Union[Response, Missing]
        unsupported_media_type=missing,  # type: Union[Response, Missing]
        range_not_satisfiable=missing,  # type: Union[Response, Missing]
        expectation_failed=missing,  # type: Union[Response, Missing]
        upgrade_required=missing,  # type: Union[Response, Missing]
        internal_server_error=missing,  # type: Union[Response, Missing]
        not_implemented=missing,  # type: Union[Response, Missing]
        bad_gateway=missing,  # type: Union[Response, Missing]
        service_unavailable=missing,  # type: Union[Response, Missing]
        gateway_timeout=missing,  # type: Union[Response, Missing]
        http_version_not_supported=missing,  # type: Union[Response, Missing]
    ):
        # type: (...) -> None
        self.default = default
        self.please_continue = please_continue
        self.switching_protocols = switching_protocols
        self.ok = ok
        self.created = created
        self.accepted = accepted
        self.non_authoritative_information = non_authoritative_information
        self.no_content = no_content
        self.reset_content = reset_content
        self.partial_content = partial_content
        self.multiple_choices = multiple_choices
        self.moved_permanently = moved_permanently
        self.found = found
        self.see_other = see_other
        self.not_modified = not_modified
        self.use_proxy = use_proxy
        self.temporary_redirect = temporary_redirect
        self.bad_request = bad_request
        self.unauthorized = unauthorized
        self.payment_required = payment_required
        self.forbidden = forbidden
        self.not_found = not_found
        self.method_not_allowed = method_not_allowed
        self.not_acceptable = not_acceptable
        self.proxy_authentication_required = proxy_authentication_required
        self.request_timeout = request_timeout
        self.conflict = conflict
        self.gone = gone
        self.length_required = length_required
        self.precondition_failed = precondition_failed
        self.payload_too_large = payload_too_large
        self.uri_too_long = uri_too_long
        self.unsupported_media_type = unsupported_media_type
        self.range_not_satisfiable = range_not_satisfiable
        self.expectation_failed = expectation_failed
        self.upgrade_required = upgrade_required
        self.internal_server_error = internal_server_error
        self.not_implemented = not_implemented
        self.bad_gateway = bad_gateway
        self.service_unavailable = service_unavailable
        self.gateway_timeout = gateway_timeout
        self.http_version_not_supported = http_version_not_supported



class Operation(JSONObject):
    """
    https://swagger.io/specification/#operationObject

    Describes a single API operation on a path.

    Properties:

        - tags (Sequence[str]):  A list of tags for API documentation control. Tags can be used for logical grouping of
          operations by resources or any other qualifier.

        - summary (str):  A short summary of what the operation does.

        - description (str): A verbose explanation of the operation behavior. `CommonMark <http://spec.commonmark.org>`
          syntax may be used for rich text representation.

        - external_docs (ExternalDocumentation):  Additional external documentation for this operation.

        - operation_id (str):  Unique string used to identify the operation. The ID must be unique among all operations
          described in the API. Tools and libraries may use the ``operation_id`` to uniquely identify an operation,
          therefore, it is recommended to follow common programming naming conventions.

        - parameters ([Parameter|Reference]):  A list of parameters that are applicable for this operation. If a
          parameter is already defined at the ``PathItem``, the new definition will override it, but can never remove
          it.

        - request_body (RequestBody|Reference):  The request body applicable for this operation. The requestBody is only
          supported in HTTP methods where the HTTP 1.1 specification
          `RFC7231 <https://tools.ietf.org/html/rfc7231#section-4.3.1>` has explicitly defined semantics for request
          bodies.

        - responses (Dict[str, Response]):  A mapping of HTTP response codes to response schemas.

        - callbacks ({str:CallBack|Reference})

        - deprecated (bool)

        - security ([[str]])

        - servers ([Server])

    Version 2x Compatibility:

        - produces ([str]):
    """

    def __init__(
        self,
        tags=missing,  # type: Union[Sequence[str], Missing]
        summary=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        external_docs=missing,  # type: Union[ExternalDocumentation, Missing]
        operation_id=missing,  # type: Union[str, Missing]
        parameters=missing,  # type: Union[Sequence[Union[Parameter, Reference]], Missing]
        request_body=missing,  # type: Union[RequestBody, Reference, Missing]
        responses=missing,  # type: Union[Dict[str, Response], Missing]
        callbacks=missing,  # type: Union[Dict[str, Union[Callback, Refefence]], Missing]
        security=missing,  # type: Union[Sequence[[str]], Missing]
        servers=missing,  # type: Union[Sequence[Server], Missing]
        # Version 2x Compatibility
        produces=missing,  # type: Union[Sequence[str], Missing]
    ):
        # type: (...) -> None
        self.tags = (
            tags
            if (tags is missing or tags is None) else
            list(tags)
        )  # type: Union[Sequence[str], Missing]
        self.summary = summary
        self.description = description
        self.external_docs = external_docs
        self.operation_id = operation_id
        self.parameters = parameters
        self.request_body = request_body
        self.responses = responses
        self.callbacks = callbacks
        self.security = (
            security if (
                security is missing or
                security is None
            ) else list(security)
        )  # type: Union[Sequence[[str]], Missing]
        self.servers = (
            servers if (
                servers is missing or
                servers is None
            ) else list(servers)
        )  # type: Union[Sequence[Server], Missing]
        # Version 2x Compatibility
        self.produces = (
            produces if (
                produces is missing or
                produces is None
            ) else list(produces)
        )  # type: Union[Sequence[str], Missing]


class PathItem(JSONObject):
    """
    https://swagger.io/specification/#pathItemObject
    """

    def __init__(
        self,
        ref=missing,  # type: Union[str, Missing]
        summary=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        get=missing,  # type: Union[Operation, Missing]
        put=missing,  # type: Union[Operation, Missing]
        post=missing,  # type: Union[Operation, Missing]
        delete=missing,  # type: Union[Operation, Missing]
        options=missing,  # type: Union[Operation, Missing]
        head=missing,  # type: Union[Operation, Missing]
        patch=missing,  # type: Union[Operation, Missing]
        trace=missing,  # type: Union[Operation, Missing]
        servers=missing,  # type: Union[Sequence[Server], Missing]
        parameters=missing,  # type: Union[Sequence[Parameter], Missing]
    ):
        # type: (...) -> None
        self.ref = ref
        self.summary = summary
        self.description = description
        self.get = get
        self.put = put
        self.post = post
        self.delete = delete
        self.options = options
        self.head = head
        self.patch = patch
        self.trace = trace
        self.servers = (
            servers
            if (servers is missing or servers is None) else
            list(servers)
        )  # type: Union[Sequence[Server], Missing]
        self.parameters = (
            parameters
            if (parameters is missing or parameters is None) else
            list(parameters)
        )  # type: Union[Sequence[Parameter], Missing]


class ServerVariable(JSONObject):

    def __init__(
        self,
        enum=missing,  # type: Union[str, Missing]
        default=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
    ):
        self.enum = enum
        self.default = default
        self.description = description


class Server(JSONObject):
    """
    https://swagger.io/specification/#serverObject
    """

    def __init__(
        self,
        url=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        variables=missing  # type: Union[Dict[str, ServerVariable], Missing]
    ):
        # type: (...) -> None
        self.url = url
        self.description = description
        self.variables = variables


class Discriminator(JSONObject):
    """
    https://swagger.io/specification/#discriminatorObject

    Properties:

        - property_name (str): The name of the property which will hold the discriminating value.

        - mapping ({str:str}): An mappings of payload values to schema names or references.
    """

    def __init__(
        self,
        property_name=missing,  # type: Union[str, Missing]
        mapping=missing,  # type: Union[Dict[str], Missing]
    ):
        self.property_name = property_name
        self.mapping = mapping


class XML(JSONObject):
    """
    Properties:

        - name (str): The element name.

        - name_space (str): The *absolute* URI of a namespace.

        - prefix (str): The prefix to be used with the name to reference the name-space.

        - attribute (bool): If ``True``, the property described is an attribute rather than a sub-element.

        - wrapped (bool): If ``True``, an array instance described by the schema will be wrapped by a tag (named
          according to the parent element's property, while ``name`` refers to the child element name).
    """

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        name_space=missing,  # type: Union[str, Missing]
        prefix=missing,  # type: Union[str, Missing]
        attribute=missing,  # type: Union[bool, Missing]
        wrapped=missing,  # type: Union[bool, Missing]
    ):
        self.name = name
        self.name_space = name_space
        self.prefix = prefix
        self.attribute = attribute
        self.wrapped = wrapped


class ExternalDocumentation(JSONObject):
    """
    Properties:

        - description (str)
        - url (str)
    """

    def __init__(
        self,
        description=missing,  # type: Union[str, Missing]
        url=missing,  # type: Union[str, Missing]
    ):
        self.description = description
        self.url = url


class Schematic(JSONObject):
    """
    Instances of this class represent a JSON validation schema, as defined on <http://json-schema.org> and
    <https://swagger.io/specification/#schemaObject>.

    Properties:

        - title (str)

        - description (str)

        - multiple_of (Number): The numeric value this schema describes should be divisible by this number.

        - maximum (Number): The number this schema describes should be less than or equal to this value, or less than
          this value, depending on the value of ``exclusive_maximum``.

        - exclusive_maximum (bool): If ``True``, the numeric instance described by this schema must be *less than*
          ``maximum``. If ``False``, the numeric instance described by this schema can be less than or *equal to*
          ``maximum``.

        - minimum (Number): The number this schema describes should be greater than or equal to this value, or greater
          than this value, depending on the value of ``exclusive_minimum``.

        - exclusive_minimum (bool): If ``True``, the numeric instance described by this schema must be *greater than*
          ``minimum``. If ``False``, the numeric instance described by this schema can be greater than or *equal to*
          ``minimum``.

        - max_length (int): The number of characters in the string instance described by this schema must be less than,
          or equal to, the value of this property.

        - min_length (int): The number of characters in the string instance described by this schema must be greater
          than, or equal to, the value of this property.

        - pattern (str): The string instance described by this schema should match this regular expression (ECMA 262).

        - items (Schematic|Sequence[Schematic]):

            - If ``items`` is a sub-schema—each item in the array instance described by this schema should be valid as
              described by this sub-schema.

            - If ``items`` is a sequence of sub-schemas, the array instance described by this schema should be equal in
              length to this sequence, and each value should be valid as described by the sub-schema at the
              corresponding index within this sequence of sub-schemas.

        - additional_items (Schematic|bool): If ``additional_items`` is ``True``—the array instance described by
          this schema may contain additional values beyond those defined in ``items``.

        - max_items (int): The array instance described by this schema should contain no more than this number of
          items.

        - min_items (int): The array instance described by this schema should contain at least this number of
          items.

        - unique_items (bool): The array instance described by this schema should contain only unique items.

        - max_properties (int)

        - min_properties (int)

        - properties (Dict[str, Schematic]): Any properties of the object instance described by this schema which
          correspond to a key in this mapping should be valid as described by the sub-schema corresponding to that key.

        - pattern_properties (Schematic): Any properties of the object instance described by this schema which
          match a key in this mapping, when the key is evaluated as a regular expression, should be valid as described by
          the sub-schema corresponding to the matched key.

        - additional_properties (bool|Schematic):

            - If ``additional_properties`` is ``True``—properties may be present in the object described by
              this schema with names which do not match those in either ``properties`` or ``pattern_properties``.

            - If ``additional_properties`` is ``False``—all properties present in the object described by this schema
              must correspond to a property matched in either ``properties`` or ``pattern_properties``.

        - dependencies (Dict[str, Dict[str, Union[Schematic, Sequence[str]]]]):

            A dictionary mapping properties of the object instance described by this schema to a mapping other
            properties and either:

                - A sub-schema for validation of the second property when the first property is present on
                  the object instance described by this schema.
                - A list of properties which must *also* be present when the first and second properties are present on
                  the object instance described by this schema.

        - enum (Sequence): The value/instance described by this schema should be among those in this sequence.

        - data_type (str|Sequence): The value/instance described by this schema should be of the types indicated
          (if this is a string), or *one of* the types indicated (if this is a sequence).

            - "null"
            - "boolean"
            - "object"
            - "array"
            - "number"
            - "string"

        - format (str|Sequence):

            - "date-time": A date and time in the format YYYY-MM-DDThh:mm:ss.sTZD (eg 1997-07-16T19:20:30.45+01:00),
              YYYY-MM-DDThh:mm:ssTZD (eg 1997-07-16T19:20:30+01:00), or YYYY-MM-DDThh:mmTZD (eg 1997-07-16T19:20+01:00).
            - "email"
            - "hostname"
            - "ipv4"
            - "ipv6"
            - "uri"
            - "uriref": A URI or a relative reference.

        - all_of (Sequence[Schematic]): The value/instance described by the schema should *also* be valid as
          described by all sub-schemas in this sequence.

        - any_of (Sequence[Schematic]): The value/instance described by the schema should *also* be valid as
          described in at least one of the sub-schemas in this sequence.

        - one_of (Sequence[Schematic]): The value/instance described by the schema should *also* be valid as
          described in one (but *only* one) of the sub-schemas in this sequence.

        - is_not (Schematic): The value/instance described by this schema should *not* be valid as described by this
          sub-schema.

        - definitions (Dict[Schematic]): A dictionary of sub-schemas, stored for the purpose of referencing
          these sub-schemas elsewhere in the schema.

        - required (Sequence[str]): A list of attributes which must be present on the object instance described by this
          schema.

        - default (Any): The value presumed if the value/instance described by this schema is absent.

        The following properties are specific to OpenAPI (not part of the core `JSON Schema <http://json-schema.org>`):

        - nullable (bool): If ``True``, the value/instance described by this schema may be a null value (``None``).

        - discriminator (Discriminator): Adds support for polymorphism.

        - read_only (bool): If ``True``, the property described may be returned as part of a response, but should not
          be part of a request.

        - write_only (bool): If ``True``, the property described may be sent as part of a request, but should not
          be returned as part of a response.

        - xml (XML): Provides additional information describing XML representation of the property described by this
          schema.

        - external_docs (ExternalDocumentation)

        - example (Any)

        - depracated (bool): If ``True``, the property or instance described by this schema should be phased out, as
          if will no longer be supported in future versions.
    """

    def __init__(
        self,
        title=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        multiple_of=missing,  # type: Union[Number, Missing]
        maximum=missing,  # type: Union[Number, Missing]
        exclusive_maximum=missing,  # type: Union[bool, Missing]
        minimum=missing,  # type: Union[Number, Missing]
        exclusive_minimum=missing,  # type: Union[bool, Missing]
        max_length=missing,  # type: Union[int, Missing]
        min_length=missing,  # type: Union[int, Missing]
        pattern=missing,  # type: Union[str, Missing]
        items=missing,  # type: Union[Schematic, Sequence[Schematic], Missing]
        additional_items=missing,  # type: Union[Schematic, bool, Missing]
        max_items=missing,  # type: Union[int, Missing]
        min_items=missing,  # type: Union[int, Missing]
        unique_items=missing,  # type: Union[bool, Missing]
        max_properties=missing,  # type: Union[int, Missing]
        min_properties=missing,  # type: Union[int, Missing]
        properties=missing,  # type: Union[Dict[str, Schematic], Missing]
        pattern_properties=missing,  # type: Union[Schematic, Missing]
        additional_properties=missing,  # type: Union[bool, Schematic, Missing]
        dependencies=missing,  # type: Union[Dict[str, Dict[str, Union[Schematic, Sequence[str]]]], Missing]
        enum=missing,  # type: Union[Sequence, Missing]
        data_type=missing,  # type: Union[str, Sequence, Missing]
        format=missing,  # type: Union[str, Sequence, Missing]
        all_of=missing,  # type: Union[Sequence[Schematic], Missing]
        any_of=missing,  # type: Union[Sequence[Schematic], Missing]
        one_of=missing,  # type: Union[Sequence[Schematic], Missing]
        is_not=missing,  # type: Union[Schematic, Missing]
        definitions=missing,  # type: Union[Dict[Schematic], Missing]
        required=missing,  # type: Union[Sequence[str], Missing]
        default=missing,  # type: Union[Any, Missing]
        discriminator=missing,  # type: Union[Discriminator, Missing]
        read_only=missing,  # type: Union[bool, Missing]
        write_only=missing,  # type: Union[bool, Missing]
        xml=missing,  # type: Union[XML, Missing]
        external_docs=missing,  # type: Union[ExternalDocumentation, Missing]
        example=missing,  # type: Any
        depracated=missing,  # type: Union[bool, Missing]
    ):
        self.title = title
        self.description = description
        self.multiple_of = multiple_of
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.items = items
        self.additional_items = additional_items
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.max_properties = max_properties
        self.min_properties = min_properties
        self.properties = properties
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.dependencies = dependencies
        self.enum = enum
        self.data_type = data_type
        self.format = format
        self.all_of = all_of
        self.any_of = any_of
        self.one_of = one_of
        self.is_not = is_not
        self.definitions = definitions
        self.required = required
        self.default = default
        self.discriminator = discriminator
        self.read_only = missing
        self.write_only = read_only
        self.xml = xml
        self.external_docs = external_docs
        self.example = example
        self.depracated = depracated


class RequestBody(JSONObject):

    def __init__(
        self,
        description=missing,  # type: Union[str, Missing]
        content=missing,  # type: Union[Dict[str, MediaType], Missing]
        required=missing,  # type: Union[bool, Missing]
    ):
        self.description = description
        self.content = content
        self.required = required


class OAuthFlow(JSONObject):
    """
    https://swagger.io/specification/#oauthFlowObject
    """

    def __init__(
        self,
        authorization_url=missing,  # type: Union[str, Missing]
        token_url=missing,  # type: Union[str, Missing]
        refresh_url=missing,  # type: Union[str, Missing]
        scopes=missing,  # type: Union[Dict[str, str], Missing]
    ):
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.refresh_url = refresh_url
        self.scopes = scopes


class OAuthFlows(JSONObject):

    def __init__(
        self,
        implicit=missing,  # type: Union[OAuthFlow, Missing]
        password=missing,  # type: Union[OAuthFlow, Missing]
        client_credentials=missing,  # type: Union[OAuthFlow, Missing]
        authorization_code=missing,  # type: Union[OAuthFlow, Missing]
    ):
        self.implicit = implicit
        self.password = password
        self.client_credentials = client_credentials
        self.authorization_code = authorization_code


class SecurityScheme(JSONObject):
    """
    https://swagger.io/specification/#requestBodyObject
    """

    def __init__(
        self,
        security_scheme_type=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        name=missing,  # type: Union[str, Missing]
        security_scheme_in=missing,  # type: Union[str, Missing]
        scheme=missing,  # type: Union[str, Missing]
        bearer_format=missing,  # type: Union[str, Missing]
        flows=missing,  # type: Union[OAuthFlows, Missing]
        open_id_connect_url=missing,  # type: Union[str, Missing]
    ):
        self.security_scheme_type = security_scheme_type
        self.description = description
        self.name = name
        self.security_scheme_in = security_scheme_in
        self.scheme = scheme
        self.bearer_format = bearer_format
        self.flows = flows
        self.open_id_connect_url = open_id_connect_url


class Components(JSONObject):

    def __init__(
        self,
        schemas=missing,  # type: Union[Dict[str, Union[Schematic, Reference]]]
        responses=missing,  # type: Union[Dict[str, Union[Response, Reference]]]
        parameters=missing,  # type: Union[Dict[str, Union[Parameter, Reference]]]
        examples=missing,  # type: Union[Dict[str, Union[Example, Reference]]]
        request_bodies=missing,  # type: Union[Dict[str, Union[RequestBody, Reference]]]
        headers=missing,  # type: Union[Dict[str, Union[Header, Reference]]]
        security_schemes=missing,  # type: Union[Dict[str, Union[SecurityScheme, Reference]]]
        links=missing,  # type: Union[Dict[str, Union[Link, Reference]]]
        callbacks=missing,  # type: Union[Dict[str, Union[Dict[str, PathItem], Reference]]]
    ):
        self.schemas = schemas
        self.responses = responses
        self.parameters = parameters
        self.examples = examples
        self.request_bodies = request_bodies
        self.headers = headers
        self.security_schemes = security_schemes
        self.links = links
        self.callbacks = callbacks


class OpenAPI(JSONObject):

    def __init__(
        self,
        swagger=missing,  # type: Union[str, Missing]
        open_api=missing,  # type: Union[str, Missing]
        info=missing,  # type: Union[Info, Missing]
        host=missing,  # type: Union[str, Missing]
        servers=missing,  # type: Union[str, Missing]
        base_path=missing,  # type: Union[str, Missing]
        schemes=missing,  # type: Union[Sequence[str], Missing]
        tags=missing,  # type: Union[Sequence[Tag], Missing]
        paths=missing,  # type: Union[Dict[str, PathItem], Missing]
        components=missing,  # type: Union[Components, Missing]
    ):
        # type: (...) -> None
        self.swagger = swagger
        self.open_api = open_api
        self.info = info
        self.host = host
        self.servers = missing if servers is missing else list(servers)  # type: Union[List[Server], Missing]
        self.base_path = base_path
        self.schemes = missing if schemes is missing else list(schemes)  # type: Union[List[str], Missing]
        self.tags = missing if tags is missing else list(tags)  # type: Union[Sequence[Tag], Missing]
        self.paths = paths
        self.components = components


from openswallow.model import schemas


def set_schema(model, schema):
    # type: (type, type) -> None
    if not issubclass(model, JSONObject):
        raise TypeError(
            'This function requires a sub-class of ``openswallow.model.JSONObject``, not ``%s``' % (
                repr(model)
            )
        )
    elif not issubclass(schema, schemas.JSONObjectSchema):
        raise TypeError(
            'This function requires a sub-class of ``openswallow.model.schemas.JSONObjectSchema``, not ``%s``' % (
                repr(schema)
            )
        )
    model.__schema__ = schema
    schema.__model__ = model


# Map schemas to objects


_schemas = {}

for _k in dir(schemas):
    _v = getattr(schemas, _k)
    if isinstance(_v, type) and (issubclass(_v, Schema)):
        _schemas[_k] = _v

for _k, _v in copy(locals()).items():
    if isinstance(_v, type) and (issubclass(_v, JSONObject)):
        _sn = _v.__name__ + 'Schema'
        if _sn in _schemas:
            _schema = _schemas[_sn]
            set_schema(_v, _schema)
        elif _sn != 'JSONObjectSchema':
            raise KeyError(_sn)
