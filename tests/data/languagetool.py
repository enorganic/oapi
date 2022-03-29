import typing
import sob


class CheckPostResponse(sob.model.Object):
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
            "CheckPostResponseSoftware"
        ] = None,
        language: typing.Optional[
            "CheckPostResponseLanguage"
        ] = None,
        matches: typing.Optional[
            "CheckPostResponseMatches"
        ] = None
    ) -> None:
        self.software = software
        self.language = language
        self.matches = matches
        super().__init__(_data)


class CheckPostResponseSoftware(sob.model.Object):
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


class CheckPostResponseLanguage(sob.model.Object):
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
                "CheckPostResponseLanguageDetectedLanguage",
                sob.utilities.types.Null
            ]
        ] = None
    ) -> None:
        self.name = name
        self.code = code
        self.detected_language = detected_language
        super().__init__(_data)


class CheckPostResponseLanguageDetectedLanguage(sob.model.Object):
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


class CheckPostResponseMatches(sob.model.Array):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponseMatchesItems"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItems(sob.model.Object):
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
                "CheckPostResponseMatchesItemsReplacements",
                sob.utilities.types.Null
            ]
        ] = None,
        context: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemsContext",
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
            "CheckPostResponseMatchesItemsRule"
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


class CheckPostResponseMatchesItemsReplacements(sob.model.Array):
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
                "CheckPostResponseMatchesItemsReplacementsItems"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemsReplacementsItems(sob.model.Object):
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


class CheckPostResponseMatchesItemsContext(sob.model.Object):
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


class CheckPostResponseMatchesItemsRule(sob.model.Object):
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
            "CheckPostResponseMatchesItemsRuleUrls"
        ] = None,
        issue_type: typing.Optional[
            str
        ] = None,
        category: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemsRuleCategory",
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


class CheckPostResponseMatchesItemsRuleUrls(sob.model.Array):
    """
    #/paths/~1check/post/responses/200/schema/properties/matches/items/
    properties/rule/properties/urls

    An optional array of URLs with a more detailed description of the error.
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponseMatchesItemsRuleUrlsItems"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemsRuleUrlsItems(sob.model.Object):
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


class CheckPostResponseMatchesItemsRuleCategory(sob.model.Object):
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


class LanguagesGetResponse(sob.model.Array):
    """
    #/paths/~1languages/get/responses/200/schema
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "LanguagesGetResponseItems"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class LanguagesGetResponseItems(sob.model.Object):
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


class WordsGetResponse(sob.model.Object):
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
            "WordsGetResponseWords"
        ] = None
    ) -> None:
        self.words = words
        super().__init__(_data)


class WordsGetResponseWords(sob.model.Array):
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


class WordsAddPostResponse(sob.model.Object):
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


class WordsDeletePostResponse(sob.model.Object):
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
    CheckPostResponse
).properties = sob.meta.Properties([
    (
        'software',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseSoftware
            ])
        )
    ),
    (
        'language',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseLanguage
            ])
        )
    ),
    (
        'matches',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseMatches
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/software
sob.meta.object_writable(  # type: ignore
    CheckPostResponseSoftware
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
            name="buildDate",
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
            name="apiVersion",
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
    CheckPostResponseLanguage
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
            name="detectedLanguage",
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseLanguageDetectedLanguage,
                sob.utilities.types.Null
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/language/properties/
# detectedLanguage
sob.meta.object_writable(  # type: ignore
    CheckPostResponseLanguageDetectedLanguage
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
    CheckPostResponseMatches
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItems
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItems
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
            name="shortMessage"
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
                CheckPostResponseMatchesItemsReplacements,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'context',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemsContext,
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
                CheckPostResponseMatchesItemsRule
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/replacements
sob.meta.array_writable(  # type: ignore
    CheckPostResponseMatchesItemsReplacements
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItemsReplacementsItems
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/replacements/items
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemsReplacementsItems
).properties = sob.meta.Properties([
    ('value', sob.properties.String())
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/context
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemsContext
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
    CheckPostResponseMatchesItemsRule
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.Property(
            name="id",
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
            name="subId"
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
                CheckPostResponseMatchesItemsRuleUrls
            ])
        )
    ),
    (
        'issue_type',
        sob.properties.String(
            name="issueType"
        )
    ),
    (
        'category',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemsRuleCategory,
                sob.utilities.types.Null
            ])
        )
    )
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/urls
sob.meta.array_writable(  # type: ignore
    CheckPostResponseMatchesItemsRuleUrls
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItemsRuleUrlsItems
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/urls/items
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemsRuleUrlsItems
).properties = sob.meta.Properties([
    ('value', sob.properties.String())
])

# #/paths/~1check/post/responses/200/schema/properties/matches/items/
# properties/rule/properties/category
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemsRuleCategory
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.String(
            name="id"
        )
    ),
    ('name', sob.properties.String())
])

# #/paths/~1languages/get/responses/200/schema
sob.meta.array_writable(  # type: ignore
    LanguagesGetResponse
).item_types = sob.types.MutableTypes([
    LanguagesGetResponseItems
])

# #/paths/~1languages/get/responses/200/schema/items
sob.meta.object_writable(  # type: ignore
    LanguagesGetResponseItems
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
            name="longCode",
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
    WordsGetResponse
).properties = sob.meta.Properties([
    (
        'words',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                WordsGetResponseWords
            ])
        )
    )
])

# #/paths/~1words/get/responses/200/schema/properties/words
sob.meta.array_writable(  # type: ignore
    WordsGetResponseWords
).item_types = sob.types.MutableTypes([
    sob.properties.String()
])

# #/paths/~1words~1add/post/responses/200/schema
sob.meta.object_writable(  # type: ignore
    WordsAddPostResponse
).properties = sob.meta.Properties([
    ('added', sob.properties.Boolean())
])

# #/paths/~1words~1delete/post/responses/200/schema
sob.meta.object_writable(  # type: ignore
    WordsDeletePostResponse
).properties = sob.meta.Properties([
    ('deleted', sob.properties.Boolean())
])
