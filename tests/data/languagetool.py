import typing
import io
import sob


class CheckPostResponses200Schema(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema
    """

    def __init__(
        self,
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        software: typing.Optional[
            'CheckPostResponses200SchemaSoftware'
        ] = None,
        language: typing.Optional[
            'CheckPostResponses200SchemaLanguage'
        ] = None,
        matches: typing.Optional[
            'CheckPostResponses200SchemaMatches'
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        name: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        version: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        build_date: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        api_version: typing.Optional[
            typing.Union[
                int,
                sob.utilities.types.Null
            ]
        ] = None,
        status: typing.Optional[
            str
        ] = None,
        premium: typing.Optional[
            bool
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        name: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        code: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        detected_language: typing.Optional[
            typing.Union[
                (
                    'CheckPostResponses200SchemaPropertiesLanguageDetectedLang'
                    'uage'
                ),
                sob.utilities.types.Null
            ]
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        name: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        code: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        confidence: typing.Optional[
            typing.Union[int, float]
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        message: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        short_message: typing.Optional[
            str
        ] = None,
        offset: typing.Optional[
            typing.Union[
                int,
                sob.utilities.types.Null
            ]
        ] = None,
        length: typing.Optional[
            typing.Union[
                int,
                sob.utilities.types.Null
            ]
        ] = None,
        replacements: typing.Optional[
            typing.Union[
                (
                    'CheckPostResponses200SchemaPropertiesMatchesItemsReplacem'
                    'ents'
                ),
                sob.utilities.types.Null
            ]
        ] = None,
        context: typing.Optional[
            typing.Union[
                'CheckPostResponses200SchemaPropertiesMatchesItemsContext',
                sob.utilities.types.Null
            ]
        ] = None,
        sentence: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        rule: typing.Optional[
            'CheckPostResponses200SchemaPropertiesMatchesItemsRule'
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        value: typing.Optional[
            str
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        text: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        offset: typing.Optional[
            typing.Union[
                int,
                sob.utilities.types.Null
            ]
        ] = None,
        length: typing.Optional[
            typing.Union[
                int,
                sob.utilities.types.Null
            ]
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        id_: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        sub_id: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        urls: typing.Optional[
            (
                'CheckPostResponses200SchemaPropertiesMatchesItemsProperti'
                'esRuleUrls'
            )
        ] = None,
        issue_type: typing.Optional[
            str
        ] = None,
        category: typing.Optional[
            typing.Union[
                (
                    'CheckPostResponses200SchemaPropertiesMatchesItemsProperti'
                    'esRuleCategory'
                ),
                sob.utilities.types.Null
            ]
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        value: typing.Optional[
            str
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        id_: typing.Optional[
            str
        ] = None,
        name: typing.Optional[
            str
        ] = None
    ) -> None:
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
        _data: typing.Optional[
            typing.Union[
                str,
                bytes,
                dict,
                typing.Sequence,
                io.IOBase
            ]
        ] = None,
        name: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        code: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None,
        long_code: typing.Optional[
            typing.Union[
                str,
                sob.utilities.types.Null
            ]
        ] = None
    ) -> None:
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
            types=sob.types.MutableTypes([
                CheckPostResponses200SchemaSoftware
            ])
        )
    ),
    (
        'language',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponses200SchemaLanguage
            ])
        )
    ),
    (
        'matches',
        sob.properties.Property(
            types=sob.types.MutableTypes([
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
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'version',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'build_date',
        sob.properties.Property(
            name='buildDate',
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'api_version',
        sob.properties.Property(
            name='apiVersion',
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
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
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'detected_language',
        sob.properties.Property(
            name='detectedLanguage',
            types=sob.types.MutableTypes([
                sob.properties.Property(
                    types=sob.types.MutableTypes([
                        CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage  # noqa
                    ])
                ),
                sob.utilities.types.Null
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
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    ('confidence', sob.properties.Number())
]

# #/paths/~1check/post/responses/200/schema/properties/matches
sob.meta.writable(
    CheckPostResponses200SchemaMatches
).item_types = sob.types.MutableTypes([
    CheckPostResponses200SchemaPropertiesMatchesItems
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItems
).properties = [
    (
        'message',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
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
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'replacements',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Property(
                    types=sob.types.MutableTypes([
                        CheckPostResponses200SchemaPropertiesMatchesItemsReplacements  # noqa
                    ])
                ),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'context',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Property(
                    types=sob.types.MutableTypes([
                        CheckPostResponses200SchemaPropertiesMatchesItemsContext  # noqa
                    ])
                ),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'sentence',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'rule',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponses200SchemaPropertiesMatchesItemsRule
            ])
        )
    )
]

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/replacements
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsReplacements
).item_types = sob.types.MutableTypes([
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
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'offset',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
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
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
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
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'urls',
        sob.properties.Property(
            types=sob.types.MutableTypes([
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
            types=sob.types.MutableTypes([
                sob.properties.Property(
                    types=sob.types.MutableTypes([
                        CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory  # noqa
                    ])
                ),
                sob.utilities.types.Null
            ])
        )
    )
]

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/urls
sob.meta.writable(
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleUrls
).item_types = sob.types.MutableTypes([
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
).item_types = sob.types.MutableTypes([
    LanguagesGetResponses200SchemaItems
])

# #/paths/~1languages/get/responses/200/schema/items
sob.meta.writable(
    LanguagesGetResponses200SchemaItems
).properties = [
    (
        'name',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'long_code',
        sob.properties.Property(
            name='longCode',
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    )
]
