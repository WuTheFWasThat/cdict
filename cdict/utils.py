from typing import Any


class overridable():
    def __init__(self, x: Any):
        self.x = x

    def cdict_combine(self, other: Any) -> Any:
        return other

    def cdict_item(self) -> Any:
        return self.x
