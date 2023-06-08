import time
import pytest

from cdict import C

def assert_dicts(c, expected):
    print(c)
    dicts = list(iter(c))
    assert len(dicts) == len(expected), f"Expected equal lengths, got {len(expected)} instead of {len(dicts)}"
    for i, (d1, d2) in enumerate(zip(dicts, expected)):
        assert d1 == d2, f"Mismatch at {i}, got {d1} instead of {d2}"

def assert_equivalent(c1, c2):
    print(c1, c2)
    dicts1 = list(iter(c1))
    dicts2 = list(iter(c2))
    assert len(dicts1) == len(dicts2), f"Expected equal lengths, got {len(dicts2)} instead of {len(dicts1)}"
    for i, (d1, d2) in enumerate(zip(dicts1, dicts2)):
        assert d1 == d2, f"Mismatch at {i}, got {d1} instead of {d2}"

def assert_equivalent_sets(c1, c2):
    print(c1, c2)
    dicts1 = list(iter(c1))
    dicts2 = list(iter(c2))
    assert len(dicts1) == len(dicts2), f"Expected equal lengths, got {len(dicts2)} instead of {len(dicts1)}"
    for d1 in dicts1:
        found = 0
        for d2 in dicts2:
            if d1 == d2:
                found += 1
        assert found == 1


def test_simple():
    c0 = C.dict(a=5, b=3)
    assert_dicts(c0, [dict(a=5, b=3)])

    c1 = C.dict(a=5, b=C.list(3, 30))
    assert_dicts(c1, [dict(a=5, b=3), dict(a=5, b=30)])

    c2 = C.dict(nested=c1, c=4)
    assert_dicts(c2, [dict(nested=dict(a=5, b=3), c=4), dict(nested=dict(a=5, b=30), c=4)])

    c3 = c1 + c2
    assert_dicts(c3, [
        dict(a=5, b=3),
        dict(a=5, b=30),
        dict(nested=dict(a=5, b=3), c=4),
        dict(nested=dict(a=5, b=30), c=4),
    ])

    c4 = c1 * c2
    assert_dicts(c4, [
        dict(a=5, b=3, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=3, nested=dict(a=5, b=30), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=30), c=4),
    ])

    c5 = c4 * C.dict(c=4)
    assert_dicts(c5, [
        dict(a=5, b=3, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=3, nested=dict(a=5, b=30), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=30), c=4),
    ])

    # with an iterator, can still iterate twice
    c6 = C.dict(a=C.iter(range(5, 7)), b=3)
    assert_dicts(c6, [dict(a=5, b=3), dict(a=6, b=3)])
    assert_dicts(c6, [dict(a=5, b=3), dict(a=6, b=3)])

    c6 = C.dict(a=C.iter(range(5, 7)), b=3)
    assert_dicts(c6, [dict(a=5, b=3), dict(a=6, b=3)])

    c6 = C.dict(a=C.list(5, 6), b=3)
    assert_dicts(c6, [dict(a=5, b=3), dict(a=6, b=3)])
    assert_dicts(c6, [dict(a=5, b=3), dict(a=6, b=3)])

    c7 = C.dict(a=C.dict(a1=5, a2=6) + C.dict(a1=6, a2=5)) * C.dict(b=3)
    assert_dicts(c7, [dict(a=dict(a1=5, a2=6), b=3), dict(a=dict(a1=6, a2=5), b=3)])

    c7 = c4 + c5
    assert_dicts(c7, [
        dict(a=5, b=3, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=3, nested=dict(a=5, b=30), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=30), c=4),
        dict(a=5, b=3, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=3, nested=dict(a=5, b=30), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=3), c=4),
        dict(a=5, b=30, nested=dict(a=5, b=30), c=4),
    ])

    c8 = C.dict(a=C.iter(range(2))) * C.dict(b=C.iter(range(2)))
    assert_dicts(c8, [
        dict(a=0, b=0),
        dict(a=0, b=1),
        dict(a=1, b=0),
        dict(a=1, b=1),
    ])

def test_overwriting():
    c0 = C.dict(a=5, b=3)
    c1 = C.dict(a=6, c=4)
    assert_dicts(c0 * c1, [
        dict(a=6, b=3, c=4),
    ])

def test_or():
    c0 = C.dict(a=5, b=3)
    c1 = C.dict(a=6, c=4)
    assert_dicts(c0 | c1, [
        dict(a=6, b=3, c=4),
    ])

    c0 = C.dict(a=C.list(5, 6), b=3)
    c1 = C.dict(c=C.list(4, 3))
    assert_dicts(c0 | c1, [
        dict(a=5, b=3, c=4),
        dict(a=6, b=3, c=3),
    ])

    c0 = C.dict(a=C.list(5, 6), b=3)
    c1 = C.dict(a=6, c=C.list(4, 3))
    assert_dicts(c0 | c1, [
        dict(a=6, b=3, c=4),
        dict(a=6, b=3, c=3),
    ])

    with pytest.raises(ValueError):
        c0 = C.dict(a=C.list(1, 2, 3))
        c1 = C.dict(b=C.list(1, 2))
        list(iter(c0 | c1))


def test_distributive():
    a0 = C.dict(a=C.list(1,2))
    a1 = C.dict(a=C.list(3,4))
    b = C.dict(b=C.list(1,2))
    assert_equivalent(a0 * b + a1 * b, (a0 + a1) * b)
    assert_equivalent_sets(b * a0 + b * a1, b * (a0 + a1))


def test_commutative_mult():
    a0 = C.dict(a=C.list(1,2))
    a1 = C.dict(b=C.list(3,4))
    assert_equivalent_sets(a0 * a1, a1 * a0)


if __name__ == "__main__":
    test_simple()
    test_overwriting()
    test_or()
    test_distributive()
    test_commutative_mult()
