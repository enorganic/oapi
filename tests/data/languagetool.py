import typing
import sob


class CheckPostResponses200Schema(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        software: typing.Optional[
            "CheckPostResponses200SchemaSoftware"
        ] = None,
        language: typing.Optional[
            "CheckPostResponses200SchemaLanguage"
        ] = None,
        matches: typing.Optional[
            "CheckPostResponses200SchemaMatches"
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
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
                "CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage",  # noqa
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
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
        ] = None
    ) -> None:
        self.name = name
        self.code = code
        super().__init__(_data)


class CheckPostResponses200SchemaMatches(sob.model.Array):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponses200SchemaPropertiesMatchesItems"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponses200SchemaPropertiesMatchesItems(sob.model.Object):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
                "CheckPostResponses200SchemaPropertiesMatchesItemsReplacements",  # noqa
                sob.utilities.types.Null
            ]
        ] = None,
        context: typing.Optional[
            typing.Union[
                "CheckPostResponses200SchemaPropertiesMatchesItemsContext",
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
            "CheckPostResponses200SchemaPropertiesMatchesItemsRule"
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

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesReplacementsItems"  # noqa
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesReplacementsItems(  # noqa
    sob.model.Object
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/replacements/items
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
            "CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleUrls"  # noqa
        ] = None,
        issue_type: typing.Optional[
            str
        ] = None,
        category: typing.Optional[
            typing.Union[
                "CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory",  # noqa
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

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRulePropertiesUrlsItems"  # noqa
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRulePropertiesUrlsItems(  # noqa
    sob.model.Object
):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/rule/properties/urls/items
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "LanguagesGetResponses200SchemaItems"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class LanguagesGetResponses200SchemaItems(sob.model.Object):
    """
    #/paths/~1languages/get/responses/200/schema/items
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
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


class WordsGetResponses200Schema(sob.model.Object):
    """
    #/paths/~1words/get/responses/200/schema
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        words: typing.Optional[
            "WordsGetResponses200SchemaWords"
        ] = None
    ) -> None:
        self.words = words
        super().__init__(_data)


class WordsGetResponses200SchemaWords(sob.model.Array):
    """
    #/paths/~1words/get/responses/200/schema/properties/words

    array of words
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                str
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class WordsAddPostResponses200Schema(sob.model.Object):
    """
    #/paths/~1words~1add/post/responses/200/schema
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        added: typing.Optional[
            bool
        ] = None
    ) -> None:
        self.added = added
        super().__init__(_data)


class WordsDeletePostResponses200Schema(sob.model.Object):
    """
    #/paths/~1words~1delete/post/responses/200/schema
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        deleted: typing.Optional[
            bool
        ] = None
    ) -> None:
        self.deleted = deleted
        super().__init__(_data)


# #/paths/~1check/post/responses/200/schema
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200Schema
).properties = sob.meta.Properties([
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
])

# #/paths/~1check/post/responses/200/schema/properties/software
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaSoftware
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'version',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'build_date',
        sob.properties.Property(
            name='buildDate',
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'api_version',
        sob.properties.Property(
            name='apiVersion',
            required=True,
            types=sob.types.MutableTypes([
                int,
                sob.utilities.types.Null
            ])
        )
    ),
    ('status', sob.properties.String()),
    ('premium', sob.properties.Boolean())
])

# #/paths/~1check/post/responses/200/schema/properties/language
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaLanguage
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'detected_language',
        sob.properties.Property(
            name='detectedLanguage',
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage,  # noqa
                sob.utilities.types.Null
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/language/properties/
# detectedLanguage
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesLanguageDetectedLanguage
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/matches
sob.meta.array_writable(  # type: ignore
    CheckPostResponses200SchemaMatches
).item_types = sob.types.MutableTypes([
    CheckPostResponses200SchemaPropertiesMatchesItems
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItems
).properties = sob.meta.Properties([
    (
        'message',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
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
            required=True,
            types=sob.types.MutableTypes([
                int,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                int,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'replacements',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponses200SchemaPropertiesMatchesItemsReplacements,  # noqa
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'context',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponses200SchemaPropertiesMatchesItemsContext,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'sentence',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
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
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/replacements
sob.meta.array_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItemsReplacements
).item_types = sob.types.MutableTypes([
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesReplacementsItems  # noqa
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/replacements/items
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesReplacementsItems  # noqa
).properties = sob.meta.Properties([
    ('value', sob.properties.String())
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/context
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItemsContext
).properties = sob.meta.Properties([
    (
        'text',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'offset',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                int,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                int,
                sob.utilities.types.Null
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItemsRule
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.Property(
            name='id',
            required=True,
            types=sob.types.MutableTypes([
                str,
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
            required=True,
            types=sob.types.MutableTypes([
                str,
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
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory,  # noqa
                sob.utilities.types.Null
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/urls
sob.meta.array_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleUrls
).item_types = sob.types.MutableTypes([
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRulePropertiesUrlsItems  # noqa
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/urls/items
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRulePropertiesUrlsItems  # noqa
).properties = sob.meta.Properties([
    ('value', sob.properties.String())
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/category
sob.meta.object_writable(  # type: ignore
    CheckPostResponses200SchemaPropertiesMatchesItemsPropertiesRuleCategory
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.String(
            name='id'
        )
    ),
    ('name', sob.properties.String())
])

# #/paths/~1languages/get/responses/200/schema
sob.meta.array_writable(  # type: ignore
    LanguagesGetResponses200Schema
).item_types = sob.types.MutableTypes([
    LanguagesGetResponses200SchemaItems
])

# #/paths/~1languages/get/responses/200/schema/items
sob.meta.object_writable(  # type: ignore
    LanguagesGetResponses200SchemaItems
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'long_code',
        sob.properties.Property(
            name='longCode',
            required=True,
            types=sob.types.MutableTypes([
                str,
                sob.utilities.types.Null
            ])
        )
    )
])

# #/paths/~1words/get/responses/200/schema
sob.meta.object_writable(  # type: ignore
    WordsGetResponses200Schema
).properties = sob.meta.Properties([
    (
        'words',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                WordsGetResponses200SchemaWords
            ])
        )
    )
])

# #/paths/~1words/get/responses/200/schema/properties/words
sob.meta.array_writable(  # type: ignore
    WordsGetResponses200SchemaWords
).item_types = sob.types.MutableTypes([
    sob.properties.String()
])

# #/paths/~1words~1add/post/responses/200/schema
sob.meta.object_writable(  # type: ignore
    WordsAddPostResponses200Schema
).properties = sob.meta.Properties([
    ('added', sob.properties.Boolean())
])

# #/paths/~1words~1delete/post/responses/200/schema
sob.meta.object_writable(  # type: ignore
    WordsDeletePostResponses200Schema
).properties = sob.meta.Properties([
    ('deleted', sob.properties.Boolean())
])
