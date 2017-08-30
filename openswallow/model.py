import functools
import json
from copy import copy
from swallow.utilities import bases

SCHEMAS_OBJECTS = {}


class JSONObject(object):

    pass


class JSONDict(JSONObject):

    @property
    @functools.lru_cache()
    def __schema__(self):
        from swallow.schemas import OBJECTS_SCHEMAS
        return OBJECTS_SCHEMAS[self.__class__.__name__](strict=True)

    def __str__(self):
        return self.__schema__.dumps(self).data



class JSONList(JSONObject, list):

    def __str__(self):
        items = self[:]
        if items and isinstance(items[0], JSONDict):
            return items[0].schema.dumps(items, many=True)
        else:
            return json.dumps(items)


# Swagger ("Open API") 2.0


class SwaggerInfo(JSONDict):

    def __init__(
        self,
        version=None,  # type: Optional[str]
        title=None,  # type: Optional[str]
    ):
        self.version = version  # type: Optional[str]
        self.title = title  # type: Optional[str]


class SwaggerTag(JSONDict):

    def __init__(
        self,
        name=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
    ):
        self.name = name  # type: Optional[str]
        self.description = description  # type: Optional[str]


class SwaggerService(JSONDict):

    def __init__(
        self,
        get=None,  # type: Optional[dict]
        put=None,  # type: Optional[dict]
        post=None,  # type: Optional[dict]
        delete=None,  # type: Optional[dict]
        patch=None,  # type: Optional[dict]
    ):
        self.get = get  # type: Optional[dict]
        self.put = put  # type: Optional[dict]
        self.post = post  # type: Optional[dict]
        self.delete = delete  # type: Optional[dict]
        self.patch = patch  # type: Optional[dict]


class Swagger(JSONDict):

    def __init__(
        self,
        swagger=None,  # type: Optional[str]
        info=None,  # type: Optional[SwaggerInfo]
        host=None,  # type: Optional[str]
        base_path=None,  # type: Optional[str]
        schemes=None,  # type: Optional[Sequence[str]]
        tags=None,  # type: Optional[Dict[str, SwaggerTag]]
        paths=None,  # type: Optional[Dict[str, SwaggerService]]
    ):
        self.swagger = swagger  # type: Optional[str]
        self.info = info  # type: Optional[SwaggerInfo]
        self.host = host  # type: Optional[str]
        self.base_path = base_path  # type: Optional[Sequence[str]]
        self.schemes = schemes  # type: Optional[Sequence[str]]
        self.tags = None if tags is None else JSONList(t for t in tags)  # type: Optional[Sequence[SwaggerTag]]
        self.paths = paths  # type: Optional[Dict[str, SwaggerService]]


for k, v in copy(locals()).items():
    if isinstance(v, type) and JSONObject in bases(v):
        SCHEMAS_OBJECTS[v.__name__ + 'Schema'] = v