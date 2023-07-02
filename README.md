# cdict

This is a small library for creating lists of dictionaries combinatorially, for config/hyperparameter management.

## Installation

`pip install cdict`

## Usage

It's most easily understood by example!

```python
import pytest
from cdict import C

# create very simple values
# cdicts always represent a list of dictionaries
a1 = C.dict(a=1, aa=1)
a2 = C.dict(a=2, aa=4)
assert list(a1) == [dict(a=1, aa=1)]
assert list(a2) == [dict(a=2, aa=4)]

# "add" cdicts by union-ing the set of dicts
sweep_a = a1 + a2
assert list(sweep_a) == [
    dict(a=1, aa=1),
    dict(a=2, aa=4)
]
# convenience method
sweep_a = C.sum(C.dict(a=a, aa=a*a) for a in [1,2])
assert list(sweep_a) == [
    dict(a=1, aa=1),
    dict(a=2, aa=4)
]

# "multiply" cdicts by combinatorially combining all possibilities
sweep_b = C.dict(b=1) + C.dict(b=2)
sweep_ab = sweep_a * sweep_b
assert list(sweep_ab) == [
    dict(a=1, aa=1, b=1),
    dict(a=1, aa=1, b=2),
    dict(a=2, aa=4, b=1),
    dict(a=2, aa=4, b=2),
]

# you can also nest
nested_sweep = C.dict(nested_a=sweep_a, nested_b=sweep_b)
assert list(nested_sweep) == [
    dict(nested_a=dict(a=1, aa=1), nested_b=dict(b=1)),
    dict(nested_a=dict(a=1, aa=1), nested_b=dict(b=2)),
    dict(nested_a=dict(a=2, aa=4), nested_b=dict(b=1)),
    dict(nested_a=dict(a=2, aa=4), nested_b=dict(b=2)),
]

# a more convenient way to union
sweep_concise = C.dict(a=C.list(1, 2), b=C.list(1, 2))
assert list(sweep_concise) == [
    dict(a=1, b=1),
    dict(a=1, b=2),
    dict(a=2, b=1),
    dict(a=2, b=2),
]

# avoid instantiating lists if needed
sweep_concise = C.dict(a=C.iter(range(1, 3)), b=C.iter(range(1, 3)))
assert list(sweep_concise) == [
    dict(a=1, b=1),
    dict(a=1, b=2),
    dict(a=2, b=1),
    dict(a=2, b=2),
]

# and transform
def square_a(x):
    x['aa'] = x['a']**2
    return x

sweep_concise = sweep_concise.map(square_a)
assert list(sweep_concise) == [
    dict(a=1, aa=1, b=1),
    dict(a=1, aa=1, b=2),
    dict(a=2, aa=4, b=1),
    dict(a=2, aa=4, b=2),
]

def add_seeds(x):
    for i in range(2):
        yield dict(**x, seed=x['a'] * 100 + x['b'] * 10 + i)

sweep_concise = sweep_concise.apply(add_seeds)
print(list(sweep_concise))
assert list(sweep_concise) == [
    dict(a=1, aa=1, b=1, seed=110),
    dict(a=1, aa=1, b=1, seed=111),
    dict(a=1, aa=1, b=2, seed=120),
    dict(a=1, aa=1, b=2, seed=121),
    dict(a=2, aa=4, b=1, seed=210),
    dict(a=2, aa=4, b=1, seed=211),
    dict(a=2, aa=4, b=2, seed=220),
    dict(a=2, aa=4, b=2, seed=221),
]


# conflicting keys errors by default
s1 = C.sum(C.dict(a=a, label=f"a{a}") for a in [1, 2])
s2 = C.sum(C.dict(b=b, label=f"b{b}") for b in [1, 2])
with pytest.raises(ValueError):
    list(s1 * s2)

# implementing a cdict_combine lets you override that behavior
class label(str):
    def cdict_combine(self, other):
        return label(self + "." + other)

s1 = C.sum(C.dict(a=a, label=label(f"a{a}")) for a in [1, 2])
s2 = C.sum(C.dict(b=b, label=label(f"b{b}")) for b in [1, 2])
assert list(s1 * s2) == [
    dict(a=1, b=1, label="a1.b1"),
    dict(a=1, b=2, label="a1.b2"),
    dict(a=2, b=1, label="a2.b1"),
    dict(a=2, b=2, label="a2.b2"),
]

# zipping of equal length things
diag_sweep = sweep_a | sweep_b
assert list(diag_sweep) == [
    dict(a=1, aa=1, b=1),
    dict(a=2, aa=4, b=2),
]

# you can multiply within nesting (because cdict results implement cdict_combine)
nested_sweep = (
    C.dict(nested=C.dict(a=C.list(1, 2))) *
    C.dict(nested=C.dict(b=C.list(1, 2)))
)
assert list(nested_sweep) == [
    dict(nested=dict(a=1, b=1)),
    dict(nested=dict(a=1, b=2)),
    dict(nested=dict(a=2, b=1)),
    dict(nested=dict(a=2, b=2)),
]

# to change that behavior, use finaldict
nested_sweep = (
    C.dict(nested=C.finaldict(a=C.list(1, 2))) *
    C.dict(nested=C.dict(b=C.list(1, 2)))
)
with pytest.raises(ValueError):
    list(nested_sweep)
```

## Properties

- `+` is associative.
- `*` and `|` are associative\*
- `*` is left-distributive and right-distributive^ over `+`
- `+`  is commutative^
- `|` is commutative\*
- `*` is commutative\*^

\*:  if either cdict_combine has the same property or there are no conflicting keys

^:  if ignoring order of the resulting items
