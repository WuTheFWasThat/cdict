import time
import pytest
import re
import os
import traceback
import sys

import cdict as C
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


def test_nested_fail():
    c0 = C.dict(a=C.dict(a=C.list(1, 2)))
    assert_dicts(c0, [dict(a=dict(a=1)), dict(a=dict(a=2))])
    c1 = C.dict(a=dict(b=2))
    assert_dicts(c1, [dict(a=dict(b=2))])
    with pytest.raises(ValueError):
        list(c0 * c1)


def test_defaultdict():
    s = C.sum(C.overridable(f"a{i}") for i in range(1, 3)) * C.sum(f"b{i}" for i in range(1, 3))
    assert list(s) == ["b1", "b2", "b1", "b2"]

    c0 = C.dict(a=C.defaultdict(a=1, b=1))
    assert_dicts(c0, [dict(a=dict(a=1, b=1))])

    with pytest.raises(ValueError):
        list(c0 * C.dict(a=2))

    c1 = c0 * C.dict(a=C.dict(a=2))
    assert_dicts(c1, [dict(a=dict(a=2, b=1))])

    c2 = c1 * C.dict(a=C.dict(a=3))
    with pytest.raises(ValueError):
        list(c2)

    c3 = c1 * C.dict(a=C.dict(b=2))
    assert_dicts(c3, [dict(a=dict(a=2, b=2))])

def test_map():
    cbase = C.dict(a=5, b=3) + C.dict(a=6, b=4)
    seeds = C.dict(seed=C.list(1, 2))

    def increment_a(d):
        d['a'] += 1
        return d

    def aplusb(d):
        d['sum'] = d['a'] + d['b']
        return d

    c0 = (cbase * seeds).map(increment_a).map(aplusb)
    assert_dicts(c0, [
        dict(a=6, b=3, seed=1, sum=9),
        dict(a=6, b=3, seed=2, sum=9),
        dict(a=7, b=4, seed=1, sum=11),
        dict(a=7, b=4, seed=2, sum=11),
    ])
    c1 = (cbase.map(increment_a).map(aplusb)) * seeds
    assert_equivalent(c0, c1)


def test_mut():
    mut = C.dict(
            inner=C.dict(a=1)
    ) * (
        C.dict() + C.dict(inner=C.dict(b=1))
    )

    for x, inner in zip(mut, [dict(a=1), dict(a=1, b=1)]):
        assert x['inner'] == inner

    # mutating is fine
    for x, inner in zip(mut, [dict(a=1), dict(a=1, b=1)]):
        assert x['inner'] == inner
        if 'a' in x['inner']:
            x['inner'].pop('a')


def test_list_of_dicts():
    clist = C.dict(
        a=C.list(
            C.dict(a=1, b=2),
            C.dict(a=2, b=1),
        ),
        b=3,
    )
    assert_dicts(clist, [
        dict(a=dict(a=1, b=2), b=3),
        dict(a=dict(a=2, b=1), b=3),
    ])

    clist = C.dict(
        a=C.list(
            C.dict(a=1, b=2),
            C.dict(a=2, b=1),
        ),
        b=3,
    ) * C.dict(
        a=C.list(
            C.dict(c=3, d=4),
            C.dict(c=4, d=3),
        )
    )
    assert_dicts(clist, [
        dict(
            a=dict(a=1, b=2, c=3, d=4),
            b=3,
        ),
        dict(
            a=dict(a=1, b=2, c=4, d=3),
            b=3,
        ),
        dict(
            a=dict(a=2, b=1, c=3, d=4),
            b=3,
        ),
        dict(
            a=dict(a=2, b=1, c=4, d=3),
            b=3,
        ),
    ])


def test_dotkeys():
    cd = C.dict(
        **{
            'a.b': 1,
            'a.c': 2,
        }
    )
    assert_dicts(cd, [
        {'a.b': 1, 'a.c': 2},
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



def test_semiring_properties():
    a = C.dict(a=C.list(1,2))
    b = C.dict(b=C.list(3,4))
    c = C.dict(c=C.list(5,6))
    zero = C.list()
    one = C.dict()

    assert_equivalent((a + b) + c, a + (b + c))
    assert_equivalent(a + zero, a)
    assert_equivalent(zero + a, a)
    assert_equivalent_sets(a + b, b + a)

    assert_equivalent((a * b) * c, a * (b * c))
    assert_equivalent(a * one, a)
    assert_equivalent(one * a, a)
    assert_equivalent_sets(a * b, b * a)  # commutative semiring!

    assert_equivalent(a * zero, zero)
    assert_equivalent(zero * a, zero)
    assert_equivalent(b * a + c * a, (b + c) * a)
    assert_equivalent_sets(a * b + a * c, a * (b + c))


def test_or_distribution_property():
    a = C.dict(a=C.list(1,2))
    b = C.dict(b=C.list(3,4))
    c = C.dict(c=C.list(5,6))
    d = C.dict(d=C.list(7,8))
    assert_equivalent(
        (a + b) | (c + d),
        (a | c) + (b | d)
    )
    assert_equivalent(
        (a * b) | (c * d),
        (a | c) * (b | d)
    )



def test_combiners():
    class joinstr1(str):
        def cdict_combine(self, other):
            return joinstr1(self + "." + other)

    s = C.sum(joinstr1(f"a{i}") for i in range(1, 3)) * C.sum(joinstr1(f"b{i}") for i in range(1, 3))
    assert list(s) == ["a1.b1", "a1.b2", "a2.b1", "a2.b2"]

    joinstr2 = C.combiner(lambda a, b: a + "." + b)
    s = C.sum(joinstr2(f"a{i}") for i in range(1, 3)) * C.sum(joinstr2(f"b{i}") for i in range(1, 3))
    assert list(s) == ["a1.b1", "a1.b2", "a2.b1", "a2.b2"]

    joinstr2 = C.combiner(lambda a, b: a + "." + b)
    s = C.sum(joinstr2(f"a{i}") for i in range(1, 3)) * C.sum(f"b{i}" for i in range(1, 3)) * C.item(f"c0")
    assert list(s) == ["a1.b1.c0", "a1.b2.c0", "a2.b1.c0", "a2.b2.c0"]


def test_readme_code():
    readme_file = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    with open(readme_file) as f:
        text = f.read()
    m = re.search('```(.+?)```', text, flags=re.DOTALL)
    assert m
    code = m.group(1)
    assert code.startswith('python')
    code = code[6:].strip()
    try:
        exec(code, globals(), globals())
    except Exception as err:
        error_class = err.__class__.__name__
        detail = err.args[0] if len(err.args) else ""
        cl, exc, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1][1]
        raise Exception(f'Error in README.md line {line_number}: {error_class} {detail}')


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
    test_list_of_dicts()
    test_dotkeys()
    test_overwriting()
    test_defaultdict()
    test_map()
    test_mut()
    test_nested_times()
    test_nested_fail()
    test_or()
    test_semiring_properties()
    test_or_distribution_property()
    test_combiners()
    test_readme_code()
    test_types()
