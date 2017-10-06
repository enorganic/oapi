import collections
import operator
import re
import typing
from collections import Callable
from copy import copy, deepcopy
from itertools import chain
from numbers import Number
from typing import Optional

from oapi import model


UNDEFINED = object()


class _Container(object):

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Memo
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, deepcopy(v, memo=memo))
        return new_instance


class JSON(object):

    def __init__(
        self,
        types=None,  # type: Optional[Sequence[str]]
        formats=None,  # type: Optional[Sequence[str]]
    ):
        self.types = types
        self.formats = formats


class XML(object):

    def __init__(
        self,
    ):
        pass


_DOT_SYNTAX_RE = re.compile(
    r'^\d+(\.\d+)*$'
)


class Version(object):

    def __init__(
        self,
        specification=None,  # type: Optional[Sequence[str]]
        equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        not_equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
        types=None,  # type: typing.Sequence[Union[type, Property]]
    ):
        if isinstance(specification, str) and (
            (equals is None) and
            (not_equals is None) and
            (less_than is None) and
            (less_than_or_equal_to) is None and
            (greater_than is None) and
            (greater_than_or_equal_to is None)
        ):
            if '==' in specification:
                specification, equals = specification.split('==')
            elif '<=' in specification:
                specification, less_than_or_equal_to = specification.split('<=')
            elif '>=' in specification:
                specification, greater_than_or_equal_to = specification.split('>=')
            elif '<' in specification:
                specification, less_than = specification.split('<')
            elif '>' in specification:
                specification, greater_than = specification.split('>')
            elif '!=' in specification:
                specification, not_equals = specification.split('!=')
            elif '=' in specification:
                specification, equals = specification.split('=')
        self.specification = specification
        self.equals = equals
        self.not_equals = not_equals
        self.less_than = less_than
        self.less_than_or_equal_to = less_than_or_equal_to
        self.greater_than = greater_than
        self.greater_than_or_equal_to = greater_than_or_equal_to
        self.types = types

    def __eq__(self, other):
        # type: (Any) -> bool
        compare_properties_functions = (
            ('equals', operator.eq),
            ('not_equals', operator.ne),
            ('less_than', operator.lt),
            ('less_than_or_equal_to', operator.le),
            ('greater_than', operator.gt),
            ('greater_than_or_equal_to', operator.ge),
        )
        if isinstance(other, str) and _DOT_SYNTAX_RE.match(other):
            other_components = tuple(int(n) for n in other.split('.'))
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if compare_value is not None:
                    compare_values = tuple(int(n) for n in compare_value.split('.'))
                    other_values = copy(other_components)
                    ld = len(other_values) - len(compare_values)
                    if ld < 0:
                        other_values = tuple(chain(other_values, [0] * (-ld)))
                    elif ld > 0:
                        compare_values = tuple(chain(compare_values, [0] * (ld)))
                    if not compare_function(other_values, compare_values):
                        return False
                    # for i in range(len(other_values)):
                    #     if not compare_function(other_values[i], compare_values[i]):
                    #         return False
        else:
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if (compare_value is not None) and not compare_function(other, compare_value):
                    return False
        return True

    def __repr__(self):
        properties_values = []
        for p in dir(self):
            if p[0] != '_':
                v = getattr(self, p)
                if not isinstance(v, Callable):
                    properties_values.append((p, v))
        return ('\n'.join(
            ['Version('] +
            [
                '    %s=%s,' % (p, repr(v))
                for p, v in properties_values
            ] +
            [')']
        ))

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Memo
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, deepcopy(v, memo=memo))
        return new_instance



class Meta(object):

    def __init__(
        self,
        data=None,  # type: Optional[Object]
        properties=UNDEFINED,  # Optional[Union[typing.Dict[str, properties.Property], Sequence[Tuple[str, properties.Property]]]]
        url=UNDEFINED,  # type: Optional[str]
    ):
        self.data = data
        self._properties = None  # type: Optional[Properties]
        if properties is not UNDEFINED:
            self.properties = properties
        self.url = None if url is UNDEFINED else url

    @property
    def properties(self):
        if isinstance(self.data, type):
            property_definitions = self._properties
        else:
            if self._properties is None:
                property_definitions = deepcopy(
                    get_meta(type(self.data))._properties
                )
            else:
                property_definitions = self._properties
        if property_definitions is None:
            property_definitions = Properties()
        return property_definitions

    @properties.setter
    def properties(
        self,
        property_definitions  # type: Optional[Union[typing.Dict[str, properties.Property], Sequence[Tuple[str, properties.Property]]]]
    ):
        # if not isinstance(self.data, type):
        #     raise AttributeError(
        #         '`oapi.model.meta.py.Meta().properties` cannot be *set* on metadata describing *instances* of a class—' +
        #         'only on metadata describing the class itself.'
        #     )
        if isinstance(property_definitions, Properties):
            property_definitions.meta = self
        else:
            property_definitions = Properties(property_definitions, meta=self)
        self._properties = property_definitions

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Memo
        new_instance = self.__class__()
        for a in dir(self):
            if a != 'data' and a[0] != '_':
                v = getattr(self, a)
                if a != 'data':
                    v = deepcopy(v, memo=memo)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance


class Properties(collections.OrderedDict):

    def __init__(
        self,
        items=None,  # type: Optional[Union[typing.Dict[str, properties.Property], Sequence[Tuple[str, properties.Property]]]]
        meta=None  # type: Optional[Meta]Optional[
    ):
        self.meta = meta
        if items is None:
            super().__init__()
        else:
            if isinstance(items, dict):
                if isinstance(items, collections.Reversible):
                    items = sorted(
                        ((k, v) for k, v in items.items())
                    )
                else:
                    items = items.items()
            super().__init__(items)
    #         for k, v in items:
    #             super().__setitem__(k, v)
    #
    # def __setitem__(self, key, value):
    #     # type: (str, properties.Property) -> None
    #     raise NotImplementedError(
    #         'Instances of `oapi.model.meta.py.Properties` are not mutable.'
    #     )
    #
    # def __delitem__(self, key):
    #     # type: (str) -> Any
    #     raise NotImplementedError(
    #         'Instances of `oapi.model.meta.py.Properties` are not mutable.'
    #     )
    #
    # def update(
    #     self,
    #     **kwargs  # type: properties.Property
    # ):
    #     # type: (...) -> Any
    #     raise NotImplementedError(
    #         'Instances of `oapi.model.meta.py.Properties` are not mutable.'
    #     )
    #
    def __copy__(self):
        # type: () -> Properties
        return self.__class__(tuple(self.items()), meta=self.meta)

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Properties
        return self.__class__(
            tuple(
                (k, deepcopy(v, memo=memo))
                for k, v in self.items()
            ),
            meta=self.meta
        )


def set_meta(
    o,  # type: Union[type, model.Object]
    properties=(
        UNDEFINED
    ),  # type: Optional[Union[Sequence[Tuple[str, properties.Property]], typing.Mapping[str, properties.Property]]]
    url=UNDEFINED,  # type: Optional[str]
):
    if (o._meta is None) or (o._meta.data is not o):
        o._meta = Meta(o)
    meta = o._meta
    if properties is not UNDEFINED:
        meta.properties = properties
    if url is not UNDEFINED:
        meta.url = url


def get_meta(
    o  # type: Union[type, model.Object]
):
    # type: (...) -> Union[Meta, typing.Mapping, str]
    if isinstance(o, type):
        if o._meta is None:
            o._meta = Meta(data=o)
        return o._meta
    else:
        if o._meta is None:
            o._meta = deepcopy(get_meta(type(o)))
    return o._meta