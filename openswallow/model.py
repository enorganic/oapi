import collections
import functools
import json
from copy import copy

from marshmallow import missing

from openswallow.utilities import bases

SCHEMAS_OBJECTS = {}

Missing = type(missing)


class JSONObject(object):

    pass


class JSONDict(JSONObject):

    @property
    @functools.lru_cache()
    def __schema__(self):
        from openswallow.schemas import OBJECTS_SCHEMAS
        c = self.__class__
        n = c.__name__
        if n in OBJECTS_SCHEMAS:
            return OBJECTS_SCHEMAS[n](strict=True, many=False)
        else:
            for b in bases(c):
                bn = b.__name__
                if bn in OBJECTS_SCHEMAS:
                    return OBJECTS_SCHEMAS[bn](strict=True, many=False)
            raise KeyError(n)

    def __iter__(self):
        for k in dir(self):
            if k[0] != '_':
                v = getattr(self, k)
                if not isinstance(v, (collections.Callable, Missing)):
                    yield k, v

    def __copy__(self):
        return self.__class__(**{
            k: copy(v) for k, v in self
        })

    def __str__(self):
        return self.__schema__.dumps(self, many=False).data


# Swagger ("Open API") 2.0


class Info(JSONDict):

    def __init__(
        self,
        version=missing,  # type: Optional[str]
        title=missing,  # type: Optional[str]
    ):
        self.version = version  # type: Optional[str]
        self.title = title  # type: Optional[str]


class Tag(JSONDict):

    def __init__(
        self,
        name=missing,  # type: Optional[str]
        description=missing,  # type: Optional[str]
    ):
        self.name = name  # type: Optional[str]
        self.description = description  # type: Optional[str]


class Service(JSONDict):

    def __init__(
        self,
        get=missing,  # type: Optional[dict]
        put=missing,  # type: Optional[dict]
        post=missing,  # type: Optional[dict]
        delete=missing,  # type: Optional[dict]
        patch=missing,  # type: Optional[dict]
    ):
        self.get = get  # type: Optional[dict]
        self.put = put  # type: Optional[dict]
        self.post = post  # type: Optional[dict]
        self.delete = delete  # type: Optional[dict]
        self.patch = patch  # type: Optional[dict]


class OpenAPI(JSONDict):

    def __init__(
        self,
        swagger=missing,  # type: Optional[str]
        open_api=missing,  # type: Optional[str]
        info=missing,  # type: Optional[Info]
        host=missing,  # type: Optional[str]
        base_path=missing,  # type: Optional[str]
        schemes=missing,  # type: Optional[Sequence[str]]
        tags=missing,  # type: Optional[Dict[str, Tag]]
        paths=missing,  # type: Optional[Dict[str, Service]]
    ):
        self.swagger = swagger  # type: Optional[str]
        self.open_api = open_api  # type: Optional[str]
        self.info = info  # type: Optional[Info]
        self.host = host  # type: Optional[str]
        self.base_path = base_path  # type: Optional[Sequence[str]]
        self.schemes = schemes  # type: Optional[Sequence[str]]
        self.tags = missing if tags is missing else tuple(t for t in tags)  # type: Optional[Sequence[Tag]]
        self.paths = paths  # type: Optional[Dict[str, Service]]


for k, v in copy(locals()).items():
    if isinstance(v, type) and JSONObject in bases(v):
        SCHEMAS_OBJECTS[v.__name__ + 'Schema'] = v