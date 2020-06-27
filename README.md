# cdict

This is a small library for creating lists of dictionaries combinatorially, for config/hyperparameter management.

## Installation

`pip install cdict`

## Usage

It's most easily understood by example!

```python
from cdict import C

c1 = C.dict(a=5, b=3)
assert list(c1.dicts()) == [dict(a=5, b=3)]

# nest cdicts
c2 = C.dict(nested=c1, c=4)
assert list(c2.dicts()) == [dict(nested=dict(a=5, b=3), c=4)]

# "add" cdicts by union-ing the set of dicts
c3 = c1 + c2
assert list(c3.dicts()) == [
    dict(a=5, b=3),
    dict(nested=dict(a=5, b=3), c=4)
]

# and most importantly, combinatorially multiply
c4 = c1 * c2
assert list(c4.dicts()) == [
    dict(a=5, b=3, nested=dict(a=5, b=3), c=4)
]

# also some convenience ways to union
c6 = C.dict(a=C.list(5, 6), b=3)
assert list(c6.dicts()) == [dict(a=5, b=3), dict(a=6, b=3)]

# overly complicated example
c7 = C.dict(a=C.dict(a1=5, a2=6) + C.dict(a1=6, a2=5), b=3) * C.dict(c=2)
assert list(c7.dicts()) == [dict(a=dict(a1=5, a2=6), b=3, c=2), dict(a=dict(a1=6, a2=5), b=3, c=2)]
```
