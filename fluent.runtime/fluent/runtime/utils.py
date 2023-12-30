from abc import abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Union, Type, Dict

from babel.core import Locale
from fluent.syntax.ast import MessageReference, TermReference

from .errors import FluentReferenceError
from .types import FluentInt, FluentFloat, FluentDecimal, FluentDate, FluentDateTime, FluentType

TERM_SIGIL = '-'
ATTRIBUTE_SEPARATOR = '.'


class NewFluentType(FluentType):
    @abstractmethod
    def __init__(self, value: Any):
        pass

    @abstractmethod
    def __eq__(self, other: Any):
        pass

    @abstractmethod
    def format(self, locale: Locale) -> str:
        pass


class VariantsType(NewFluentType):

    def __init__(self, value: Any):
        self.value = str(value).casefold()

    def __eq__(self, other: str):
        if isinstance(other, str):
            return other == self.value
        if isinstance(other, VariantsType):
            return self.value == other.value
        return False

    def format(self, locale: Locale) -> str:
        return self.value


types_map: Dict[Any, Type[NewFluentType]] = {
    None: VariantsType,
    True: VariantsType,
    False: VariantsType,
}


def native_to_fluent(val: Any) -> Any:
    """
    Convert a python type to a Fluent Type.
    """
    if isinstance(val, bool):
        return VariantsType(val)
    if isinstance(val, int):
        return FluentInt(val)
    if isinstance(val, float):
        return FluentFloat(val)
    if isinstance(val, Decimal):
        return FluentDecimal(val)

    if isinstance(val, datetime):
        return FluentDateTime.from_date_time(val)
    if isinstance(val, date):
        return FluentDate.from_date(val)
    if val is None:
        return VariantsType(val)
    # with suppress(KeyError, TypeError):
    #     return types_map[val](val)
    # with suppress(KeyError, TypeError):
    #     return types_map[type(val)](val)
    return val


def reference_to_id(ref: Union[MessageReference, TermReference]) -> str:
    """
    Returns a string reference for a MessageReference or TermReference
    AST node.

    e.g.
       message
       message.attr
       -term
       -term.attr
    """
    start: str
    if isinstance(ref, TermReference):
        start = TERM_SIGIL + ref.id.name
    else:
        start = ref.id.name

    if ref.attribute:
        return ''.join([start, ATTRIBUTE_SEPARATOR, ref.attribute.name])
    return start


def unknown_reference_error_obj(ref_id: str) -> FluentReferenceError:
    if ATTRIBUTE_SEPARATOR in ref_id:
        return FluentReferenceError(f"Unknown attribute: {ref_id}")
    if ref_id.startswith(TERM_SIGIL):
        return FluentReferenceError(f"Unknown term: {ref_id}")
    return FluentReferenceError(f"Unknown message: {ref_id}")
