import typing
import sob


class CheckPostResponse(sob.model.Object):
    """

    Properties:

    - software
    - language:
      The language used for checking the text.
    - matches
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


class CheckPostResponseLanguage(sob.model.Object):
    """
    The language used for checking the text.

    Properties:

    - name:
      Language name like 'French' or 'English (US)'.
    - code:
      ISO 639-1 code like 'en', 'en-US', or 'ca-ES-valencia'
    - detected_language:
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
    The automatically detected text language (might be different from the
    language actually used for checking).

    Properties:

    - name:
      Language name like 'French' or 'English (US)'.
    - code:
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

    Properties:

    - message:
      Message about the error displayed to the user.
    - short_message:
      An optional shorter version of 'message'.
    - offset:
      The 0-based character offset of the error in the text.
    - length:
      The length of the error in characters.
    - replacements:
      Replacements that might correct the error. The array can be empty, in
      this case there is no suggested replacement.
    - context
    - sentence:
      The sentence the error occurred in (since LanguageTool 4.0 or later)
    - rule
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
                "CheckPostResponseMatchesItemreplacements",
                sob.utilities.types.Null
            ]
        ] = None,
        context: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemcontext",
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
            "CheckPostResponseMatchesItemrule"
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


class CheckPostResponseMatchesItemcontext(sob.model.Object):
    """

    Properties:

    - text:
      Context of the error, i.e. the error and some text to the left and to the
      left.
    - offset:
      The 0-based character offset of the error in the context text.
    - length:
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


class CheckPostResponseMatchesItemreplacements(sob.model.Array):
    """
    Replacements that might correct the error. The array can be empty, in this
    case there is no suggested replacement.
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponseMatchesItemreplacementsItem"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemreplacementsItem(sob.model.Object):
    """

    Properties:

    - value:
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
            str
        ] = None
    ) -> None:
        self.value = value
        super().__init__(_data)


class CheckPostResponseMatchesItemrule(sob.model.Object):
    """

    Properties:

    - id_:
      An rule's identifier that's unique for this language.
    - sub_id:
      An optional sub identifier of the rule, used when several rules are
      grouped.
    - description
    - urls:
      An optional array of URLs with a more detailed description of the error.
    - issue_type:
      The <a href="http://www.w3.org/International/multilingualweb/lt/drafts/
      its20/its20.html#lqissue-typevalues">Localization Quality Issue Type</a>.
      This is not defined for all languages, in which case it will always be '
      Uncategorized'.
    - category
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
            "CheckPostResponseMatchesItemruleUrls"
        ] = None,
        issue_type: typing.Optional[
            str
        ] = None,
        category: typing.Optional[
            typing.Union[
                "CheckPostResponseMatchesItemruleCategory",
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


class CheckPostResponseMatchesItemruleCategory(sob.model.Object):
    """

    Properties:

    - id_:
      A category's identifier that's unique for this language.
    - name:
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
            str
        ] = None,
        name: typing.Optional[
            str
        ] = None
    ) -> None:
        self.id_ = id_
        self.name = name
        super().__init__(_data)


class CheckPostResponseMatchesItemruleUrls(sob.model.Array):
    """
    An optional array of URLs with a more detailed description of the error.
    """

    def __init__(
        self,
        items: typing.Union[
            typing.Iterable[
                "CheckPostResponseMatchesItemruleUrlsItem"
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None
    ) -> None:
        super().__init__(items)


class CheckPostResponseMatchesItemruleUrlsItem(sob.model.Object):
    """

    Properties:

    - value:
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
            str
        ] = None
    ) -> None:
        self.value = value
        super().__init__(_data)


