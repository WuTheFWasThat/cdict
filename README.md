# cdict

This is a small library for creating lists of dictionaries combinatorially, for config/hyperparameter sweep management.

## Installation

`pip install cdict`

## Usage

### Basic features and primitives

The basic unit in `cdict` is essentially a list of dictionaries.  We then have two main operations:

- `a + b` concatenates (includes items in list `a` and list `b`)
- `a * b` does an outer product (includes items formed by combining all pairs of items from list `a` and list `b`)

Other features include:
- nesting of `cdict`s
- customizable combining behavior, gives user control over conflict resolution
- transforms of `cdict`s
- `|` which does a zip/elementwise product of lists of equal length

### Examples

It can be easier to understand `cdict` by example!

(Though shorter than the examples below, [the codebase](./cdict/core.py) is probably a more arduous read..)

```python
import pytest
import cdict as C

###############################################################################
# The basics
###############################################################################

# create very simple values
a1 = C.dict(a=1)
# cdicts always represent a list of dictionaries
assert list(a1) == [dict(a=1)]
a2 = C.dict(a=2)
assert list(a2) == [dict(a=2)]

# "add" cdicts by union-ing the set of dicts
sweep_a = a1 + a2
assert list(sweep_a) == [dict(a=1), dict(a=2)]

# equivalent way to add
sweep_b = C.sum(C.dict(b=b) for b in [1,2])
assert list(sweep_b) == [dict(b=1), dict(b=2)]

# "multiply" cdicts by combinatorially combining all possibilities
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

# equivalent, thanks to left-distributive property
sweep_complex_2 = sweep_a * sweep_b + sweep_z * sweep_b + baseline
assert list(sweep_complex_2) == list(sweep_complex)

###############################################################################
# cdict_combine
###############################################################################

# you can actually multiply lists of anything, as long as they implement cdict_combine
class joinstr(str):
    def cdict_combine(self, other):
        return joinstr(f"{self}.{other}")

# nicer utility
joinstr = C.combiner(lambda x, y: f"{x}.{y}")

s = C.sum(joinstr(f"a{i}") for i in range(1, 3)) * C.sum(joinstr(f"b{i}") for i in range(1, 3))
assert list(s) == ["a1.b1", "a1.b2", "a2.b1", "a2.b2"]

# utilities for overridable things

s = C.sum(C.overridable(f"a{i}") for i in range(1, 3)) * C.sum(f"b{i}" for i in range(1, 3))
assert list(s) == ["b1", "b2", "b1", "b2"]

# dict with entirely overridable things
defaults = C.defaultdict(a=1, b=1)
a2 = C.dict(a=2)
assert list(defaults * a2) == [dict(a=2, b=1)]
assert list(defaults * defaults * a2) == [dict(a=2, b=1)]

with pytest.raises(ValueError):
    # defaults don't override
    list(a2 * defaults)

with pytest.raises(ValueError):
    # can't override twice
    list(defaults * a2 * a2)

###############################################################################
# Conflicting dict keys
###############################################################################

# conflicting keys errors by default
s1 = C.sum(C.dict(a=a, uid=f"a{a}") for a in [1, 2])
s2 = C.sum(C.dict(b=b, uid=f"b{b}") for b in [1, 2])
with pytest.raises(ValueError):
    list(s1 * s2)

# implementing a cdict_combine lets you override that behavior!
s1 = C.sum(C.dict(a=a, uid=joinstr(f"a{a}")) for a in [1, 2])
s2 = C.sum(C.dict(b=b, uid=joinstr(f"b{b}")) for b in [1, 2])
assert list(s1 * s2) == [
    dict(a=1, b=1, uid="a1.b1"),
    dict(a=1, b=2, uid="a1.b2"),
    dict(a=2, b=1, uid="a2.b1"),
    dict(a=2, b=2, uid="a2.b2"),
]

###############################################################################
# Nesting, basics
###############################################################################

# You can nest cdicts, to get lists of nested dicts.
# This is useful if you have nested configuration
sweep_nested = C.dict(nested_a=sweep_a, nested_b=sweep_b)
assert list(sweep_nested) == [
    dict(nested_a=dict(a=1), nested_b=dict(b=1)),
    dict(nested_a=dict(a=1), nested_b=dict(b=2)),
    dict(nested_a=dict(a=2), nested_b=dict(b=1)),
    dict(nested_a=dict(a=2), nested_b=dict(b=2)),
]

# Multiplying nested cdicts acts as expected
sweep_nested_2 = C.dict(nested_a=sweep_a) * C.dict(nested_b=sweep_b)
assert list(sweep_nested_2) == list(sweep_nested)

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
# Nesting and conflicts
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

# also fails with objects that don't implement cdict_combine 
nested_sweep_fail_2 = C.dict(nested=C.dict(a=1)) * C.dict(nested=C.dict(a=2))
with pytest.raises(ValueError):
    list(nested_sweep_fail_2)

# since the outer dict isn't final, separate keys is fine even with final values
nested_sweep_nonconflict = (
    C.dict(nested_a=C.finaldict(a=C.list(1, 2))) *
    C.dict(nested_b=C.finaldict(b=C.list(1, 2)))
)
assert list(nested_sweep_nonconflict) == list(sweep_nested)

###############################################################################
# Everything can be lazy
###############################################################################

# avoid lists if needed, for memory efficiency
sweep_lazy = C.dict(a=C.iter(range(1, 3)), b=C.iter(range(1, 3)))
it = iter(sweep_lazy)
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
        yield dict(aab=x['aa'] * x['b'], seed=x['a'] * 100 + x['b'] * 10 + i)

sweep_squares_filtered_seeded = sweep_squares_filtered.apply(add_seeds)
assert list(sweep_squares_filtered_seeded) == [
    dict(aab=2, seed=120), dict(aab=2, seed=121),
    dict(aab=4, seed=210), dict(aab=4, seed=211),
    dict(aab=8, seed=220), dict(aab=8, seed=221),
]

###############################################################################
# Zipping
###############################################################################

# zipping of equal length things
diag_sweep = sweep_a | sweep_b
assert list(diag_sweep) == [
    dict(a=1, b=1), dict(a=2, b=2),
]

```

### Properties

`cdict` combinators have some nice properties:

- `+` is associative
- `*` is associative if 1
- `+` is commutative if 2
- `*` is commutative if 1 and 2
- `*` is left-distributive over `+`, and right-distributive if 2
- `|` is associative if 1
- `|` is commutative if 1
- `(a + b) | (c + d) = (a | c) + (b | d)` if `len(a) == len(c)`
- `(a * b) | (c * d) = (a | c) * (b | d)` if `len(a) == len(c)` and `len(b) == len(d)` and `cdict_combine` is associative and commutative 

Where
1. *if values implement `cdict_combine` satisfying the same property, at any/all conflicting keys*
2. *if ignoring order of the resulting yielded items*

We get essentially every property one would expect given the `+` and `*` syntax.  In fact, they form a commutative semiring with `0 = C.list()` and `1 = C.dict()`!

## Tests

`pytest tests`

## Acknowledgements

This library was strongly inspired by another tiny library written by Paul Christiano and Daniel Ziegler
