import typing
import sob


class CheckPostResponse(sob.model.Object):
    """
    Attributes:
        software:
        language:
            The language used for checking the text.
        matches:
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
            typing.Union[
                "CheckPostResponseSoftware",
                sob.types.Null
            ]
        ] = None,
        language: typing.Optional[
            typing.Union[
                "CheckPostResponseLanguage",
                sob.types.Null
            ]
        ] = None,
        matches: typing.Optional[
            typing.Union[
                "CheckPostResponseMatches",
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.software: typing.Optional[
            typing.Union[
                "CheckPostResponseSoftware",
                sob.types.Null
            ]
        ] = software
        self.language: typing.Optional[
            typing.Union[
                "CheckPostResponseLanguage",
                sob.types.Null
            ]
        ] = language
        self.matches: typing.Optional[
            typing.Union[
                "CheckPostResponseMatches",
                sob.types.Null
            ]
        ] = matches
        super().__init__(_data)


class CheckPostResponseLanguage(sob.model.Object):
    """
    The language used for checking the text.

    Attributes:
        name:
            Language name like 'French' or 'English (US)'.
        code:
            ISO 639-1 code like 'en', 'en-US', or 'ca-ES-valencia'
        detected_language:
            The automatically detected text language (might be different from
            the language actually used for checking).
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
                sob.types.Null
            ]
        ] = None,
        code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        detected_language: typing.Optional[
            typing.Union[
                "CheckPostResponseLanguageDetectedLanguage",
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.name: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = name
        self.code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = code
        self.detected_language: typing.Optional[
            typing.Union[
                "CheckPostResponseLanguageDetectedLanguage",
                sob.types.Null
            ]
        ] = detected_language
        super().__init__(_data)


class CheckPostResponseLanguageDetectedLanguage(sob.model.Object):
    """
    The automatically detected text language (might be different from the
    language actually used for checking).

    Attributes:
        name:
            Language name like 'French' or 'English (US)'.
        code:
            ISO 639-1 code like 'en', 'en-US', or 'ca-ES-valencia'.
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
                sob.types.Null
            ]
        ] = None,
        code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.name: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = name
        self.code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = code
        super().__init__(_data)


class CheckPostResponseMatches(sob.model.Array):

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponseMatchesItem"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItem(sob.model.Object):
    """
    Attributes:
        message:
            Message about the error displayed to the user.
        short_message:
            An optional shorter version of 'message'.
        offset:
            The 0-based character offset of the error in the text.
        length:
            The length of the error in characters.
        replacements:
            Replacements that might correct the error. The array can be empty,
            in this case there is no suggested replacement.
        context:
        sentence:
            The sentence the error occurred in (since LanguageTool 4.0 or later
            )
        rule:
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
                sob.types.Null
            ]
        ] = None,
        short_message: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        offset: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = None,
        length: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = None,
        replacements: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemReplacements",
                sob.types.Null
            ]
        ] = None,
        context: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemContext",
                sob.types.Null
            ]
        ] = None,
        sentence: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        rule: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemRule",
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.message: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = message
        self.short_message: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = short_message
        self.offset: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = offset
        self.length: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = length
        self.replacements: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemReplacements",
                sob.types.Null
            ]
        ] = replacements
        self.context: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemContext",
                sob.types.Null
            ]
        ] = context
        self.sentence: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = sentence
        self.rule: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemRule",
                sob.types.Null
            ]
        ] = rule
        super().__init__(_data)


class CheckPostResponseMatchesItemContext(sob.model.Object):
    """
    Attributes:
        text:
            Context of the error, i.e. the error and some text to the left and
            to the left.
        offset:
            The 0-based character offset of the error in the context text.
        length:
            The length of the error in characters in the context.
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
                sob.types.Null
            ]
        ] = None,
        offset: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = None,
        length: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.text: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = text
        self.offset: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = offset
        self.length: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = length
        super().__init__(_data)


class CheckPostResponseMatchesItemReplacements(sob.model.Array):
    """
    Replacements that might correct the error. The array can be empty, in this
    case there is no suggested replacement.
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponseMatchesItemReplacementsItem"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemReplacementsItem(sob.model.Object):
    """
    Attributes:
        value:
            the replacement string
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
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.value: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = value
        super().__init__(_data)


class CheckPostResponseMatchesItemRule(sob.model.Object):
    """
    Attributes:
        id_:
            An rule's identifier that's unique for this language.
        sub_id:
            An optional sub identifier of the rule, used when several rules are
            grouped.
        description:
        urls:
            An optional array of URLs with a more detailed description of the
            error.
        issue_type:
            The <a href="http://www.w3.org/International/multilingualweb/lt/
            drafts/its20/its20.html#lqissue-typevalues">Localization Quality
            Issue Type</a>. This is not defined for all languages, in which
            case it will always be 'Uncategorized'.
        category:
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
                sob.types.Null
            ]
        ] = None,
        sub_id: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        description: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        urls: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemRuleUrls",
                sob.types.Null
            ]
        ] = None,
        issue_type: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        category: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemRuleCategory",
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.id_: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = id_
        self.sub_id: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = sub_id
        self.description: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = description
        self.urls: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemRuleUrls",
                sob.types.Null
            ]
        ] = urls
        self.issue_type: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = issue_type
        self.category: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemRuleCategory",
                sob.types.Null
            ]
        ] = category
        super().__init__(_data)


