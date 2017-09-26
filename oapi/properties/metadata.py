import operator
import re
from collections import Callable
from copy import copy
from itertools import chain
from numbers import Number

from decimal import Decimal


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

if __name__ == '__main__':
    v = Version('swagger<3.0')
    print(v == '2.0')