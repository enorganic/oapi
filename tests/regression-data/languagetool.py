from __future__ import annotations
import typing
import sob


class CheckPostResponse(sob.Object):
    """
    Attributes:
        software:
        language: The language used for checking the text.
        matches:
    """

    __slots__: tuple[str, ...] = (
        "software",
        "language",
        "matches",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        software: (
            CheckPostResponseSoftware
            | sob.Null
            | None
        ) = None,
        language: (
            CheckPostResponseLanguage
            | sob.Null
            | None
        ) = None,
        matches: (
            CheckPostResponseMatches
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.software: (
            CheckPostResponseSoftware
            | sob.Null
            | None
        ) = software
        self.language: (
            CheckPostResponseLanguage
            | sob.Null
            | None
        ) = language
        self.matches: (
            CheckPostResponseMatches
            | sob.Null
            | None
        ) = matches
        super().__init__(_data)


class CheckPostResponseLanguage(sob.Object):
    """
    The language used for checking the text.

    Attributes:
        name: Language name like 'French' or 'English (US)'.
        code: ISO 639-1 code like 'en', 'en-US', or 'ca-ES-valencia'
        detected_language: The automatically detected text language (might
            be different from the language actually used for checking).
    """

    __slots__: tuple[str, ...] = (
        "name",
        "code",
        "detected_language",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | sob.Null
            | None
        ) = None,
        code: (
            str
            | sob.Null
            | None
        ) = None,
        detected_language: (
            CheckPostResponseLanguageDetectedLanguage
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | sob.Null
            | None
        ) = name
        self.code: (
            str
            | sob.Null
            | None
        ) = code
        self.detected_language: (
            CheckPostResponseLanguageDetectedLanguage
            | sob.Null
            | None
        ) = detected_language
        super().__init__(_data)


class CheckPostResponseLanguageDetectedLanguage(sob.Object):
    """
    The automatically detected text language (might be different from the
    language actually used for checking).

    Attributes:
        name: Language name like 'French' or 'English (US)'.
        code: ISO 639-1 code like 'en', 'en-US', or 'ca-ES-valencia'.
    """

    __slots__: tuple[str, ...] = (
        "name",
        "code",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | sob.Null
            | None
        ) = None,
        code: (
            str
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | sob.Null
            | None
        ) = name
        self.code: (
            str
            | sob.Null
            | None
        ) = code
        super().__init__(_data)


class CheckPostResponseMatches(sob.Array):

    def __init__(
        self,
        items: (
            typing.Iterable[
                CheckPostResponseMatchesItem
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItem(sob.Object):
    """
    Attributes:
        message: Message about the error displayed to the user.
        short_message: An optional shorter version of 'message'.
        offset: The 0-based character offset of the error in the text.
        length: The length of the error in characters.
        replacements: Replacements that might correct the error. The array
            can be empty, in this case there is no suggested replacement.
        context:
        sentence: The sentence the error occurred in (since LanguageTool 4.
            0 or later)
        rule:
    """

    __slots__: tuple[str, ...] = (
        "message",
        "short_message",
        "offset",
        "length",
        "replacements",
        "context",
        "sentence",
        "rule",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        message: (
            str
            | sob.Null
            | None
        ) = None,
        short_message: (
            str
            | sob.Null
            | None
        ) = None,
        offset: (
            int
            | sob.Null
            | None
        ) = None,
        length: (
            int
            | sob.Null
            | None
        ) = None,
        replacements: (
            CheckPostResponseMatchesItemReplacements
            | sob.Null
            | None
        ) = None,
        context: (
            CheckPostResponseMatchesItemContext
            | sob.Null
            | None
        ) = None,
        sentence: (
            str
            | sob.Null
            | None
        ) = None,
        rule: (
            CheckPostResponseMatchesItemRule
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.message: (
            str
            | sob.Null
            | None
        ) = message
        self.short_message: (
            str
            | sob.Null
            | None
        ) = short_message
        self.offset: (
            int
            | sob.Null
            | None
        ) = offset
        self.length: (
            int
            | sob.Null
            | None
        ) = length
        self.replacements: (
            CheckPostResponseMatchesItemReplacements
            | sob.Null
            | None
        ) = replacements
        self.context: (
            CheckPostResponseMatchesItemContext
            | sob.Null
            | None
        ) = context
        self.sentence: (
            str
            | sob.Null
            | None
        ) = sentence
        self.rule: (
            CheckPostResponseMatchesItemRule
            | sob.Null
            | None
        ) = rule
        super().__init__(_data)


class CheckPostResponseMatchesItemContext(sob.Object):
    """
    Attributes:
        text: Context of the error, i.e. the error and some text to the
            left and to the left.
        offset: The 0-based character offset of the error in the context
            text.
        length: The length of the error in characters in the context.
    """

    __slots__: tuple[str, ...] = (
        "text",
        "offset",
        "length",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        text: (
            str
            | sob.Null
            | None
        ) = None,
        offset: (
            int
            | sob.Null
            | None
        ) = None,
        length: (
            int
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.text: (
            str
            | sob.Null
            | None
        ) = text
        self.offset: (
            int
            | sob.Null
            | None
        ) = offset
        self.length: (
            int
            | sob.Null
            | None
        ) = length
        super().__init__(_data)


class CheckPostResponseMatchesItemReplacements(sob.Array):
    """
    Replacements that might correct the error. The array can be empty, in this
    case there is no suggested replacement.
    """

    def __init__(
        self,
        items: (
            typing.Iterable[
                CheckPostResponseMatchesItemReplacementsItem
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemReplacementsItem(sob.Object):
    """
    Attributes:
        value: the replacement string
    """

    __slots__: tuple[str, ...] = (
        "value",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        value: (
            str
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.value: (
            str
            | sob.Null
            | None
        ) = value
        super().__init__(_data)


class CheckPostResponseMatchesItemRule(sob.Object):
    """
    Attributes:
        id_: An rule's identifier that's unique for this language.
        sub_id: An optional sub identifier of the rule, used when several
            rules are grouped.
        description:
        urls: An optional array of URLs with a more detailed description of
            the error.
        issue_type: The <a href="http://www.w3.org/International/
            multilingualweb/lt/drafts/its20/its20.html#lqissue-typevalues">
            Localization Quality Issue Type</a>. This is not defined for all
            languages, in which case it will always be 'Uncategorized'.
        category:
    """

    __slots__: tuple[str, ...] = (
        "id_",
        "sub_id",
        "description",
        "urls",
        "issue_type",
        "category",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        id_: (
            str
            | sob.Null
            | None
        ) = None,
        sub_id: (
            str
            | sob.Null
            | None
        ) = None,
        description: (
            str
            | sob.Null
            | None
        ) = None,
        urls: (
            CheckPostResponseMatchesItemRuleUrls
            | sob.Null
            | None
        ) = None,
        issue_type: (
            str
            | sob.Null
            | None
        ) = None,
        category: (
            CheckPostResponseMatchesItemRuleCategory
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.id_: (
            str
            | sob.Null
            | None
        ) = id_
        self.sub_id: (
            str
            | sob.Null
            | None
        ) = sub_id
        self.description: (
            str
            | sob.Null
            | None
        ) = description
        self.urls: (
            CheckPostResponseMatchesItemRuleUrls
            | sob.Null
            | None
        ) = urls
        self.issue_type: (
            str
            | sob.Null
            | None
        ) = issue_type
        self.category: (
            CheckPostResponseMatchesItemRuleCategory
            | sob.Null
            | None
        ) = category
        super().__init__(_data)


class CheckPostResponseMatchesItemRuleCategory(sob.Object):
    """
    Attributes:
        id_: A category's identifier that's unique for this language.
        name: A short description of the category.
    """

    __slots__: tuple[str, ...] = (
        "id_",
        "name",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        id_: (
            str
            | sob.Null
            | None
        ) = None,
        name: (
            str
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.id_: (
            str
            | sob.Null
            | None
        ) = id_
        self.name: (
            str
            | sob.Null
            | None
        ) = name
        super().__init__(_data)


class CheckPostResponseMatchesItemRuleUrls(sob.Array):
    """
    An optional array of URLs with a more detailed description of the error.
    """

    def __init__(
        self,
        items: (
            typing.Iterable[
                CheckPostResponseMatchesItemRuleUrlsItem
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemRuleUrlsItem(sob.Object):
    """
    Attributes:
        value: the URL
    """

    __slots__: tuple[str, ...] = (
        "value",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        value: (
            str
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.value: (
            str
            | sob.Null
            | None
        ) = value
        super().__init__(_data)


class CheckPostResponseSoftware(sob.Object):
    """
    Attributes:
        name: Usually 'LanguageTool'.
        version: A version string like '3.3' or '3.4-SNAPSHOT'.
        build_date: Date when the software was built, e.g. '2016-05-25'.
        api_version: Version of this API response. We don't expect to make
            incompatible changes, so this can also be increased for newly added
            fields.
        status: An optional warning, e.g. when the API format is not
            stable.
        premium: true if you're using a Premium account with all the
            premium text checks (since LanguageTool 4.2)
    """

    __slots__: tuple[str, ...] = (
        "name",
        "version",
        "build_date",
        "api_version",
        "status",
        "premium",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | sob.Null
            | None
        ) = None,
        version: (
            str
            | sob.Null
            | None
        ) = None,
        build_date: (
            str
            | sob.Null
            | None
        ) = None,
        api_version: (
            int
            | sob.Null
            | None
        ) = None,
        status: (
            str
            | sob.Null
            | None
        ) = None,
        premium: (
            bool
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | sob.Null
            | None
        ) = name
        self.version: (
            str
            | sob.Null
            | None
        ) = version
        self.build_date: (
            str
            | sob.Null
            | None
        ) = build_date
        self.api_version: (
            int
            | sob.Null
            | None
        ) = api_version
        self.status: (
            str
            | sob.Null
            | None
        ) = status
        self.premium: (
            bool
            | sob.Null
            | None
        ) = premium
        super().__init__(_data)


class LanguagesGetResponse(sob.Array):

    def __init__(
        self,
        items: (
            typing.Iterable[
                LanguagesGetResponseItem
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None
    ) -> None:
        super().__init__(items)


class LanguagesGetResponseItem(sob.Object):
    """
    Attributes:
        name: a language name like 'French' or 'English (Australia)'
        code: a language code like 'en'
        long_code: a language code like 'en-US' or 'ca-ES-valencia'
    """

    __slots__: tuple[str, ...] = (
        "name",
        "code",
        "long_code",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | sob.Null
            | None
        ) = None,
        code: (
            str
            | sob.Null
            | None
        ) = None,
        long_code: (
            str
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | sob.Null
            | None
        ) = name
        self.code: (
            str
            | sob.Null
            | None
        ) = code
        self.long_code: (
            str
            | sob.Null
            | None
        ) = long_code
        super().__init__(_data)


class WordsGetResponse(sob.Object):
    """
    Attributes:
        words: array of words
    """

    __slots__: tuple[str, ...] = (
        "words",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        words: (
            WordsGetResponseWords
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.words: (
            WordsGetResponseWords
            | sob.Null
            | None
        ) = words
        super().__init__(_data)


class WordsGetResponseWords(sob.Array):
    """
    array of words
    """

    def __init__(
        self,
        items: (
            typing.Iterable[
                str
                | sob.Null
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None
    ) -> None:
        super().__init__(items)


class WordsAddPostResponse(sob.Object):
    """
    Attributes:
        added: true if the word has been added. false means the word hasn't
            been added because it had been added before.
    """

    __slots__: tuple[str, ...] = (
        "added",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        added: (
            bool
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.added: (
            bool
            | sob.Null
            | None
        ) = added
        super().__init__(_data)


class WordsDeletePostResponse(sob.Object):
    """
    Attributes:
        deleted: true if the word has been removed. false means the word
            hasn't been removed because it was not in the dictionary.
    """

    __slots__: tuple[str, ...] = (
        "deleted",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        deleted: (
            bool
            | sob.Null
            | None
        ) = None
    ) -> None:
        self.deleted: (
            bool
            | sob.Null
            | None
        ) = deleted
        super().__init__(_data)


sob.get_writable_object_meta(  # type: ignore
    CheckPostResponse
).properties = sob.Properties([
    (
        'software',
        sob.Property(
            types=sob.MutableTypes([
                CheckPostResponseSoftware,
                sob.Null
            ])
        )
    ),
    (
        'language',
        sob.Property(
            types=sob.MutableTypes([
                CheckPostResponseLanguage,
                sob.Null
            ])
        )
    ),
    (
        'matches',
        sob.Property(
            types=sob.MutableTypes([
                CheckPostResponseMatches,
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseLanguage
).properties = sob.Properties([
    (
        'name',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'code',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'detected_language',
        sob.Property(
            name="detectedLanguage",
            required=True,
            types=sob.MutableTypes([
                CheckPostResponseLanguageDetectedLanguage,
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseLanguageDetectedLanguage
).properties = sob.Properties([
    (
        'name',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'code',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_array_meta(  # type: ignore
    CheckPostResponseMatches
).item_types = sob.MutableTypes([
    CheckPostResponseMatchesItem
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseMatchesItem
).properties = sob.Properties([
    (
        'message',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'short_message',
        sob.Property(
            name="shortMessage",
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'offset',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.IntegerProperty(),
                sob.Null
            ])
        )
    ),
    (
        'length',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.IntegerProperty(),
                sob.Null
            ])
        )
    ),
    (
        'replacements',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                CheckPostResponseMatchesItemReplacements,
                sob.Null
            ])
        )
    ),
    (
        'context',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                CheckPostResponseMatchesItemContext,
                sob.Null
            ])
        )
    ),
    (
        'sentence',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'rule',
        sob.Property(
            types=sob.MutableTypes([
                CheckPostResponseMatchesItemRule,
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseMatchesItemContext
).properties = sob.Properties([
    (
        'text',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'offset',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.IntegerProperty(),
                sob.Null
            ])
        )
    ),
    (
        'length',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.IntegerProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_array_meta(  # type: ignore
    CheckPostResponseMatchesItemReplacements
).item_types = sob.MutableTypes([
    CheckPostResponseMatchesItemReplacementsItem
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseMatchesItemReplacementsItem
).properties = sob.Properties([
    (
        'value',
        sob.Property(
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseMatchesItemRule
).properties = sob.Properties([
    (
        'id_',
        sob.Property(
            name="id",
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'sub_id',
        sob.Property(
            name="subId",
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'description',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'urls',
        sob.Property(
            types=sob.MutableTypes([
                CheckPostResponseMatchesItemRuleUrls,
                sob.Null
            ])
        )
    ),
    (
        'issue_type',
        sob.Property(
            name="issueType",
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'category',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                CheckPostResponseMatchesItemRuleCategory,
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseMatchesItemRuleCategory
).properties = sob.Properties([
    (
        'id_',
        sob.Property(
            name="id",
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'name',
        sob.Property(
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_array_meta(  # type: ignore
    CheckPostResponseMatchesItemRuleUrls
).item_types = sob.MutableTypes([
    CheckPostResponseMatchesItemRuleUrlsItem
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseMatchesItemRuleUrlsItem
).properties = sob.Properties([
    (
        'value',
        sob.Property(
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    CheckPostResponseSoftware
).properties = sob.Properties([
    (
        'name',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'version',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'build_date',
        sob.Property(
            name="buildDate",
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'api_version',
        sob.Property(
            name="apiVersion",
            required=True,
            types=sob.MutableTypes([
                sob.IntegerProperty(),
                sob.Null
            ])
        )
    ),
    (
        'status',
        sob.Property(
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'premium',
        sob.Property(
            types=sob.MutableTypes([
                sob.BooleanProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_array_meta(  # type: ignore
    LanguagesGetResponse
).item_types = sob.MutableTypes([
    LanguagesGetResponseItem
])
sob.get_writable_object_meta(  # type: ignore
    LanguagesGetResponseItem
).properties = sob.Properties([
    (
        'name',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'code',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    ),
    (
        'long_code',
        sob.Property(
            name="longCode",
            required=True,
            types=sob.MutableTypes([
                sob.StringProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    WordsGetResponse
).properties = sob.Properties([
    (
        'words',
        sob.Property(
            types=sob.MutableTypes([
                WordsGetResponseWords,
                sob.Null
            ])
        )
    )
])
sob.get_writable_array_meta(  # type: ignore
    WordsGetResponseWords
).item_types = sob.MutableTypes([
    sob.Property(
        types=sob.MutableTypes([
            sob.StringProperty(),
            sob.Null
        ])
    )
])
sob.get_writable_object_meta(  # type: ignore
    WordsAddPostResponse
).properties = sob.Properties([
    (
        'added',
        sob.Property(
            types=sob.MutableTypes([
                sob.BooleanProperty(),
                sob.Null
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    WordsDeletePostResponse
).properties = sob.Properties([
    (
        'deleted',
        sob.Property(
            types=sob.MutableTypes([
                sob.BooleanProperty(),
                sob.Null
            ])
        )
    )
])
# The following is used to retain class names when re-generating
# this model from an updated OpenAPI document
_POINTERS_CLASSES: dict[str, type[sob.abc.Model]] = {
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