class CheckPostResponseMatchesItemRuleCategory(sob.model.Object):
    """
    Attributes:
        id_:
            A category's identifier that's unique for this language.
        name:
            A short description of the category.
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
                sob.types.Null
            ]
        ] = None,
        name: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.id_: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = id_
        self.name: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = name
        super().__init__(_data)


class CheckPostResponseMatchesItemRuleUrls(sob.model.Array):
    """
    An optional array of URLs with a more detailed description of the error.
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponseMatchesItemRuleUrlsItem"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemRuleUrlsItem(sob.model.Object):
    """
    Attributes:
        value:
            the URL
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
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.value: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = value
        super().__init__(_data)


class CheckPostResponseSoftware(sob.model.Object):
    """
    Attributes:
        name:
            Usually 'LanguageTool'.
        version:
            A version string like '3.3' or '3.4-SNAPSHOT'.
        build_date:
            Date when the software was built, e.g. '2016-05-25'.
        api_version:
            Version of this API response. We don't expect to make incompatible
            changes, so this can also be increased for newly added fields.
        status:
            An optional warning, e.g. when the API format is not stable.
        premium:
            true if you're using a Premium account with all the premium text
            checks (since LanguageTool 4.2)
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
                sob.types.Null
            ]
        ] = None,
        version: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        build_date: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        api_version: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = None,
        status: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        premium: typing.Optional[
            typing.Union[
                bool,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.name: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = name
        self.version: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = version
        self.build_date: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = build_date
        self.api_version: typing.Optional[
            typing.Union[
                int,
                sob.types.Null
            ]
        ] = api_version
        self.status: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = status
        self.premium: typing.Optional[
            typing.Union[
                bool,
                sob.types.Null
            ]
        ] = premium
        super().__init__(_data)


class LanguagesGetResponse(sob.model.Array):

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "LanguagesGetResponseItem"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class LanguagesGetResponseItem(sob.model.Object):
    """
    Attributes:
        name:
            a language name like 'French' or 'English (Australia)'
        code:
            a language code like 'en'
        long_code:
            a language code like 'en-US' or 'ca-ES-valencia'
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
                sob.types.Null
            ]
        ] = None,
        code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None,
        long_code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.name: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = name
        self.code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = code
        self.long_code: typing.Optional[
            typing.Union[
                str,
                sob.types.Null
            ]
        ] = long_code
        super().__init__(_data)


class WordsGetResponse(sob.model.Object):
    """
    Attributes:
        words:
            array of words
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
            typing.Union[
                "WordsGetResponseWords",
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.words: typing.Optional[
            typing.Union[
                "WordsGetResponseWords",
                sob.types.Null
            ]
        ] = words
        super().__init__(_data)


class WordsGetResponseWords(sob.model.Array):
    """
    array of words
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                typing.Union[
                    str,
                    sob.types.Null
                ]
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
    Attributes:
        added:
            true if the word has been added. false means the word hasn't been
            added because it had been added before.
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
            typing.Union[
                bool,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.added: typing.Optional[
            typing.Union[
                bool,
                sob.types.Null
            ]
        ] = added
        super().__init__(_data)


class WordsDeletePostResponse(sob.model.Object):
    """
    Attributes:
        deleted:
            true if the word has been removed. false means the word hasn't been
            removed because it was not in the dictionary.
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
            typing.Union[
                bool,
                sob.types.Null
            ]
        ] = None
    ) -> None:
        self.deleted: typing.Optional[
            typing.Union[
                bool,
                sob.types.Null
            ]
        ] = deleted
        super().__init__(_data)


sob.meta.object_writable(  # type: ignore
    CheckPostResponse
).properties = sob.meta.Properties([
    (
        'software',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseSoftware,
                sob.types.Null
            ])
        )
    ),
    (
        'language',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseLanguage,
                sob.types.Null
            ])
        )
    ),
    (
        'matches',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseMatches,
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseLanguage
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
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
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseLanguageDetectedLanguage
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.array_writable(  # type: ignore
    CheckPostResponseMatches
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItem
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItem
).properties = sob.meta.Properties([
    (
        'message',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'short_message',
        sob.properties.Property(
            name="shortMessage",
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'offset',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.types.Null
            ])
        )
    ),
    (
        'replacements',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemReplacements,
                sob.types.Null
            ])
        )
    ),
    (
        'context',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemContext,
                sob.types.Null
            ])
        )
    ),
    (
        'sentence',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'rule',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemRule,
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemContext
).properties = sob.meta.Properties([
    (
        'text',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'offset',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.array_writable(  # type: ignore
    CheckPostResponseMatchesItemReplacements
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItemReplacementsItem
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemReplacementsItem
).properties = sob.meta.Properties([
    (
        'value',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemRule
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.Property(
            name="id",
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'sub_id',
        sob.properties.Property(
            name="subId",
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'description',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'urls',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemRuleUrls,
                sob.types.Null
            ])
        )
    ),
    (
        'issue_type',
        sob.properties.Property(
            name="issueType",
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'category',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemRuleCategory,
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemRuleCategory
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.Property(
            name="id",
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'name',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.array_writable(  # type: ignore
    CheckPostResponseMatchesItemRuleUrls
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItemRuleUrlsItem
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemRuleUrlsItem
).properties = sob.meta.Properties([
    (
        'value',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseSoftware
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'version',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'build_date',
        sob.properties.Property(
            name="buildDate",
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'api_version',
        sob.properties.Property(
            name="apiVersion",
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.types.Null
            ])
        )
    ),
    (
        'status',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'premium',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Boolean(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.array_writable(  # type: ignore
    LanguagesGetResponse
).item_types = sob.types.MutableTypes([
    LanguagesGetResponseItem
])
sob.meta.object_writable(  # type: ignore
    LanguagesGetResponseItem
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    ),
    (
        'long_code',
        sob.properties.Property(
            name="longCode",
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    WordsGetResponse
).properties = sob.meta.Properties([
    (
        'words',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                WordsGetResponseWords,
                sob.types.Null
            ])
        )
    )
])
sob.meta.array_writable(  # type: ignore
    WordsGetResponseWords
).item_types = sob.types.MutableTypes([
    sob.properties.Property(
        types=sob.types.MutableTypes([
            sob.properties.String(),
            sob.types.Null
        ])
    )
])
sob.meta.object_writable(  # type: ignore
    WordsAddPostResponse
).properties = sob.meta.Properties([
    (
        'added',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Boolean(),
                sob.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    WordsDeletePostResponse
).properties = sob.meta.Properties([
    (
        'deleted',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Boolean(),
                sob.types.Null
            ])
        )
    )
])
# The following is used to retain class names when re-generating
# this model from an updated OpenAPI document
_POINTERS_CLASSES: typing.Dict[str, typing.Type[sob.abc.Model]] = {
    "#/paths/~1check/post/responses/200/schema": CheckPostResponse,
    "#/paths/~1check/post/responses/200/schema/properties/language":
    CheckPostResponseLanguage,
    "#/paths/~1check/post/responses/200/schema/properties/language/properties/detectedLanguage":  # noqa
    CheckPostResponseLanguageDetectedLanguage,
    "#/paths/~1check/post/responses/200/schema/properties/matches":
    CheckPostResponseMatches,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items":
    CheckPostResponseMatchesItem,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/context":  # noqa
    CheckPostResponseMatchesItemContext,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements":  # noqa
    CheckPostResponseMatchesItemReplacements,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements/items":  # noqa
    CheckPostResponseMatchesItemReplacementsItem,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule":  # noqa
    CheckPostResponseMatchesItemRule,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/category":  # noqa
    CheckPostResponseMatchesItemRuleCategory,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls":  # noqa
    CheckPostResponseMatchesItemRuleUrls,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls/items":  # noqa
    CheckPostResponseMatchesItemRuleUrlsItem,
    "#/paths/~1check/post/responses/200/schema/properties/software":
    CheckPostResponseSoftware,
    "#/paths/~1languages/get/responses/200/schema": LanguagesGetResponse,
    "#/paths/~1languages/get/responses/200/schema/items":
    LanguagesGetResponseItem,
    "#/paths/~1words/get/responses/200/schema": WordsGetResponse,
    "#/paths/~1words/get/responses/200/schema/properties/words":
    WordsGetResponseWords,
    "#/paths/~1words~1add/post/responses/200/schema": WordsAddPostResponse,
    "#/paths/~1words~1delete/post/responses/200/schema":
    WordsDeletePostResponse,
}
