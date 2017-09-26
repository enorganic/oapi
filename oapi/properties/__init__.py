import typing
from base64 import b64decode, b64encode
from collections import Mapping, Sequence, OrderedDict, Set, Reversible, Iterable
from copy import copy
from numbers import Real

from oapi import model
from oapi.properties import metadata


class Property(object):
    """
    This is the base class for defining a property.

    Properties

        - types ([type|Property]): One or more expected types or `Property` instances. Values are checked,
          sequentially, against each type or ``Property`` instance, and the first appropriate match is used.

        - required (bool): If ``True``—dumping the object will throw an error if this value is ``None``.

        - versions ([str]|{str:Property}): The property should be one of the following:

            - A set/tuple/list of version numbers to which this property applies.
            - A mapping of version numbers to an instance of `Property` applicable to that version.

          Version numbers prefixed by "<" indicate any version less than the one specified, so "<3.0" indicates that
          this property is available in versions prior to 3.0. The inverse is true for version numbers prefixed by ">".
          ">=" and "<=" have similar meanings, but are inclusive.

          Versioning can be applied to an object by calling ``oapi.model.set_version`` in the ``__init__`` method of
          an ``oapi.model.Object`` sub-class. For an example, see ``oapi.model.OpenAPI.__init__``.

        - name (str): The name of the property when loaded from or dumped into a JSON/YAML/XML object. Specifying a
          ``name`` facilitates mapping of PEP8 compliant property to JSON or YAML attribute names, or XML element names,
          which are either camelCased, are python keywords, or otherwise not appropriate for usage in python code.

    (XML Only)

        - attribute (bool): Should this property be interpreted as an attribute (as opposed to a child element) when
          dumped as XML.

        - prefix (str): The XML prefix.

        - name_space (str): The URI of an XML name space.

    """

    json = metadata.JSON(
        types=('array', 'object', 'integer', 'number', 'string', 'boolean'),
        formats=None
    )
    xml = metadata.XML()

    def __init__(
        self,
        types=None,  # type: typing.Sequence[Union[type, Property]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[Sequence[Union[str, Version]]]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        if isinstance(types, (type, Property)):
            types = (types,)
        else:
            types = copy(types)
        self.types = types  # type: Optional[Sequence[type]]
        self.name = name
        self.required = required
        self._versions = None  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        self.versions = versions  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        self.name_space = name_space  # type: Optional[str]
        self.prefix = prefix  # type: Optional[str]
        self.attribute = attribute  # type: Optional[str]

    @property
    def versions(self):
        # type: () -> Optional[Sequence[Version]]
        return self._versions

    @versions.setter
    def versions(
        self,
        versions  # type: Optional[Sequence[Union[str, Version]]]
    ):
        # type: (...) -> Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        if versions is not None:
            if isinstance(versions, (str, Number, metadata.Version)):
                versions = (versions,)
            if isinstance(versions, Iterable):
                versions = tuple(
                    (v if isinstance(v, metadata.Version) else metadata.Version(v))
                    for v in versions
                )
            else:
                raise TypeError(
                    '``Property.versions`` requires a sequence of version strings or ' +
                    '``oapi.properties.metadata.Version`` instances, not ' +
                    '``%s``.' % type(versions).__name__
                )
        self._versions = versions

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return data if self.types is None else polymorph(data, self.types)

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return model.dump(data)


class String(Property):
    """
    See ``oapi.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """

    json = metadata.JSON(
        types=('string',),
        formats = (None,)
    )
    xml = metadata.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=(str,),
            name=name,
            required=required,
            versions=versions,
            attribute=attribute,
            name_space=name_space,
            prefix=prefix,
        )


