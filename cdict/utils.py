from typing import Any, Callable


class overridable():
    def __init__(self, x: Any):
        self.x = x

    def cdict_combine(self, other: Any) -> Any:
        return other

    def cdict_item(self) -> Any:
        return self.x


class combinable():
    def __init__(self, x: Any, f: Callable[[Any, Any], Any]):
        self.x = x
        self.f = f

    def cdict_combine(self, other: Any) -> Any:
        if hasattr(other, "cdict_item"):
            other = other.cdict_item()
        return combinable(self.f(self.x, other), self.f)

    def cdict_item(self) -> Any:
        return self.x


def combiner(f: Callable[[Any, Any], Any]) -> Callable[[Any], combinable]:
    return lambda x: combinable(x, f)
