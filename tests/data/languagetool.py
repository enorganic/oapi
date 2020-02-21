from __future__ import (
    nested_scopes, generators, division, absolute_import,
    with_statement, print_function, unicode_literals
)
from future import standard_library
standard_library.install_aliases()
from future.builtins import *  # noqa

import sob  # noqa
import numbers  # noqa
try:
    from typing import Union, Dict, Any, Sequence, IO, Optional
except ImportError:
    Union = Dict = Any = Sequence = IO = Optional = None


class CheckPostResponses200Schema(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        software=None,  # type: Optional[CheckPostResponses200SchemaSoftware]
        language=None,  # type: Optional[CheckPostResponses200SchemaLanguage]
        matches=None  # type: Optional[CheckPostResponses200SchemaMatches]
    ):
        self.software = software
        self.language = language
        self.matches = matches
        super().__init__(_data)


class CheckPostResponses200SchemaSoftware(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema/properties/software
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        version=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        build_date=None,  # type: Optional[Union[str, sob.properties.types.Null]]  # noqa
        api_version=None,  # type: Optional[Union[int, sob.properties.types.Null]]  # noqa
        status=None,  # type: Optional[str]
        premium=None  # type: Optional[bool]
    ):
        self.name = name
        self.version = version
        self.build_date = build_date
        self.api_version = api_version
        self.status = status
        self.premium = premium
        super().__init__(_data)


class CheckPostResponses200SchemaLanguage(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema/properties/language
    
    The language used for checking the text.
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        code=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        detected_language=None  # type: Optional[Union[CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage, sob.properties.types.Null]]  # noqa
    ):
        self.name = name
        self.code = code
        self.detected_language = detected_language
        super().__init__(_data)


class CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage(
    sob.model.Object
):
    """
    #/paths/~1check/post/responses/200/schema/properties/language/properties/
    detectedLanguage
    
    The automatically detected text language (might be different from the
    language actually used for checking).
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        code=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        confidence=None  # type: Optional[numbers.Number]
    ):
        self.name = name
        self.code = code
        self.confidence = confidence
        super().__init__(_data)


class CheckPostResponses200SchemaMatches(sob.model.Array):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches
    """

    pass


class CheckPostResponses200SchemaPropertiesMatchesItems(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        message=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        short_message=None,  # type: Optional[str]
        offset=None,  # type: Optional[Union[int, sob.properties.types.Null]]
        length=None,  # type: Optional[Union[int, sob.properties.types.Null]]
        replacements=None,  # type: Optional[Union[CheckPostResponses200SchemaPropertiesMatchesItemsReplacements, sob.properties.types.Null]]  # noqa
        context=None,  # type: Optional[Union[CheckPostResponses200SchemaPropertiesMatchesItemsContext, sob.properties.types.Null]]  # noqa
        sentence=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        rule=None  # type: Optional[CheckPostResponses200SchemaPropertiesMatchesItemsRule]  # noqa
    ):
        self.message = message
        self.short_message = short_message
        self.offset = offset
        self.length = length
        self.replacements = replacements
        self.context = context
        self.sentence = sentence
        self.rule = rule
        super().__init__(_data)


