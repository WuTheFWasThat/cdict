from __future__ import annotations
import functools
from typing import Any, Union, Iterable, Optional, Generator, Tuple, Callable
import itertools

AnyDict = dict[Any, Any]

class cdict():
    @classmethod
    def dict(cls, **kwargs: Any) -> cdict:
        return _cdict_dict(kwargs)

    @classmethod
    def finaldict(cls, **kwargs: Any) -> cdict:
        return _cdict_dict(kwargs, overridable=False)

    @classmethod
    def iter(cls, it: Any) -> cdict:
        return _cdict_sum(it)

    @classmethod
    def list(cls, *args: Any) -> cdict:
        return cls.iter(args)

    @classmethod
    def sum(cls, args: Iterable[cdict]) -> cdict:
        return sum(args, cls.list())

    def apply(self, fn: Callable[[Any], Any]) -> cdict:
        return _cdict_apply(fn, self)

    def map(self, fn: Callable[[Any], Any]) -> cdict:
        @functools.wraps(fn)
        def apply_fn(x: Any) -> Any:
            yield fn(x)
        return _cdict_apply(apply_fn, self)

    def filter(self, fn: Callable[[Any], bool]) -> cdict:
        @functools.wraps(fn)
        def apply_fn(x: Any) -> Any:
            if fn(x): yield x
        return _cdict_apply(apply_fn, self)

    def __iter__(self) -> Generator[AnyDict, None, None]:
        raise NotImplementedError("Please override this method")

    def __add__(self, other: cdict) -> cdict:
        return _cdict_sum([self, other])

    def __mul__(self, other: cdict) -> cdict:
        return _cdict_product([self, other])

    def __or__(self, other: cdict) -> cdict:
        return _cdict_or([self, other])

    def __repr_helper__(self) -> str:
        raise NotImplementedError("Please override this method")

    def __repr__(self) -> str:
        return f"cdict({self.__repr_helper__()})"

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


class _cdict_dict(cdict):
    def __init__(self, _item: AnyDict, overridable: bool = True) -> None:
        self._item = _item
        self._overridable = overridable

    def __iter__(self) -> Generator[AnyDict, None, None]:
        # combinatorially yield
        d = self._item
        ks = list(d.keys())
        for vs in itertools.product(
            *(iter(v) if isinstance(v, cdict) else [v] for k, v in d.items())
        ):
            d = {k: v for k, v in zip(ks, vs)}
            yield _cdict_combinable_dict(d) if self._overridable else d

    def __repr_helper__(self) -> str:
        return ", ".join([f"{k}={v}" for k, v in self._item.items()])


class _cdict_sum(cdict):
    def __init__(self, _items: Iterable[Any]) -> None:
        self._items = _items

    def __iter__(self) -> Generator[AnyDict, None, None]:
        for d in iter(self._items):
            if isinstance(d, cdict):
                yield from d
            else:
                # bit of a hack for the sake of nested cdict.list convenience
                yield d

    def __repr_helper__(self) -> str:
        if isinstance(self._items, list):
            return " + ".join([str(d) for d in self._items])
        else:
            return "sum(" + str(self._items) + ")"


class _cdict_apply(cdict):
    def __init__(self, fn: Callable[[Any], Any], _inner: cdict) -> None:
        self._inner = _inner
        self._fn = fn

    def __iter__(self) -> Generator[AnyDict, None, None]:
        for x in iter(self._inner):
            yield from self._fn(x)

    def __repr_helper__(self) -> str:
        return f"apply({self._fn}, {self._inner})"


class _cdict_product(cdict):
    def __init__(self, _items: list[cdict]) -> None:
        for c in _items:
            assert isinstance(c, cdict), f"Cannot multiply non-cdicts: {c}"
        self._items = _items

    def __iter__(self) -> Generator[AnyDict, None, None]:
        for ds in itertools.product(*self._items):
            yield _combine_dicts(ds)

    def __repr_helper__(self) -> str:
        return " * ".join([str(d) for d in self._items])


def _safe_zip(*iterables: Iterable[Any]) -> Generator[Tuple[Any], None, None]:
    sentinel = object()
    for tup in itertools.zip_longest(*iterables, fillvalue=sentinel):
        if sentinel in tup:
            raise ValueError("Iterables are not the same length")
        yield tup


class _cdict_or(cdict):
    def __init__(self, _items: list[cdict]) -> None:
        self._items = _items

    def __iter__(self) -> Generator[AnyDict, None, None]:
        for ds in _safe_zip(*self._items):
            yield _combine_dicts(ds)

    def __repr_helper__(self) -> str:
        return " | ".join([str(d) for d in self._items])
