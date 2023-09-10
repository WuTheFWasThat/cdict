from builtins import sum as builtin_sum
from typing import Any, Iterable
from .main import cdict_base, cdict_dict, cdict_iter, cdict_overridable

class C():
    @staticmethod
    def dict(**kwargs: Any) -> cdict_base:
        return cdict_dict(kwargs)

    @staticmethod
    def finaldict(**kwargs: Any) -> cdict_base:
        return cdict_dict(kwargs, final=True)

    @staticmethod
    def defaultdict(**kwargs: Any) -> cdict_base:
        return cdict_dict({k: cdict_overridable(v) for k, v in kwargs.items()})

    @staticmethod
    def iter(it: Any) -> cdict_base:
        return cdict_iter(it)

    @staticmethod
    def list(*args: Any) -> cdict_base:
        return cdict_iter(args)

    @staticmethod
    def sum(args: Iterable[cdict_base]) -> cdict_base:
        return builtin_sum(args, C.list())


dict = C.dict
cdict = C.dict
finaldict = C.finaldict
cfinaldict = C.finaldict
defaultdict = C.defaultdict
cdefaultdict = C.defaultdict
iter = C.iter
citer = C.iter
list = C.list
clist = C.list
sum = C.sum
csum = C.sum
overridable = cdict_overridable
coverridable = cdict_overridable

__all__ = [
    'C',
    'dict',
    'cdict',
    'finaldict',
    'cfinaldict',
    'defaultdict',
    'cdefaultdict',
    'iter',
    'citer',
    'list',
    'clist',
    'sum',
    'csum',
    'overridable',
    'coverridable',
]
