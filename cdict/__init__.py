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
finaldict = C.finaldict
defaultdict = C.defaultdict
iter = C.iter
list = C.list
sum = C.sum

__all__ = ['C', 'dict', 'finaldict', 'defaultdict', 'iter', 'list', 'sum']
