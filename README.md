# cdict

This is a small library for creating iterators of dictionaries combinatorially, for config/hyperparameter sweep management.

## Installation

`pip install cdict`

## Usage

### Basic features and primitives

The basic unit in `cdict` is essentially a stream of dictionaries (`Iterable[dict]`).  We then have two main operations:
<ul>
    <li>

`x + y` concatenates (includes dictionaries in `x` and then dictionaries in `y`), much like list addition

<details><summary>Example</summary>

```python
import cdict as C

# setup
a1 = C.dict(a=1)
assert list(a1) == [dict(a=1)]
a2 = C.dict(a=2)
assert list(a2) == [dict(a=2)]

# "add" cdicts by union-ing the set of dicts
sweep_a = a1 + a2
assert list(sweep_a) == [dict(a=1), dict(a=2)]

# equivalent way to add
sweep_a = C.sum(C.dict(a=a) for a in [1,2])
assert list(sweep_a) == [dict(a=1), dict(a=2)]

# a convenience
sweep_a = C.dict(a=C.list(1, 2))
assert list(sweep_a) == [dict(a=1), dict(a=2)]
```

</details>
</li>

<li>

`x * y` does an outer product (includes dictionaries formed by *combining* all pairs of dictionaries from `x` and `y`)

<details><summary>Example</summary>

```python
import cdict as C

# setup
sweep_a = C.dict(a=C.list(1, 2))
assert list(sweep_a) == [dict(a=1), dict(a=2)]
sweep_b = C.dict(b=C.list(1,2))
assert list(sweep_b) == [dict(b=1), dict(b=2)]

# "multiply" cdicts by combinatorially combining all possibilities
sweep_ab = sweep_a * sweep_b
assert list(sweep_ab) == [
    dict(a=1, b=1), dict(a=1, b=2),
    dict(a=2, b=1), dict(a=2, b=2),
]

# a convenience
sweep_ab = C.dict(
    a=C.list(1, 2),
    b=C.list(1, 2),
)
assert list(sweep_ab) == [
    dict(a=1, b=1), dict(a=1, b=2),
    dict(a=2, b=1), dict(a=2, b=2),
]
```

</details>
</li>

</ul>

These two basic operations can be composed arbitrarily, and behave as you would expect!

<details><summary>Example</summary>

```python
import cdict as C

sweep_a = C.dict(a=C.list(1, 2))
assert list(sweep_a) == [dict(a=1), dict(a=2)]
sweep_b = C.dict(b=C.list(1,2))
assert list(sweep_b) == [dict(b=1), dict(b=2)]

# add and multiply all you want
baseline = C.dict(a=0, b=0)
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
```

</details>

Note that `cdict`s are lazy.

<details><summary>Example</summary>

```python
import cdict as C

# avoid lists if needed, for memory efficiency
sweep_lazy = C.dict(a=C.iter(range(1, 3)), b=C.iter(range(1, 3)))
it = iter(sweep_lazy)
assert next(it) == dict(a=1, b=1)
assert next(it) == dict(a=1, b=2)
assert next(it) == dict(a=2, b=1)
assert next(it) == dict(a=2, b=2)
```

</details>


Other features include:

<ul>
    <li>

customizable combining behavior, gives user control over conflict resolution (allowing vs disallow override)

<details><summary>Example</summary>

```python
import pytest
import cdict as C

# conflicting keys errors by default
a1 = C.dict(a=1)
a2 = C.dict(a=2)
with pytest.raises(ValueError):
    list(a1 * a2)

# you can use overridable to change this behavior
a1 = C.dict(a=C.overridable(1))
a2 = C.dict(a=2)
assert list(a1 * a2) == [dict(a=2)]

with pytest.raises(ValueError):
    # order matters - a2 isn't overridable
    list(a2 * a1)

# overridable is just one special case of combining conflicting keys
joinstr = C.combiner(lambda x, y: f"{x}.{y}")

s1 = C.sum(C.dict(a=a, uid=joinstr(f"a{a}")) for a in [1, 2])
s2 = C.sum(C.dict(b=b, uid=joinstr(f"b{b}")) for b in [1, 2])
assert list(s1 * s2) == [
    dict(a=1, b=1, uid="a1.b1"),
    dict(a=1, b=2, uid="a1.b2"),
    dict(a=2, b=1, uid="a2.b1"),
    dict(a=2, b=2, uid="a2.b2"),
]

# Under the hood, override and combiner work by cdict_combine lets you override that behavior!
# You can actually multiply lists of anything, as long as they implement cdict_combine.
# Here's a more explicit implementation of joinstr
class joinstr(str):
    def cdict_combine(self, other):
        return joinstr(f"{self}.{other}")

s = C.sum(joinstr(f"a{i}") for i in range(1, 3)) * C.sum(joinstr(f"b{i}") for i in range(1, 3))
assert list(s) == ["a1.b1", "a1.b2", "a2.b1", "a2.b2"]

# Yet another implementation that doesn't subclass string
# cdict_item lets you control what cdict iteration yields
class joinstr():
    def __init__(self, s: str):
        self.s = s
    def cdict_combine(self, other):
        return joinstr(f"{self.s}.{other.s}")
    def cdict_item(self):
        return self.s

s = C.sum(joinstr(f"a{i}") for i in range(1, 3)) * C.sum(joinstr(f"b{i}") for i in range(1, 3))
assert list(s) == ["a1.b1", "a1.b2", "a2.b1", "a2.b2"]

# C.defaultdict also provides a convenience for having everything be overridable
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
```