class CheckPostResponses200SchemaPropertiesMatchesItemsReplacements(
    sob.model.Array
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/replacements
    
    Replacements that might correct the error. The array can be empty, in this
    case there is no suggested replacement.
    """

    pass


class CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesReplacementsItems(  # noqa
    sob.model.Object
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/replacements/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        value=None  # type: Optional[str]
    ):
        self.value = value
        super().__init__(_data)


class CheckPostResponses200SchemaPropertiesMatchesItemsContext(
    sob.model.Object
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/context
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        text=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        offset=None,  # type: Optional[Union[int, sob.properties.types.Null]]
        length=None  # type: Optional[Union[int, sob.properties.types.Null]]
    ):
        self.text = text
        self.offset = offset
        self.length = length
        super().__init__(_data)


class CheckPostResponses200SchemaPropertiesMatchesItemsRule(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/rule
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        id_=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        sub_id=None,  # type: Optional[str]
        description=None,  # type: Optional[Union[str, sob.properties.types.Null]]  # noqa
        urls=None,  # type: Optional[CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleUrls]  # noqa
        issue_type=None,  # type: Optional[str]
        category=None  # type: Optional[Union[CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory, sob.properties.types.Null]]  # noqa
    ):
        self.id_ = id_
        self.sub_id = sub_id
        self.description = description
        self.urls = urls
        self.issue_type = issue_type
        self.category = category
        super().__init__(_data)


class CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleUrls(
    sob.model.Array
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/rule/properties/urls
    
    An optional array of URLs with a more detailed description of the error.
    """

    pass


class CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRulePropertiesUrlsItems(  # noqa
    sob.model.Object
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/rule/properties/urls/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        value=None  # type: Optional[str]
    ):
        self.value = value
        super().__init__(_data)


class CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory(
    sob.model.Object
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/rule/properties/category
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        id_=None,  # type: Optional[str]
        name=None  # type: Optional[str]
    ):
        self.id_ = id_
        self.name = name
        super().__init__(_data)


class LanguagesGetResponses200Schema(sob.model.Array):
    """
    #/paths/~1languages/get/responses/200/schema
    """

    pass


class LanguagesGetResponses200SchemaItems(sob.model.Object):
    """
    #/paths/~1languages/get/responses/200/schema/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        code=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        long_code=None  # type: Optional[Union[str, sob.properties.types.Null]]
    ):
        self.name = name
        self.code = code
        self.long_code = long_code
        super().__init__(_data)


# #/paths/~1check/post/responses/200/schema
sob.meta.writable(
    CheckPostResponses200Schema
).properties = [
    (
        'software',
        sob.properties.Property(
            types=sob.properties.types.Types([
                CheckPostResponses200SchemaSoftware
            ])
        )
    ),
    (
        'language',
        sob.properties.Property(
            types=sob.properties.types.Types([
                CheckPostResponses200SchemaLanguage
            ])
        )
    ),
    (
        'matches',
        sob.properties.Property(
            types=sob.properties.types.Types([
                CheckPostResponses200SchemaMatches
            ])
        )
    )
]

# #/paths/~1check/post/responses/200/schema/properties/software
sob.meta.writable(
    CheckPostResponses200SchemaSoftware
).properties = [
    (
        'name',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'version',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'build_date',
        sob.properties.Property(
            name='buildDate',
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'api_version',
        sob.properties.Property(
            name='apiVersion',
            types=sob.properties.types.Types([
                sob.properties.Integer(),
                sob.properties.types.Null
            ])
        )
    ),
    ('status', sob.properties.String()),
    ('premium', sob.properties.Boolean())
]

# #/paths/~1check/post/responses/200/schema/properties/language
sob.meta.writable(
    CheckPostResponses200SchemaLanguage
).properties = [
    (
        'name',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'detected_language',
        sob.properties.Property(
            name='detectedLanguage',
            types=sob.properties.types.Types([
                sob.properties.Property(
                    types=sob.properties.types.Types([
                        CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage  # noqa
                    ])
                ),
                sob.properties.types.Null
            ])
        )
    )
]

# #/paths/~1check/post/responses/200/schema/properties/language/properties/
# detectedLanguage
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage
).properties = [
    (
        'name',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    ('confidence', sob.properties.Number())
]

# #/paths/~1check/post/responses/200/schema/properties/matches
sob.meta.writable(
    CheckPostResponses200SchemaMatches
).item_types = sob.properties.types.Types([
    CheckPostResponses200SchemaPropertiesMatchesItems
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItems
).properties = [
    (
        'message',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'short_message',
        sob.properties.String(
            name='shortMessage'
        )
    ),
    (
        'offset',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.Integer(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.Integer(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'replacements',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.Property(
                    types=sob.properties.types.Types([
                        CheckPostResponses200SchemaPropertiesMatchesItemsReplacements  # noqa
                    ])
                ),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'context',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.Property(
                    types=sob.properties.types.Types([
                        CheckPostResponses200SchemaPropertiesMatchesItemsContext  # noqa
                    ])
                ),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'sentence',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'rule',
        sob.properties.Property(
            types=sob.properties.types.Types([
                CheckPostResponses200SchemaPropertiesMatchesItemsRule
            ])
        )
    )
]

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/replacements
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsReplacements
).item_types = sob.properties.types.Types([
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesReplacementsItems  # noqa
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/replacements/items
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesReplacementsItems  # noqa
).properties = [
    ('value', sob.properties.String())
]

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/context
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsContext
).properties = [
    (
        'text',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'offset',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.Integer(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.Integer(),
                sob.properties.types.Null
            ])
        )
    )
]

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsRule
).properties = [
    (
        'id_',
        sob.properties.Property(
            name='id',
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'sub_id',
        sob.properties.String(
            name='subId'
        )
    ),
    (
        'description',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'urls',
        sob.properties.Property(
            types=sob.properties.types.Types([
                CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleUrls  # noqa
            ])
        )
    ),
    (
        'issue_type',
        sob.properties.String(
            name='issueType'
        )
    ),
    (
        'category',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.Property(
                    types=sob.properties.types.Types([
                        CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory  # noqa
                    ])
                ),
                sob.properties.types.Null
            ])
        )
    )
]

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/urls
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleUrls
).item_types = sob.properties.types.Types([
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRulePropertiesUrlsItems  # noqa
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/urls/items
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRulePropertiesUrlsItems  # noqa
).properties = [
    ('value', sob.properties.String())
]

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/category
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory
).properties = [
    (
        'id_',
        sob.properties.String(
            name='id'
        )
    ),
    ('name', sob.properties.String())
]

# #/paths/~1languages/get/responses/200/schema
sob.meta.writable(
    LanguagesGetResponses200Schema
).item_types = sob.properties.types.Types([
    LanguagesGetResponses200SchemaItems
])

# #/paths/~1languages/get/responses/200/schema/items
sob.meta.writable(
    LanguagesGetResponses200SchemaItems
).properties = [
    (
        'name',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    ),
    (
        'long_code',
        sob.properties.Property(
            name='longCode',
            types=sob.properties.types.Types([
                sob.properties.String(),
                sob.properties.types.Null
            ])
        )
    )
]