class CheckPostResponseSoftware(sob.model.Object):
    """

    Properties:

    - name:
      Usually 'LanguageTool'.
    - version:
      A version string like '3.3' or '3.4-SNAPSHOT'.
    - build_date:
      Date when the software was built, e.g. '2016-05-25'.
    - api_version:
      Version of this API response. We don't expect to make incompatible
      changes, so this can also be increased for newly added fields.
    - status:
      An optional warning, e.g. when the API format is not stable.
    - premium:
      true if you're using a Premium account with all the premium text checks (
      since LanguageTool 4.2)
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

    Properties:

    - name:
      a language name like 'French' or 'English (Australia)'
    - code:
      a language code like 'en'
    - long_code:
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

    Properties:

    - words:
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
            "WordsGetResponseWords"
        ] = None
    ) -> None:
        self.words = words
        super().__init__(_data)


class WordsGetResponseWords(sob.model.Array):
    """
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

    Properties:

    - added:
      true if the word has been added. false means the word hasn't been added
      because it had been added before.
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

    Properties:

    - deleted:
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
            bool
        ] = None
    ) -> None:
        self.deleted = deleted
        super().__init__(_data)


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
sob.meta.object_writable(  # type: ignore
    CheckPostResponseLanguage
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
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
sob.meta.object_writable(  # type: ignore
    CheckPostResponseLanguageDetectedLanguage
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
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
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'replacements',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemreplacements,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'context',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemcontext,
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'sentence',
        sob.properties.Property(
            required=True,
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
                CheckPostResponseMatchesItemrule
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemcontext
).properties = sob.meta.Properties([
    (
        'text',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'offset',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'length',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    )
])
sob.meta.array_writable(  # type: ignore
    CheckPostResponseMatchesItemreplacements
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItemreplacementsItem
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemreplacementsItem
).properties = sob.meta.Properties([
    ('value', sob.properties.String())
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemrule
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.Property(
            name="id",
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
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
                sob.properties.String(),
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'urls',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                CheckPostResponseMatchesItemruleUrls
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
                CheckPostResponseMatchesItemruleCategory,
                sob.utilities.types.Null
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemruleCategory
).properties = sob.meta.Properties([
    (
        'id_',
        sob.properties.String(
            name="id"
        )
    ),
    ('name', sob.properties.String())
])
sob.meta.array_writable(  # type: ignore
    CheckPostResponseMatchesItemruleUrls
).item_types = sob.types.MutableTypes([
    CheckPostResponseMatchesItemruleUrlsItem
])
sob.meta.object_writable(  # type: ignore
    CheckPostResponseMatchesItemruleUrlsItem
).properties = sob.meta.Properties([
    ('value', sob.properties.String())
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
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'version',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
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
                sob.properties.String(),
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
                sob.properties.Integer(),
                sob.utilities.types.Null
            ])
        )
    ),
    ('status', sob.properties.String()),
    ('premium', sob.properties.Boolean())
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
                sob.utilities.types.Null
            ])
        )
    ),
    (
        'code',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                sob.properties.String(),
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
                sob.properties.String(),
                sob.utilities.types.Null
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
                WordsGetResponseWords
            ])
        )
    )
])
sob.meta.array_writable(  # type: ignore
    WordsGetResponseWords
).item_types = sob.types.MutableTypes([
    sob.properties.String()
])
sob.meta.object_writable(  # type: ignore
    WordsAddPostResponse
).properties = sob.meta.Properties([
    ('added', sob.properties.Boolean())
])
sob.meta.object_writable(  # type: ignore
    WordsDeletePostResponse
).properties = sob.meta.Properties([
    ('deleted', sob.properties.Boolean())
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
    CheckPostResponseMatchesItemcontext,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements":  # noqa
    CheckPostResponseMatchesItemreplacements,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements/items":  # noqa
    CheckPostResponseMatchesItemreplacementsItem,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule":  # noqa
    CheckPostResponseMatchesItemrule,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/category":  # noqa
    CheckPostResponseMatchesItemruleCategory,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls":  # noqa
    CheckPostResponseMatchesItemruleUrls,
    "#/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls/items":  # noqa
    CheckPostResponseMatchesItemruleUrlsItem,
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