</details>
</li>

<li>

nesting of `cdict`s

<details><summary>Example</summary>

```python
import pytest
import cdict as C

###############################################################################
# Nesting, basics
###############################################################################

# You can nest cdicts, to get lists of nested dicts.
# This is useful if you have nested configuration
sweep_nested = C.dict(
    nested_a=C.dict(a=1) + C.dict(a=2),
    nested_b=C.dict(b=1) + C.dict(b=2),
)
assert list(sweep_nested) == [
    dict(nested_a=dict(a=1), nested_b=dict(b=1)),
    dict(nested_a=dict(a=1), nested_b=dict(b=2)),
    dict(nested_a=dict(a=2), nested_b=dict(b=1)),
    dict(nested_a=dict(a=2), nested_b=dict(b=2)),
]

# Multiplying nested cdicts acts as expected
sweep_nested_2 = C.dict(
    nested_a=C.dict(a=1) + C.dict(a=2),
) * C.dict(
    nested_b=C.dict(b=1) + C.dict(b=2),
)
assert list(sweep_nested_2) == list(sweep_nested)

###############################################################################
# Nesting convenience syntax
###############################################################################

# "nested" syntax for adding
sweep_a = C.dict(a=C.list(1,2))
assert list(sweep_a) == [dict(a=1), dict(a=2)]
sweep_b = C.dict(b=C.list(1,2))
assert list(sweep_b) == [dict(b=1), dict(b=2)]

# "nested" multiply
sweep_ab = C.dict(a=C.list(1, 2), b=C.list(1, 2))
assert list(sweep_ab) == [
    dict(a=1, b=1), dict(a=1, b=2),
    dict(a=2, b=1), dict(a=2, b=2),
]

###############################################################################
# Nesting and conflicts
###############################################################################

# you can multiply within nesting (under the hood, because cdicts' items implement cdict_combine by default!)
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

```

</details>
</li>

<li>

transforms

<details><summary>Example</summary>

```python
import cdict as C

sweep_ab = C.dict(
    a=C.list(1, 2), b=C.list(1, 2),
)

# transform with map
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
```

</details>
</li>

<li>

a "zip" operation `|` which does an elementwise product of `cdict`s of equal length


<details><summary>Example</summary>

```python
import pytest
import cdict as C

sweep_a = C.dict(a=C.list(1, 2))
assert list(sweep_a) == [dict(a=1), dict(a=2)]
sweep_b = C.dict(b=C.list(1,2))
assert list(sweep_b) == [dict(b=1), dict(b=2)]

# zipping of equal length things
diag_sweep = sweep_a | sweep_b
assert list(diag_sweep) == [
    dict(a=1, b=1), dict(a=2, b=2),
]
```

</details>
</li>

</ul>


### Properties

`cdict` combinators have some nice properties, including essentially everything you would expect given the `+` and `*` syntax.

To be precise:

- `+` is associative
- `*` is associative if 1
- `+` is commutative if 2
- `*` is commutative if 1 and 2
- `*` is left-distributive over `+`, and right-distributive if 2

Where:
1. *if values implement `cdict_combine` satisfying the same property, at any/all conflicting keys*
2. *if ignoring order of the resulting yielded items*

For math nerds: assuming these two things, they form a commutative semiring with `0 = C.list()` and `1 = C.dict()`!

We also have properties of `|`:

- `|` is associative if 1
- `|` is commutative if 1
- `(a + b) | (c + d) = (a | c) + (b | d)` if `len(a) == len(c)`
- `(a * b) | (c * d) = (a | c) * (b | d)` if `len(a) == len(c)` and `len(b) == len(d)` and `cdict_combine` is associative and commutative 

## Tests

`pytest tests`

## Acknowledgements

This library was strongly inspired by another tiny library written by Paul Christiano and Daniel Ziegler
