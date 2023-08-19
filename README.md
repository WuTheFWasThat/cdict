# cdict

This is a small library for creating lists of dictionaries combinatorially, for config/hyperparameter sweep management.

## Installation

`pip install cdict`

## Usage

### Basic features and primitives

You can think of the basic unit in `cdict` to be a list of dictionaries.  We then have two main operations:

- `+` which concatenates experiments (include list 1 and list 2)
- `*` which does an outer product/grid sweep (make a new list by merging pairs of dictionaries from list 1 and list 2)

There are a number of other more advanced features like
- nesting of `cdict`s
- transforms of `cdict`s
- customizable override behavior
- `|` which zips experiment sets of equal length

### Examples

It can be easier to understand `cdict` by example!

Though probably a more arduous read, [the codebase](./cdict/main.py) is as short as the examples below :)

```python
import pytest
from cdict import C

###############################################################################
# The basics
###############################################################################

# create very simple values
a1 = C.dict(a=1)
# cdicts always represent a list of dictionaries
assert list(a1) == [dict(a=1)]

# "add" cdicts by union-ing the set of dicts
a2 = C.dict(a=2)
assert list(a2) == [dict(a=2)]
sweep_a = a1 + a2
assert list(sweep_a) == [dict(a=1), dict(a=2)]

# equivalent way to add
sweep_a = C.sum(C.dict(a=a) for a in [1,2])
assert list(sweep_a) == [dict(a=1), dict(a=2)]

# "multiply" cdicts by combinatorially combining all possibilities
sweep_b = C.dict(b=1) + C.dict(b=2)
sweep_ab = sweep_a * sweep_b
assert list(sweep_ab) == [
    dict(a=1, b=1), dict(a=1, b=2),
    dict(a=2, b=1), dict(a=2, b=2),
]

###############################################################################
# Composing building blocks
###############################################################################

# add and multiply all you want
baseline = dict(a=0, b=0)
sweep_z = C.dict(z=1) + C.dict(z=2)
sweep_complex = (sweep_a + sweep_z) * sweep_b + baseline
assert list(sweep_complex) == [
    dict(a=1, b=1), dict(a=1, b=2),
    dict(a=2, b=1), dict(a=2, b=2),
    dict(z=1, b=1), dict(z=1, b=2),
    dict(z=2, b=1), dict(z=2, b=2),
    dict(a=0, b=0),
]

# equivalent
sweep_complex_2 = sweep_a * sweep_b + sweep_z * sweep_b + baseline
assert list(sweep_complex_2) == list(sweep_complex)

###############################################################################
# Nesting, basics
###############################################################################

# You can nest cdicts, to get lists of nested dicts.
# This is useful if you have nested configuration
nested_sweep = C.dict(nested_a=sweep_a, nested_b=sweep_b)
assert list(nested_sweep) == [
    dict(nested_a=dict(a=1), nested_b=dict(b=1)),
    dict(nested_a=dict(a=1), nested_b=dict(b=2)),
    dict(nested_a=dict(a=2), nested_b=dict(b=1)),
    dict(nested_a=dict(a=2), nested_b=dict(b=2)),
]

# Multiplying nested cdicts acts as expected
nested_sweep_2 = C.dict(nested_a=sweep_a) * C.dict(nested_b=sweep_b)
assert list(nested_sweep_2) == list(nested_sweep)

###############################################################################
# Nesting convenience syntax
###############################################################################

# "nested" way to add
sweep_a = C.dict(a=C.list(1,2))
assert list(sweep_a) == [dict(a=1), dict(a=2)]

# "nested" multiply
sweep_concise = C.dict(a=C.list(1, 2), b=C.list(1, 2))
assert list(sweep_concise) == [
    dict(a=1, b=1), dict(a=1, b=2),
    dict(a=2, b=1), dict(a=2, b=2),
]

###############################################################################
# Everything can be lazy
###############################################################################

# avoid lists if needed, for memory efficiency
sweep_concise = C.dict(a=C.iter(range(1, 3)), b=C.iter(range(1, 3)))
it = iter(sweep_concise)
assert next(it) == dict(a=1, b=1)
assert next(it) == dict(a=1, b=2)
assert next(it) == dict(a=2, b=1)
assert next(it) == dict(a=2, b=2)

###############################################################################
# Everything can be transformed (mapped/filtered/etc)
###############################################################################

# and transform with map
def square_a(x):
    x['aa'] = x['a']**2
    return x

sweep_squares = sweep_ab.map(square_a)
assert list(sweep_squares) == [
    dict(a=1, aa=1, b=1),
    dict(a=1, aa=1, b=2),
    dict(a=2, aa=4, b=1),
    dict(a=2, aa=4, b=2),
]

# or filter!
sweep_squares_filtered = sweep_squares.filter(lambda d: d['aa'] != d['b'])
assert list(sweep_squares_filtered) == [
    dict(a=1, aa=1, b=2),
    dict(a=2, aa=4, b=1),
    dict(a=2, aa=4, b=2),
]

# more general transforms with apply
def add_seeds(x):
    for i in range(2):
        yield dict(**x, seed=x['a'] * 100 + x['b'] * 10 + i)

sweep_squares_filtered_seeded = sweep_squares_filtered.apply(add_seeds)
assert list(sweep_squares_filtered_seeded) == [
    dict(a=1, aa=1, b=2, seed=120),
    dict(a=1, aa=1, b=2, seed=121),
    dict(a=2, aa=4, b=1, seed=210),
    dict(a=2, aa=4, b=1, seed=211),
    dict(a=2, aa=4, b=2, seed=220),
    dict(a=2, aa=4, b=2, seed=221),
]

###############################################################################
# Zipping
###############################################################################

# zipping of equal length things
diag_sweep = sweep_a | sweep_b
assert list(diag_sweep) == [
    dict(a=1, b=1),
    dict(a=2, b=2),
]

###############################################################################
# Conflict resolution
###############################################################################

# conflicting keys errors by default
s1 = C.dict(a=1, label="a1")
s2 = C.dict(b=1, label="b1")
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

###############################################################################
# Conflict resolution and nesting
###############################################################################

# you can multiply within nesting (under the hood, because cdict items implement cdict_combine by default!)
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

# to change that behavior, use finaldict (yields normal dicts that don't implement cdict_combine)
nested_sweep_fail = (
    C.dict(nested=C.finaldict(a=C.list(1, 2))) *
    C.dict(nested=C.dict(b=C.list(1, 2)))
)
with pytest.raises(ValueError):
    list(nested_sweep_fail)

# ordering matters for declaring finality
nested_sweep_success = (
    C.dict(nested=C.dict(a=C.list(1, 2))) *
    C.dict(nested=C.finaldict(b=C.list(1, 2)))
)
assert list(nested_sweep_success) == list(nested_sweep)

# since the outer dict isn't final, separate keys is fine even with final values
nested_sweep = (
    C.dict(nested_a=C.finaldict(a=C.list(1, 2))) *
    C.dict(nested_b=C.finaldict(b=C.list(1, 2)))
)
assert list(nested_sweep) == [
    dict(nested_a=dict(a=1), nested_b=dict(b=1)),
    dict(nested_a=dict(a=1), nested_b=dict(b=2)),
    dict(nested_a=dict(a=2), nested_b=dict(b=1)),
    dict(nested_a=dict(a=2), nested_b=dict(b=2)),
]
```

### Properties

`cdict` combinators have some nice properties

- `+` is associative.
- `*` and `|` are associative if 1
- `*` is left-distributive over `+`, and right-distributive if 2
- `+`  is commutative if 2
- `|` is commutative if 1
- `*` is commutative if 1 and 2

1:  values implement `cdict_combine` satisfying the same property, at any/all conflicting keys

2:  if ignoring order of the resulting yielded items

## Tests

`pytest tests`

## Acknowledgements

This library was strongly inspired by another tiny library written by Paul Christiano and Daniel Ziegler
