# cdict

This is a small library for creating lists of dictionaries combinatorially, for config/hyperparameter management.

## Installation

`pip install cdict`

## Usage

It's most easily understood by example!

```python
from cdict import C

# create very simple values
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

# "multiply" cdicts by combinatorially combining all possibilities
b1 = C.dict(b=1)
b2 = C.dict(b=2)
sweep_b = b1 + b2
assert list(sweep_a * sweep_b) == [
    dict(a=1, aa=1, b=1),
    dict(a=1, aa=1, b=2),
    dict(a=2, aa=4, b=1),
    dict(a=2, aa=4, b=2),
]

# overriding behavior
assert list(b1 * b2) == [
    dict(b=2)
]

# also some convenience ways to union
sweep_concise = C.dict(a=C.list(1, 2), b=C.list(1, 2))
assert list(sweep_concise) == [
    dict(a=1, b=1),
    dict(a=1, b=2),
    dict(a=2, b=1),
    dict(a=2, b=2),
]

# nesting as well
nested_sweep = C.dict(nested_a=sweep_a, nested_b=sweep_b)
assert list(nested_sweep) == [
    dict(nested_a=dict(a=1, aa=1), nested_b=dict(b=1)),
    dict(nested_a=dict(a=1, aa=1), nested_b=dict(b=2)),
    dict(nested_a=dict(a=2, aa=4), nested_b=dict(b=1)),
    dict(nested_a=dict(a=2, aa=4), nested_b=dict(b=2)),
]

# zipping of equal length things
nested_sweep = sweep_a | sweep_b
assert list(nested_sweep) == [
    dict(a=1, aa=1, b=1),
    dict(a=2, aa=4, b=2),
]
```

## Properties

- `*` `+` and `|` are associative
- `*` distributes over `+`
- `+`  is commutative if you don’t care about order of the resulting items
- `*` is commutative if you don’t care about order of the resulting items and never overwrite keys
- `|` is commutative if you never overwrite keys
