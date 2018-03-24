# region Backwards Compatibility
from __future__ import nested_scopes, generators, division, absolute_import, with_statement,\
print_function, unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
# endregion

import serial

try:
    import typing
    from typing import Union, Dict, Any
except ImportError:
    typing = Union = Any = None


class PostCheck(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1check/post/responses/200/schema
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        software=None,  # type: Optional[Any]
        language=None,  # type: Optional[Any]
        matches=None,  # type: Optional[typing.Sequence[Any]]
    ):
        self.software = software
        self.language = language
        self.matches = matches
        super().__init__(_)


class PostCheckSoftware(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/software
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        name=None,  # type: Optional[Union[str, Null]]
        version=None,  # type: Optional[Union[str, Null]]
        build_date=None,  # type: Optional[Union[str, Null]]
        api_version=None,  # type: Optional[Union[int, Null]]
        status=None,  # type: Optional[str]
    ):
        self.name = name
        self.version = version
        self.build_date = build_date
        self.api_version = api_version
        self.status = status
        super().__init__(_)


class PostCheckLanguage(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/language
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        name=None,  # type: Optional[Union[str, Null]]
        code=None,  # type: Optional[Union[str, Null]]
    ):
        self.name = name
        self.code = code
        super().__init__(_)


# https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1check/post/responses/200/schema
serial.meta.writable(PostCheck).properties = [
    ('software', serial.properties.Property()),
    ('language', serial.properties.Property()),
    (
        'matches',
        serial.properties.Array(
            item_types=(
                serial.properties.Property(),
            ),
        )
    )
]

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/software
serial.meta.writable(PostCheckSoftware).properties = [
    (
        'name',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'version',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'build_date',
        serial.properties.Property(
            name='buildDate',
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'api_version',
        serial.properties.Property(
            name='apiVersion',
            types=(
                serial.properties.Integer(),
                serial.properties.Null
            ),
        )
    ),
    ('status', serial.properties.String())
]

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/language
serial.meta.writable(PostCheckLanguage).properties = [
    (
        'name',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'code',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    )
]
