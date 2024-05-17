from typing import Any, Callable


class overridable():
    def __init__(self, x: Any):
        self.x = x

    def cdict_combine(self, other: Any) -> Any:
        return other

    def cdict_item(self) -> Any:
        return self.x


class override():
    def __init__(self, x: Any):
        self.x = x

    def cdict_rcombine(self, other: Any) -> Any:
        return self

    def cdict_item(self) -> Any:
        return self.x


class combinable():
    def __init__(self, x: Any, f: Callable[[Any, Any], Any], multi: bool = False):
        self.x = x
        self.f = f
        self.multi = multi

    def cdict_combine(self, other: Any) -> Any:
        if hasattr(other, "cdict_item"):
            other = other.cdict_item()
        ret = self.f(self.x, other)
        return combinable(ret, self.f, multi=True) if self.multi else ret

    def cdict_item(self) -> Any:
        return self.x


def combiner(f: Callable[[Any, Any], Any], multi: bool = True) -> Callable[[Any], combinable]:
    return lambda x: combinable(x, f, multi)


class lazy():
    def __init__(self, f: Callable[[], Any]):
        self.f = f

    def cdict_item(self) -> Any:
        return self.f()
