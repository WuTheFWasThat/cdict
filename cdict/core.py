from __future__ import annotations
import functools
from typing import Any, Union, Iterable, Optional, Generator, Tuple, Callable, ItemsView, cast
import itertools


AnyDict = dict[Any, Any]


def recursive_map_dict(x: Any, f: Callable[[Any], Any]) -> Any:
    if isinstance(x, dict):
        return {k: recursive_map_dict(v, f) for k, v in x.items()}
    else:
        return f(x)


def recursive_cdict_item(x: Any) -> Any:
    return recursive_map_dict(x, lambda x: x.cdict_item() if hasattr(x, "cdict_item") else x)


class _cdict_value():
    def __init__(self, d: AnyDict, final: bool = False):
        self.d = d
        self.final = final

    def cdict_combine(self, other: _cdict_value) -> _cdict_value:
        if not isinstance(other, _cdict_value):
            raise ValueError(f"Cannot combine with {other}, must be cdict")
        if self.final:
            raise ValueError("Value already finalized")
        return _cdict_value(_combine_dicts([self.d, other.d]), final=other.final)

    def __or__(self, other: _cdict_value | AnyDict) -> _cdict_value:
        if isinstance(other, dict):
            return self.cdict_combine(_cdict_value(other))
        return self.cdict_combine(other)

    def __ror__(self, other: _cdict_value | AnyDict) -> _cdict_value:
        assert not isinstance(other, _cdict_value), f"Unexpected call to __ror__, should use __or__"
        if isinstance(other, dict):
            return _cdict_value(other) | self
        raise TypeError(f"Cannot combine with {other}, must be dict")

    def __mul__(self, other: Iterable[_cdict_value]) -> Generator[_cdict_value, None, None]:
        for x in other:
            yield self | x

    def __rmul__(self, other: Iterable[_cdict_value]) -> Generator[_cdict_value, None, None]:
        for x in other:
            yield x | self

    def __getitem__(self, k: Any) -> Any:
        return self.d[k]

    def cdict_item(self) -> AnyDict:
        return recursive_cdict_item(self.d) # type: ignore

    def items(self) -> ItemsView[Any, Any]:
        return self.d.items()


class cdict_base():
    def apply(self, fn: Callable[[Any], Any], raw: bool = False) -> cdict_base:
        return _cdict_apply(fn, self, raw=raw)

    def map(self, fn: Callable[[Any], Any], raw: bool = False) -> cdict_base:
        @functools.wraps(fn)
        def apply_fn(x: Any) -> Any:
            yield fn(x)
        return _cdict_apply(apply_fn, self, raw=raw)

    def filter(self, fn: Callable[[Any], bool], raw: bool = False) -> cdict_base:
        @functools.wraps(fn)
        def apply_fn(x: Any) -> Any:
            if fn(x): yield x
        return _cdict_apply(apply_fn, self, raw=raw)

    def __add__(self, other: cdict_base) -> cdict_base:
        return cdict_iter([self, other])

    def __mul__(self, other: cdict_base) -> cdict_base:
        if not isinstance(other, cdict_base):
            return NotImplemented
        return _cdict_product(self, other)

    def __or__(self, other: cdict_base) -> cdict_base:
        return _cdict_zip([self, other])

    def cdict_iter(self) -> Generator[_cdict_value, None, None]:
        raise NotImplementedError("Please override this method")

    def __iter__(self) -> Generator[AnyDict, None, None]:
        for x in self.cdict_iter():
            yield recursive_cdict_item(x)

    def __len__(self) -> int:
        return len(list(iter(self)))

    def __pos__(self) -> cdict_base:
        return self


def _combine_dicts(ds: Iterable[AnyDict]) -> AnyDict:
    res: AnyDict = {}
    for d in ds:
        for k, v in d.items():
            if k in res:
                if hasattr(res[k], "cdict_combine"):
                    res[k] = res[k].cdict_combine(v)
                elif hasattr(v, "cdict_rcombine"):
                    res[k] = v.cdict_rcombine(res[k])
                else:
                    raise ValueError(f"No cdict_combine method found.  Cannot combine key {k}: {res[k]} and {v}")
            else:
                res[k] = v
    return res


def _iter_values(d: Any) -> Generator[Any, None, None]:
    if hasattr(d, "cdict_iter"):
        yield from d.cdict_iter()
    else:
        yield d


class cdict_iter(cdict_base):
    def __init__(self, _items: Iterable[Any]) -> None:
        self._items = _items

    def cdict_iter(self) -> Generator[_cdict_value, None, None]:
        for d in iter(self._items):
            yield from _iter_values(d)

    def __repr__(self) -> str:
        if isinstance(self._items, (list, tuple)):
            return "clist(" + ", ".join(str(d) for d in self._items) + ")"
        else:
            return "citer(" + str(self._items) + ")"


class cdict_dict(cdict_base):
    def __init__(self, _item: AnyDict, final: bool = False) -> None:
        self._item = _item
        self._final = final

    def cdict_iter(self) -> Generator[_cdict_value, None, None]:
        # combinatorially yield
        d = self._item
        ks = list(d.keys())
        for vs in itertools.product(*(_iter_values(d[k]) for k in ks)):
            d = {k: v for k, v in zip(ks, vs)}
            yield _cdict_value(d, final=self._final)

    def __repr__(self) -> str:
        return "cdict(" + ", ".join([f"{k}={v}" for k, v in self._item.items()]) + ")"


class _cdict_apply(cdict_base):
    def __init__(self, fn: Callable[[Any], Any], _inner: cdict_base, raw: bool = False) -> None:
        self._inner = _inner
        self._fn = fn
        self.raw = raw

    def cdict_iter(self) -> Generator[_cdict_value, None, None]:
        for x in self._inner.cdict_iter():
            if self.raw:
                # this version respects finalize, gives user control over that
                # also lets user use cdict_combine on the values
                for v in self._fn(x):
                    if not isinstance(v, _cdict_value):
                        raise ValueError(f"Raw apply function must return cdict values, got {v}")
                    yield v
            else:
                # TODO preserve nesting properly?
                for v in self._fn(recursive_cdict_item(x)):
                    yield _cdict_value(v)

    def __repr__(self) -> str:
        return f"{self._inner}.apply({self._fn})"


class _cdict_product(cdict_base):
    def __init__(self, _item1: Any, _item2: Any) -> None:
        for c in [_item1, _item2]:
            if not isinstance(c, cdict_base):
                raise TypeError(f"Cannot multiply non-cdicts: {c}")
        self._item1 = _item1
        self._item2 = _item2

    def cdict_iter(self) -> Generator[_cdict_value, None, None]:
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

    def cdict_iter(self) -> Generator[_cdict_value, None, None]:
        for ds in _safe_zip(*[it.cdict_iter() for it in self._items]):
            yield _cdict_value(_combine_dicts(ds))

    def __repr__(self) -> str:
        return " | ".join([str(d) for d in self._items])