class Bytes(Property):
    """
    See ``oapi.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = metadata.JSON(
        types=('string',),
        formats=('byte',)
    )
    xml = metadata.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=(bytes, bytearray),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )

    def load(self, data):
        # type: (str) -> bytes
        return b64decode(data)

    def dump(self, data):
        # type: (bytes) -> str
        return b64encode(data)


class Enum(Property):
    """
    See ``oapi.model.Property`` for additional details.

    Properties:

        - types ([type|Property])

        - values ([Any]):  A list of possible values. If ``types`` are specified—typing is applied prior to validation.

        - name (str)

        - required (bool)

        - versions ([str]|{str:Property})
    """
    json = metadata.JSON()
    xml = metadata.XML()

    def __init__(
        self,
        types=None,  # type: Optional[Sequence[Union[type, Property]]]
        values=None,  # type: Optional[Union[typing.Sequence, typing.Set]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )
        self._values = None
        self.values = values  # type: Optional[typing.Sequence]

    @property
    def values(self):
        # type: () -> Optional[Tuple]
        return self._values

    @values.setter
    def values(self, values):
        # type: (Iterable) -> None
        if (values is not None) and (not isinstance(values, (Sequence, Set))):
            raise TypeError(
                '`values` must be a finite set or sequence, not `%s`.' %
                type(values).__name__
            )
        if values is not None:
            tuple(polymorph(v, self.types) for v in values)
        self._values = values

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        if self.types is not None:
            data = polymorph(data, self.types)
        if (self.values is not None) and (data not in self.values):
            raise ValueError(
                'The value provided is not a valid option:\n%s\n\n' % repr(data) +
                'Valid options include:\n%s' % (
                    ','.join(repr(t) for t in self.value_types)
                )
            )
        return data


class Number(Property):
    """
    See ``oapi.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = metadata.JSON(
        types=('number',),
        formats=None
    )
    xml = metadata.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        # type: (...) -> None
        super().__init__(
            types=(Real,),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )


class Integer(Property):
    """
    See ``oapi.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = metadata.JSON(
        types=('integer',),
        formats=None
    )
    xml = metadata.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=(int,),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return int(data)

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return int(data)


class Boolean(Property):
    """
    See ``oapi.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = metadata.JSON(
        types=('boolean',),
        formats=None
    )
    xml = metadata.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        # type: (...) -> None
        super().__init__(
            types=(bool,),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return bool(data)

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return bool(data)


class Array(Property):
    """
    See ``oapi.model.Property`` for details.

    Properties:

        - item_types (type|Property|[type|Property]): The type(s) of values/objects contained in the array. Similar to
          ``oapi.model.Property().types``, but applied to items in the array, not the array itself.

        - name (str)

        - required (bool)

        - versions ([str]|{str:Property})
    """
    json = metadata.JSON(
        types=('array',),
        formats=None
    )
    xml = metadata.XML()

    def __init__(
        self,
        item_types=None,  # type: Optional[Union[type, typing.Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
    ):
        super().__init__(
            types=(tuple, list),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=False
        )
        if isinstance(item_types, (type, Property)):
            item_types = (item_types,)
        self.item_types = item_types  # type: Optional[typing.Sequence[Union[type, Property]]]

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return [polymorph(d, self.item_types) for d in data]


def validate(data, types):
    # type: (Union[model.Object, model.Array], Seqeunce[Union[type, Property]]) -> None
    if types is not None:
          pass


def polymorph(data, types):
    # type: (Any, typing.Sequence[Union[type, Property]]) -> type
    if types is None:
        return data
    closest_match = None
    data_keys = None
    for t in types:
        if (
            closest_match is None
        ) and isinstance(
            t,
            Property
        ) and (
            (
                t.types is None
            ) or isinstance(
                data,
                tuple(tt for tt in t.types if isinstance(tt, type))
            )
        ):
            data = t.load(data)
            break
        elif isinstance(t, type) and issubclass(t, model.Object) and isinstance(data, Mapping):
            data_keys = data_keys or set(data.keys())
            type_keys = {
                (v.name or k)
                for k, v in model.get_properties(t).items()
            }
            if not (data_keys - type_keys):
                unused = type_keys - data_keys
                if (
                    (closest_match is None) or
                    len(unused) < len(closest_match[-1])
                ):
                    closest_match = (t, unused)
    if closest_match is not None:
        data = closest_match[0](data)
    return data


class Object(Property):
    """
    See ``oapi.model.Property`` for details.

    Properties:

        - value_types (type|Property|[type|Property]): The type(s) of values/objects comprising the mapped
          values. Similar to ``oapi.model.Property().types``, but applies to *values* in the dictionary object,
          not the object itself.

        - name (str)

        - required (bool)

        - versions ([str]|{str:Property})
    """
    json = metadata.JSON(
        types=('object',),
        formats=None
    )
    xml = metadata.XML()

    def __init__(
        self,
        types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        value_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=False
        )
        if value_types is not None:
            if isinstance(value_types, (type, Property)):
                value_types = (value_types,)
        self.value_types = value_types

    def load(self, data):
        # type: (typing.Mapping[str, Any]) -> typing.Mapping[str, Any]
        data = super().load(data)
        if isinstance(data, model.Object):
            return data
        else:
            if not isinstance(data, Mapping):
                raise TypeError(
                    'Data must be a mapping, not a `%s`.' % type(data).__name__
                )
            mapping = OrderedDict()
            for k, v in data.items():
                mapping[k] = polymorph(v, self.value_types)
            return mapping