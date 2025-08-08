"""
Workaround for Pylance not recognizing Python built-ins.
Import this module in files that have issues with built-in functions.
"""

# Re-export all commonly used built-ins that Pylance sometimes doesn't recognize
from builtins import (
    all, any, dict, list, tuple, set, str, int, float, bool,
    len, max, min, sum, abs, round, sorted, reversed,
    getattr, setattr, hasattr, delattr, isinstance, issubclass,
    property, staticmethod, classmethod, super,
    enumerate, zip, map, filter, range,
    print, input, open, type, callable, id, repr, hash,
    chr, ord, bin, hex, oct, divmod, pow
)

__all__ = [
    'all', 'any', 'dict', 'list', 'tuple', 'set', 'str', 'int', 'float', 'bool',
    'len', 'max', 'min', 'sum', 'abs', 'round', 'sorted', 'reversed',
    'getattr', 'setattr', 'hasattr', 'delattr', 'isinstance', 'issubclass',
    'property', 'staticmethod', 'classmethod', 'super',
    'enumerate', 'zip', 'map', 'filter', 'range',
    'print', 'input', 'open', 'type', 'callable', 'id', 'repr', 'hash',
    'chr', 'ord', 'bin', 'hex', 'oct', 'divmod', 'pow'
]
