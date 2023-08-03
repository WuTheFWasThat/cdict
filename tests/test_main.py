import time
import pytest
import re
import os

from cdict import C
import mypy.api


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


def test_multilist():
    c = C.dict(a=C.list(1, 2), b=C.list(1, 2))
    assert_dicts(c, [
        dict(a=1, b=1),
        dict(a=1, b=2),
        dict(a=2, b=1),
        dict(a=2, b=2),
    ])

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

    with pytest.raises(ValueError):
        c5 = c4 * C.dict(c=4)
        list(c5)

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

    c8 = C.dict(a=C.iter(range(2))) * C.dict(b=C.iter(range(2)))
    assert_dicts(c8, [
        dict(a=0, b=0),
        dict(a=0, b=1),
        dict(a=1, b=0),
        dict(a=1, b=1),
    ])

def test_nested_times():
    c0 = C.dict(a=C.dict(a=C.list(1, 2)))
    assert_dicts(c0, [dict(a=dict(a=1)), dict(a=dict(a=2))])
    c1 = C.dict(a=C.dict(b=C.list(1, 2)))
    assert_dicts(c1, [dict(a=dict(b=1)), dict(a=dict(b=2))])

    assert_dicts(c0 * c1, [
        dict(a=dict(a=1, b=1)),
        dict(a=dict(a=1, b=2)),
        dict(a=dict(a=2, b=1)),
        dict(a=dict(a=2, b=2)),
    ])

    # normal dict can't get overridden
    c0 = C.dict(a=dict(a=1)) + C.dict(a=dict(a=2))
    assert_dicts(c0, [dict(a=dict(a=1)), dict(a=dict(a=2))])
    c1 = C.dict(a=C.dict(b=C.list(1, 2)))
    assert_dicts(c1, [dict(a=dict(b=1)), dict(a=dict(b=2))])
    with pytest.raises(ValueError):
        list(c0 * c1)

    # finaldict can't get overridden
    c0 = C.dict(a=C.finaldict(a=C.list(1, 2)))
    assert_dicts(c0, [dict(a=dict(a=1)), dict(a=dict(a=2))])
    c1 = C.dict(a=C.dict(b=C.list(1, 2)))
    assert_dicts(c1, [dict(a=dict(b=1)), dict(a=dict(b=2))])
    with pytest.raises(ValueError):
        list(c0 * c1)

    c0 = C.dict(a=C.dict(a=C.list(1, 2)))
    c1 = C.dict(a=C.dict(a=C.list(3, 4)))

    with pytest.raises(ValueError):
        list(c0 * c1)

    c0 = C.dict(a=C.dict(a=C.finaldict(a=1)))
    assert_dicts(c0, [dict(a=dict(a=dict(a=1)))])
    c1 = C.dict(a=C.dict(b=C.finaldict(a=1)))
    assert_dicts(c1, [dict(a=dict(b=dict(a=1)))])

    assert_dicts(c0 * c1, [
        dict(a=dict(a=dict(a=1), b=dict(a=1))),
    ])

    # finaldict can't get overridden
    c0 = C.dict(a=C.finaldict(a=C.list(1, 2)))
    assert_dicts(c0, [dict(a=dict(a=1)), dict(a=dict(a=2))])
    c1 = C.dict(b=C.finaldict(b=C.list(1, 2)))
    assert_dicts(c1, [dict(b=dict(b=1)), dict(b=dict(b=2))])
    assert_dicts(c0 * c1, [
        dict(a=dict(a=1), b=dict(b=1)),
        dict(a=dict(a=1), b=dict(b=2)),
        dict(a=dict(a=2), b=dict(b=1)),
        dict(a=dict(a=2), b=dict(b=2)),
    ])


def test_map():
    c0 = (C.dict(a=5, b=3) + C.dict(a=6, b=4)) * C.dict(seed=C.list(1, 2))
    def increment_a(d):
        d['a'] += 1
        return d
    c0 = c0.map(increment_a)
    def aplusb(d):
        d['sum'] = d['a'] + d['b']
        return d
    c0 = c0.map(aplusb)
    assert_dicts(c0, [
        dict(a=6, b=3, seed=1, sum=9),
        dict(a=6, b=3, seed=2, sum=9),
        dict(a=7, b=4, seed=1, sum=11),
        dict(a=7, b=4, seed=2, sum=11),
    ])


def test_overwriting():
    c0 = C.dict(a=5, b=3)
    c1 = C.dict(a=6, c=4)
    with pytest.raises(ValueError):
        assert_dicts(c0 * c1, [
            dict(a=6, b=3, c=4),
        ])

    class summing_number(int):
        def cdict_combine(self, other):
            return summing_number(self + other)

    c0 = C.dict(a=summing_number(5), b=summing_number(3))
    c1 = C.dict(a=summing_number(6), c=summing_number(4))
    assert_dicts(c0 * c1, [
        dict(a=11, b=3, c=4),
    ])

    assert_dicts(c0 | c1, [
        dict(a=11, b=3, c=4),
    ])

    class overriding_number(int):
        def cdict_combine(self, other):
            return overriding_number(other)

    c0 = C.dict(a=overriding_number(5), b=overriding_number(3))
    c1 = C.dict(a=overriding_number(6), c=overriding_number(4))
    c2 = C.dict(a=overriding_number(7), d=overriding_number(5))
    assert_dicts(c0 * c1 * c2, [
        dict(a=7, b=3, c=4, d=5),
    ])


def test_or():
    c0 = C.dict(a=5, b=3)
    c1 = C.dict(a=6, c=4)
    with pytest.raises(ValueError):
        assert_dicts(c0 | c1, [
            dict(a=6, b=3, c=4),
        ])

    c0 = C.dict(a=C.list(5, 6), b=3)
    c1 = C.dict(c=C.list(4, 3))
    assert_dicts(c0 | c1, [
        dict(a=5, b=3, c=4),
        dict(a=6, b=3, c=3),
    ])

    class overriding_number(int):
        def cdict_combine(self, other):
            return overriding_number(other)

    c0 = C.dict(a=C.list(overriding_number(5), overriding_number(6)), b=3)
    c1 = C.dict(a=6, c=C.list(4, 3))
    assert_dicts(c0 | c1, [
        dict(a=6, b=3, c=4),
        dict(a=6, b=3, c=3),
    ])

    with pytest.raises(ValueError):
        c0 = C.dict(a=C.list(1, 2, 3))
        c1 = C.dict(b=C.list(1, 2))
        list(c0 | c1)


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


def test_readme_code():
    readme_file = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    with open(readme_file) as f:
        text = f.read()
    m = re.search('```(.+?)```', text, flags=re.DOTALL)
    assert m
    code = m.group(1)
    assert code.startswith('python')
    code = code[6:].strip()
    exec(code, globals(), globals())


def test_types():
    files = []
    for dirpath, dirnames, filenames in os.walk(
        os.path.join(os.path.dirname(__file__), '..', 'cdict'),
    ):
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(dirpath, filename))
    stdout, stderr, _ = mypy.api.run(['--strict'] + files)
    if 'Success: no issues found' not in stdout:
        print("MyPy stdout:\n", stdout)
        print("MyPy stderr:\n", stderr)
        raise AssertionError("MyPy found type errors")


if __name__ == "__main__":
    test_multilist()
    test_simple()
    test_overwriting()
    test_map()
    test_nested_times()
    test_or()
    test_distributive()
    test_commutative_mult()
    test_readme_code()
    test_types()
