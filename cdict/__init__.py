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
        return sum(args, C.list())


cdict = C.dict
cfinaldict = C.finaldict
cdefaultdict = C.defaultdict
citer = C.iter
clist = C.list
csum = C.sum

__all__ = ['C', 'cdict', 'cfinaldict', 'cdefaultdict', 'citer', 'clist', 'csum']
