from __future__ import annotations
import functools
from typing import Any, Union, Iterable, Optional, List, Generator, Tuple, Callable, Dict
import itertools

class cdict():
    @classmethod
    def dict(cls, **kwargs: Any) -> cdict:
        return _cdict_sum([dict(**kwargs)])

    @classmethod
    def list(cls, *args: Any) -> cdict:
        return cls.iter(list(args))

    @classmethod
    def iter(cls, it: Any) -> cdict:
        return _cdict_sum(it)

    def apply(self, fn: Callable[[Any], Any]) -> cdict:
        return _cdict_apply(fn, self)

    def map(self, fn: Callable[[Any], Any]) -> cdict:
        @functools.wraps(fn)
        def apply_fn(x):
            yield fn(x)
        return _cdict_apply(apply_fn, self)

    def __iter__(self):
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

class _cdict_sum(cdict):
    def __init__(self, _items: Iterable) -> None:
        self._items = _items

    def __iter__(self):
        for d in iter(self._items):
            if isinstance(d, cdict):
                yield from d
            elif isinstance(d, dict):
                # if values of dict are cdicts, need to combinatorially yield
                ks = list(d.keys())
                viters = []
                for k in ks:
                    v = d[k]
                    viters.append(iter(v) if isinstance(v, cdict) else [v])
                for vs in itertools.product(*viters):
                    yield {k: v for k, v in zip(ks, vs)}
            else:
                yield d

    def __repr_helper__(self) -> str:
        if isinstance(self._items, list):
            return " + ".join([d.__repr_helper__() if isinstance(d, cdict) else str(d) for d in self._items])
        else:
            return "sum(" + str(self._items) + ")"


class _cdict_apply(cdict):
    def __init__(self, fn: Callable[[Any], Any], _inner: cdict) -> None:
        self._inner = _inner
        self._fn = fn

    def __iter__(self):
        for x in iter(self._inner):
            yield from self._fn(x)

    def __repr_helper__(self) -> str:
        return f"apply({self._fn}, {self._inner})"


class _cdict_product(cdict):
    def __init__(self, _items: List[cdict]) -> None:
        for c in _items:
            assert isinstance(c, cdict), "Cannot multiply"
        self._items = _items

    def __iter__(self):
        for ds in itertools.product(*self._items):
            yield dict(sum((list(d.items()) for d in ds), []))

    def __repr_helper__(self) -> str:
        return " * ".join([d.__repr_helper__() for d in self._items])


def safe_zip(*iterables: Iterable) -> Generator[Tuple[Any], None, None]:
    sentinel = object()
    for tup in itertools.zip_longest(*iterables, fillvalue=sentinel):
        if sentinel in tup:
            raise ValueError("Iterables are not the same length")
        yield tup


class _cdict_or(cdict):
    def __init__(self, _items: List[cdict]) -> None:
        self._items = _items

    def __iter__(self):
        for ds in safe_zip(*self._items):
            yield dict(sum((list(d.items()) for d in ds), []))

    def __repr_helper__(self) -> str:
        return " | ".join([d.__repr_helper__() for d in self._items])
