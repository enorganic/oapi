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
        software=None,  # type: Optional[PostCheckSoftware]
        language=None,  # type: Optional[PostCheckLanguage]
        matches=None,  # type: Optional[typing.Sequence[CheckMatches]]
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


class CheckMatches(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        message=None,  # type: Optional[Union[str, Null]]
        short_message=None,  # type: Optional[str]
        offset=None,  # type: Optional[Union[int, Null]]
        length=None,  # type: Optional[Union[int, Null]]
        replacements=None,  # type: Optional[Union[typing.Sequence[CheckMatchesReplacements], Null]]
        context=None,  # type: Optional[Union[PostCheckMatchesContext, Null]]
        sentence=None,  # type: Optional[Union[str, Null]]
        rule=None,  # type: Optional[PostCheckMatchesRule]
    ):
        self.message = message
        self.short_message = short_message
        self.offset = offset
        self.length = length
        self.replacements = replacements
        self.context = context
        self.sentence = sentence
        self.rule = rule
        super().__init__(_)


class CheckMatchesReplacements(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements/items
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        value=None,  # type: Optional[str]
    ):
        self.value = value
        super().__init__(_)


class PostCheckMatchesContext(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/context
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        text=None,  # type: Optional[Union[str, Null]]
        offset=None,  # type: Optional[Union[int, Null]]
        length=None,  # type: Optional[Union[int, Null]]
    ):
        self.text = text
        self.offset = offset
        self.length = length
        super().__init__(_)


class PostCheckMatchesRule(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        id_=None,  # type: Optional[Union[str, Null]]
        sub_id=None,  # type: Optional[str]
        description=None,  # type: Optional[Union[str, Null]]
        urls=None,  # type: Optional[typing.Sequence[CheckMatchesRuleUrls]]
        issue_type=None,  # type: Optional[str]
        category=None,  # type: Optional[Union[PostCheckMatchesRuleCategory, Null]]
    ):
        self.id_ = id_
        self.sub_id = sub_id
        self.description = description
        self.urls = urls
        self.issue_type = issue_type
        self.category = category
        super().__init__(_)


class CheckMatchesRuleUrls(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls/items
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        value=None,  # type: Optional[str]
    ):
        self.value = value
        super().__init__(_)


class PostCheckMatchesRuleCategory(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/category
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        id_=None,  # type: Optional[str]
        name=None,  # type: Optional[str]
    ):
        self.id_ = id_
        self.name = name
        super().__init__(_)


class Languages(serial.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1languages/get/responses/200/schema/items
    """

    def __init__(
        self,
        _=None,  # type: Optional[Union[str, bytes, dict, typing.Sequence, IO]]
        name=None,  # type: Optional[Union[str, Null]]
        code=None,  # type: Optional[Union[str, Null]]
        long_code=None,  # type: Optional[Union[str, Null]]
    ):
        self.name = name
        self.code = code
        self.long_code = long_code
        super().__init__(_)


# https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1check/post/responses/200/schema
serial.meta.writable(PostCheck).properties = [
    (
        'software',
        serial.properties.Property(
            types=(
                PostCheckSoftware,
            ),
        )
    ),
    (
        'language',
        serial.properties.Property(
            types=(
                PostCheckLanguage,
            ),
        )
    ),
    (
        'matches',
        serial.properties.Array(
            item_types=(
                CheckMatches,
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

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items
serial.meta.writable(CheckMatches).properties = [
    (
        'message',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'short_message',
        serial.properties.String(
            name='shortMessage',
        )
    ),
    (
        'offset',
        serial.properties.Property(
            types=(
                serial.properties.Integer(),
                serial.properties.Null
            ),
        )
    ),
    (
        'length',
        serial.properties.Property(
            types=(
                serial.properties.Integer(),
                serial.properties.Null
            ),
        )
    ),
    (
        'replacements',
        serial.properties.Property(
            types=(
                serial.properties.Array(
                    item_types=(
                        CheckMatchesReplacements,
                    ),
                ),
                serial.properties.Null
            ),
        )
    ),
    (
        'context',
        serial.properties.Property(
            types=(
                serial.properties.Property(
                    types=(
                        PostCheckMatchesContext,
                    ),
                ),
                serial.properties.Null
            ),
        )
    ),
    (
        'sentence',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'rule',
        serial.properties.Property(
            types=(
                PostCheckMatchesRule,
            ),
        )
    )
]

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements/items
serial.meta.writable(CheckMatchesReplacements).properties = [
    ('value', serial.properties.String())
]

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/context
serial.meta.writable(PostCheckMatchesContext).properties = [
    (
        'text',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'offset',
        serial.properties.Property(
            types=(
                serial.properties.Integer(),
                serial.properties.Null
            ),
        )
    ),
    (
        'length',
        serial.properties.Property(
            types=(
                serial.properties.Integer(),
                serial.properties.Null
            ),
        )
    )
]

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule
serial.meta.writable(PostCheckMatchesRule).properties = [
    (
        'id_',
        serial.properties.Property(
            name='id',
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'sub_id',
        serial.properties.String(
            name='subId',
        )
    ),
    (
        'description',
        serial.properties.Property(
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    ),
    (
        'urls',
        serial.properties.Array(
            item_types=(
                CheckMatchesRuleUrls,
            ),
        )
    ),
    (
        'issue_type',
        serial.properties.String(
            name='issueType',
        )
    ),
    (
        'category',
        serial.properties.Property(
            types=(
                serial.properties.Property(
                    types=(
                        PostCheckMatchesRuleCategory,
                    ),
                ),
                serial.properties.Null
            ),
        )
    )
]

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls/items
serial.meta.writable(CheckMatchesRuleUrls).properties = [
    ('value', serial.properties.String())
]

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/category
serial.meta.writable(PostCheckMatchesRuleCategory).properties = [
    (
        'id_',
        serial.properties.String(
            name='id',
        )
    ),
    ('name', serial.properties.String())
]

# https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1languages/get/responses/200/schema/items
serial.meta.writable(Languages).properties = [
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
    ),
    (
        'long_code',
        serial.properties.Property(
            name='longCode',
            types=(
                serial.properties.String(),
                serial.properties.Null
            ),
        )
    )
]
