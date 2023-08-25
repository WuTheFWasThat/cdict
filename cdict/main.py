from __future__ import annotations
import functools
from typing import Any, Union, Iterable, Optional, Generator, Tuple, Callable
import itertools
from copy import deepcopy

AnyDict = dict[Any, Any]

class cdict_base():
    @classmethod
    def dict(cls, **kwargs: Any) -> cdict_base:
        return _cdict_dict(kwargs)

    @classmethod
    def finaldict(cls, **kwargs: Any) -> cdict_base:
        return _cdict_dict(kwargs, overridable=False)

    @classmethod
    def iter(cls, it: Any) -> cdict_base:
        return _cdict_iter(it)

    @classmethod
    def list(cls, *args: Any) -> cdict_base:
        return cls.iter(args)

    @classmethod
    def sum(cls, args: Iterable[cdict_base]) -> cdict_base:
        return sum(args, cls.list())

    def apply(self, fn: Callable[[Any], Any]) -> cdict_base:
        return _cdict_apply(fn, self)

    def map(self, fn: Callable[[Any], Any]) -> cdict_base:
        @functools.wraps(fn)
        def apply_fn(x: Any) -> Any:
            yield fn(x)
        return _cdict_apply(apply_fn, self)

    def filter(self, fn: Callable[[Any], bool]) -> cdict_base:
        @functools.wraps(fn)
        def apply_fn(x: Any) -> Any:
            if fn(x): yield x
        return _cdict_apply(apply_fn, self)

    def __add__(self, other: cdict_base) -> cdict_base:
        return _cdict_iter([self, other])

    def __mul__(self, other: cdict_base) -> cdict_base:
        return _cdict_product(self, other)

    def __or__(self, other: cdict_base) -> cdict_base:
        return _cdict_zip([self, other])

    def cdict_iter(self) -> Generator[AnyDict, None, None]:
        raise NotImplementedError("Please override this method")

    def __iter__(self) -> Generator[AnyDict, None, None]:
        for x in self.cdict_iter():
            yield deepcopy(x)

    def __len__(self) -> int:
        return len(list(iter(self)))


def _combine_dicts(ds: Iterable[AnyDict]) -> AnyDict:
    res: AnyDict = {}
    for d in ds:
        for k, v in d.items():
            if k in res:
                if not hasattr(res[k], "cdict_combine"):
                    raise ValueError(f"No cdict_combine method found.  Cannot combine key {k}: {res[k]} and {v}")
                res[k] = res[k].cdict_combine(v)
            else:
                res[k] = v
    return res


class _cdict_combinable_dict(AnyDict):
    def cdict_combine(self, other: AnyDict) -> _cdict_combinable_dict:
        return _cdict_combinable_dict(_combine_dicts([self, other]))


def _iter_values(d: Any) -> Generator[Any, None, None]:
    if isinstance(d, cdict_base):
        yield from d.cdict_iter()
    else:
        yield d


class _cdict_iter(cdict_base):
    def __init__(self, _items: Iterable[Any]) -> None:
        self._items = _items

    def cdict_iter(self) -> Generator[AnyDict, None, None]:
        for d in iter(self._items):
            yield from _iter_values(d)

    def __repr__(self) -> str:
        if isinstance(self._items, (list, tuple)):
            return "clist(" + ", ".join(str(d) for d in self._items) + ")"
        else:
            return "citer(" + str(self._items) + ")"


class _cdict_dict(cdict_base):
    def __init__(self, _item: AnyDict, overridable: bool = True) -> None:
        self._item = _item
        self._overridable = overridable

    def cdict_iter(self) -> Generator[AnyDict, None, None]:
        # combinatorially yield
        d = self._item
        ks = list(d.keys())
        for vs in itertools.product(*(_iter_values(d[k]) for k in ks)):
            # NOTE: could do deecopy(v) here to avoid weird issues if user mutates
            d = {k: v for k, v in zip(ks, vs)}
            yield _cdict_combinable_dict(d) if self._overridable else d

    def __repr__(self) -> str:
        return "cdict(" + ", ".join([f"{k}={v}" for k, v in self._item.items()]) + ")"


class _cdict_apply(cdict_base):
    def __init__(self, fn: Callable[[Any], Any], _inner: cdict_base) -> None:
        self._inner = _inner
        self._fn = fn

    def cdict_iter(self) -> Generator[AnyDict, None, None]:
        for x in iter(self._inner):
            yield from self._fn(deepcopy(x))

    def __repr__(self) -> str:
        return f"{self._inner}.apply({self._fn})"


class _cdict_product(cdict_base):
    def __init__(self, _item1: Any, _item2: Any) -> None:
        for c in [_item1, _item2]:
            assert isinstance(c, cdict_base), f"Cannot multiply non-cdicts: {c}"
        self._item1 = _item1
        self._item2 = _item2

    def cdict_iter(self) -> Generator[AnyDict, None, None]:
        for (d1, d2) in itertools.product(self._item1.cdict_iter(), self._item2.cdict_iter()):
            yield d1.cdict_combine(d2)

    def __repr__(self) -> str:
        return " * ".join([str(d) for d in [self._item1, self._item2]])


def _safe_zip(*iterables: Iterable[Any]) -> Generator[Tuple[Any], None, None]:
    sentinel = object()
    for tup in itertools.zip_longest(*iterables, fillvalue=sentinel):
        if sentinel in tup:
            raise ValueError("Iterables are not the same length")
        yield tup


class _cdict_zip(cdict_base):
    def __init__(self, _items: list[cdict_base]) -> None:
        self._items = _items

    def cdict_iter(self) -> Generator[AnyDict, None, None]:
        for ds in _safe_zip(*[it.cdict_iter() for it in self._items]):
            yield _cdict_combinable_dict(_combine_dicts(ds))

    def __repr__(self) -> str:
        return " | ".join([str(d) for d in self._items])
