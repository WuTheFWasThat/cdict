import itertools

class cdict():
    @classmethod
    def dict(cls, **kwargs):
        return cls(items=[dict(**kwargs)])

    @classmethod
    def list(cls, *args):
        return cls(items=list(args))

    @classmethod
    def iter(cls, it):
        return cls(items=it)

    def __init__(self, items=None, cdicts=None):
        assert items is None or cdicts is None
        if items is None:
            self._type = "mul"
            for c in cdicts:
                assert isinstance(c, cdict), "Cannot multiply"
            self._cdicts = cdicts
        else:
            self._type = "add"
            self._items_unteed = items
        self.consumed = False

    def _items(self, save_stream=False):
        if isinstance(self._items_unteed, list):
            return self._items_unteed
        if save_stream:
            self._items_unteed, use = itertools.tee(self._items_unteed)
            return use
        else:
            self.consumed = True
            return self._items_unteed

    def dicts(self, save_stream=False):
        if self.consumed:
            raise ValueError(f"Already called dicts() once.  Use save_stream=True, or use a list instead of an iterator")
        if self._type == "add":
            for d in self._items(save_stream=save_stream):
                if isinstance(d, cdict):
                    yield from d.dicts(save_stream=save_stream)
                elif isinstance(d, dict):
                    # if values of dict are cdicts, need to combinatorially yield
                    ks = list(d.keys())
                    viters = []
                    for k in ks:
                        v = d[k]
                        if isinstance(v, cdict):
                            viters.append(v.dicts(save_stream=save_stream))
                        else:
                            viters.append([v])
                    for vs in itertools.product(*viters):
                        yield {k: v for k, v in zip(ks, vs)}
                else:
                    yield d
        else:
            assert self._type == "mul"
            for ds in itertools.product(*[
                c.dicts(save_stream=save_stream) for c in self._cdicts
            ]):
                yield dict(sum((list(d.items()) for d in ds), []))

    def __add__(self, other):
        return cdict(items=[self, other])

    def __mul__(self, other):
        return cdict(cdicts=[self, other])

    def __repr_helper__(self):
        if self._type == "add":
            if isinstance(self._items_unteed, list):
                return " + ".join([str(d) for d in self._items_unteed])
            else:
                return "<iterable>"
        else:
            assert self._type == "mul"
            return " * ".join([d.__repr_helper__() for d in self._cdicts])

    def __repr__(self):
        return f"cdict({self.__repr_helper__()})"
