from collections import Mapping, Sequence, OrderedDict
from itertools import chain
from numbers import Real

from openswallow.model import JSONObject, get_properties, dump

NoneType = type(None)


class Property(object):

    types = None   # type: typing.Sequence[Union[type, Property]]
    json_types = ('array', 'object', 'integer', 'number', 'string', 'boolean')  # type: typing.Sequence[str]
    formats = None  # type: Optional[typing.Sequence[str]]

    def __init__(
        self,
        key=None,  # type: Optional[str]
        load=None,  # type: Optional[typing.Callable]
        dump=None,  # type: Optional[typing.Callable]
    ):
        self.key = key
        if load is not None:
            self.load = load
        if self.dump is not None:
            self.dump = dump

    @staticmethod
    def load(data):
        # type: (typing.Any) -> typing.Any
        return data

    @staticmethod
    def dump(data):
        # type: (typing.Any) -> typing.Any
        return data


class String(Property):

    json_types = ('string',)  # type: Optional[typing.Sequence[str]]
    types = (str,)  # type: Optional[typing.Sequence[type]]
    formats = (None,)  # type: Optional[typing.Sequence[str]]

    def __init__(
        self,
        key=None,  # type: Optional[str]
    ):
        super().__init__(
            types=(str,),
            key=key
        )


class Number(Property):

    types = (Real,)  # type: typing.Sequence[Union[type, Property]]
    json_types = ('number',)  # type: typing.Sequence[str]

    def __init__(
        self,
        key=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        super().__init__(key=key)

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return data

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return data


class Integer(Property):

    types = (int,)  # type: typing.Sequence[Union[type, Property]]
    json_types = ('integer',)  # type: Optional[typing.Sequence[str]]

    def __init__(
        self,
        key=None,  # type: Optional[str]
    ):
        super().__init__(
            key=key,
            cast=Number
        )

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return int(data)

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return int(data)


class Array(Property):

    types = (Sequence,)  # type: typing.Sequence[Union[type, Property]]
    json_types = ('array',)  # type: typing.Sequence[str]
    item_types = None  # type: Optional[typing.Sequence[Union[type, Property]]]

    def __init__(
        self,
        key=None,  # type: Optional[str]
        item_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
    ):
        super().__init__(key=key)
        if self.item_types is not None:
            self.item_types = item_types


def polymorph(data, types):
    # type: (Any, typing.Sequence[Union[type, Property]]) -> type
    closest_match = None
    data_keys = None
    for t in types:
        if (closest_match is None) and isinstance(t, Property) and isinstance(data, t.types):
            data = t.load(data)
            break
        elif issubclass(t, JSONObject) and isinstance(data, Mapping):
            data_keys = data_keys or set(data.keys())
            type_keys = {
                (v.key or k)
                for k, v in get_properties(data).items()
            }
            if not (data_keys - type_keys):
                unused = type_keys - data_keys
                if (
                    (closest_match is None) or
                    len(unused) < len(closest_match[-1])
                ):
                    closest_match = (t, unused)
    if closest_match is not None:
        data = closest_match[0](json_data=data)
    return data


class Object(Property):

    json_types = ('object',)  # type: typing.Sequence[str]
    types = (Mapping,)  # type: typing.Sequence[type]
    value_types = None

    def __init__(
        self,
        key=None,  # type: Optional[str]
        types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        value_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
    ):
        super().__init__(key=key)
        if types is not None:
            self.types = types
        if value_types is not None:
            self.value_types = value_types

    def load(self, data):
        # type: (typing.Mapping[str, Any]) -> typing.Mapping[str, Any]
        if not self.types:
            return data
        data = polymorph(data, self.types)
        if isinstance(data, JSONObject):
            return data
        else:
            mapping = OrderedDict()
            for k, v in data.items():
                mapping[k] = polymorph(v, self.value_types)
            return mapping

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return dump(data)






