import sob

sob.utilities.compatibility.backport()
try:
    from typing import Union, Dict, Any, Sequence, IO
except ImportError:
    Union = Dict = Any = Sequence = IO = None


class PostCheck(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1check/post/responses/200/schema
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        software=None,  # type: Optional[PostCheckSoftware]
        language=None,  # type: Optional[PostCheckLanguage]
        matches=None,  # type: Optional[Sequence[CheckMatches]]
    ):
        self.software = software
        self.language = language
        self.matches = matches
        super().__init__(_data)


class PostCheckSoftware(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/software
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        version=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        build_date=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        api_version=None,  # type: Optional[Union[int, sob.properties.types.Null]]
        status=None,  # type: Optional[str]
        premium=None,  # type: Optional[bool]
    ):
        self.name = name
        self.version = version
        self.build_date = build_date
        self.api_version = api_version
        self.status = status
        self.premium = premium
        super().__init__(_data)


class PostCheckLanguage(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/language
    
    The language used for checking the text.
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        code=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        detected_language=None,  # type: Optional[Union[PostCheckLanguageDetected, sob.properties.types.Null]]
    ):
        self.name = name
        self.code = code
        self.detected_language = detected_language
        super().__init__(_data)


class PostCheckLanguageDetected(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/language/properties/detectedLanguage
    
    The automatically detected text language (might be different from the language actually used for checking).
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        code=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        confidence=None,  # type: Optional[numbers.Number]
    ):
        self.name = name
        self.code = code
        self.confidence = confidence
        super().__init__(_data)


class CheckMatches(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        message=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        short_message=None,  # type: Optional[str]
        offset=None,  # type: Optional[Union[int, sob.properties.types.Null]]
        length=None,  # type: Optional[Union[int, sob.properties.types.Null]]
        replacements=None,  # type: Optional[Union[Sequence[CheckMatchesReplacements], sob.properties.types.Null]]
        context=None,  # type: Optional[Union[PostCheckMatchesContext, sob.properties.types.Null]]
        sentence=None,  # type: Optional[Union[str, sob.properties.types.Null]]
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
        super().__init__(_data)


class CheckMatchesReplacements(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        value=None,  # type: Optional[str]
    ):
        self.value = value
        super().__init__(_data)


class PostCheckMatchesContext(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/context
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        text=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        offset=None,  # type: Optional[Union[int, sob.properties.types.Null]]
        length=None,  # type: Optional[Union[int, sob.properties.types.Null]]
    ):
        self.text = text
        self.offset = offset
        self.length = length
        super().__init__(_data)


class PostCheckMatchesRule(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        id_=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        sub_id=None,  # type: Optional[str]
        description=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        urls=None,  # type: Optional[Sequence[CheckMatchesRuleUrls]]
        issue_type=None,  # type: Optional[str]
        category=None,  # type: Optional[Union[PostCheckMatchesRuleCategory, sob.properties.types.Null]]
    ):
        self.id_ = id_
        self.sub_id = sub_id
        self.description = description
        self.urls = urls
        self.issue_type = issue_type
        self.category = category
        super().__init__(_data)


class CheckMatchesRuleUrls(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        value=None,  # type: Optional[str]
    ):
        self.value = value
        super().__init__(_data)


class PostCheckMatchesRuleCategory(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json
    #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/category
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        id_=None,  # type: Optional[str]
        name=None,  # type: Optional[str]
    ):
        self.id_ = id_
        self.name = name
        super().__init__(_data)


class Languages(sob.model.Object):
    """
    https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1languages/get/responses/200/schema/items
    """

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
        name=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        code=None,  # type: Optional[Union[str, sob.properties.types.Null]]
        long_code=None,  # type: Optional[Union[str, sob.properties.types.Null]]
    ):
        self.name = name
        self.code = code
        self.long_code = long_code
        super().__init__(_data)


# https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1check/post/responses/200/schema
sob.meta.writable(PostCheck).properties = sob.meta.Properties([
        (
            'software',
            sob.properties.Property(
                types=sob.properties.types.Types([
                    PostCheckSoftware
                ])
            )
        ),
        (
            'language',
            sob.properties.Property(
                types=sob.properties.types.Types([
                    PostCheckLanguage
                ])
            )
        ),
        (
            'matches',
            sob.properties.Array(
                item_types=sob.properties.types.Types([
                    CheckMatches
                ])
            )
        )
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/software
sob.meta.writable(PostCheckSoftware).properties = sob.meta.Properties([
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
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/language
sob.meta.writable(PostCheckLanguage).properties = sob.meta.Properties([
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
                            PostCheckLanguageDetected
                        ])
                    ),
                    sob.properties.types.Null
                ])
            )
        )
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/language/properties/detectedLanguage
sob.meta.writable(PostCheckLanguageDetected).properties = sob.meta.Properties([
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
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items
sob.meta.writable(CheckMatches).properties = sob.meta.Properties([
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
                    sob.properties.Array(
                        item_types=sob.properties.types.Types([
                            CheckMatchesReplacements
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
                            PostCheckMatchesContext
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
                    PostCheckMatchesRule
                ])
            )
        )
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/replacements/items
sob.meta.writable(CheckMatchesReplacements).properties = sob.meta.Properties([
        ('value', sob.properties.String())
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/context
sob.meta.writable(PostCheckMatchesContext).properties = sob.meta.Properties([
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
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule
sob.meta.writable(PostCheckMatchesRule).properties = sob.meta.Properties([
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
            sob.properties.Array(
                item_types=sob.properties.types.Types([
                    CheckMatchesRuleUrls
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
                            PostCheckMatchesRuleCategory
                        ])
                    ),
                    sob.properties.types.Null
                ])
            )
        )
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/urls/items
sob.meta.writable(CheckMatchesRuleUrls).properties = sob.meta.Properties([
        ('value', sob.properties.String())
    ])

# https://languagetool.org/http-api/languagetool-swagger.json
# #/paths/~1check/post/responses/200/schema/properties/matches/items/properties/rule/properties/category
sob.meta.writable(PostCheckMatchesRuleCategory).properties = sob.meta.Properties([
        (
            'id_',
            sob.properties.String(
                name='id'
            )
        ),
        ('name', sob.properties.String())
    ])

# https://languagetool.org/http-api/languagetool-swagger.json#/paths/~1languages/get/responses/200/schema/items
sob.meta.writable(Languages).properties = sob.meta.Properties([
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
    ])
