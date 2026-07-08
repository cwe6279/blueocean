"""Tests for rings.py. Run: python3 test_rings.py"""

import rings


def test_tokenize():
    assert rings.tokenize("x14x14") == ["x", (1, 4), "x", (1, 4)]
    assert rings.tokenize("5.1.5.1.5") == [(5,), (1,), (5,), (1,), (5,)]
    assert rings.tokenize("-38-14") == ["x", (3, 8), "x", (1, 4)]
    assert rings.tokenize("36x7") == [(3, 6), "x", (7,)]


def test_parse_symmetric():
    # Plain Bob Minimus: 8 changes per lead
    changes = rings.parse("x14x14,12")
    assert changes == ["x", (1, 4), "x", (1, 4), "x", (1, 4), "x", (1, 2)]
    # Grandsire Doubles: 10 changes per lead
    changes = rings.parse("3,1.5.1.5.1")
    assert len(changes) == 10
    assert changes[0] == (3,)


def test_apply_change():
    assert rings.apply_change((1, 2, 3, 4), "x") == (2, 1, 4, 3)
    assert rings.apply_change((2, 1, 4, 3), (1, 4)) == (2, 4, 1, 3)
    # implicit place: on 5 bells, "1" fixes place 1, pairs 2-3 and 4-5 swap
    assert rings.apply_change((1, 2, 3, 4, 5), (1,)) == (1, 3, 2, 5, 4)
    # implicit trailing place on odd stage under a cross-like leading swap
    assert rings.apply_change((1, 2, 3, 4, 5), (5,)) == (2, 1, 4, 3, 5)


def test_plain_bob_minimus_is_the_extent():
    rows = rings.plain_course("x14x14,12", 4)
    assert rows[0] == (1, 2, 3, 4)
    assert rows[-1] == (1, 2, 3, 4)
    assert len(rows) == 25  # 24 changes + return to rounds
    assert rings.is_true(rows)
    assert rings.is_extent(rows)


def test_plain_bob_doubles_course():
    rows = rings.plain_course("5.1.5.1.5,125", 5)
    assert len(rows) - 1 == 40  # 4 leads of 10
    assert rings.is_true(rows)
    assert not rings.is_extent(rows)


def test_grandsire_doubles_course():
    rows = rings.plain_course("3,1.5.1.5.1", 5)
    assert len(rows) - 1 == 30  # 3 leads of 10
    assert rings.is_true(rows)


def test_plain_bob_minor_course():
    rows = rings.plain_course("x16x16x16,12", 6)
    assert len(rows) - 1 == 60  # 5 leads of 12
    assert rings.is_true(rows)


def test_treble_hunts_in_plain_bob():
    # In Plain Bob the treble plain-hunts: place sequence 1,2,3,4,4,3,2,1...
    rows = rings.plain_course("x14x14,12", 4)
    places = [row.index(1) + 1 for row in rows[:9]]
    assert places == [1, 2, 3, 4, 4, 3, 2, 1, 1]


def test_falseness_detected():
    # Repeating a whole extent must be false
    rows = rings.plain_course("x14x14,12", 4)
    doubled = rows[:-1] + rows
    assert not rings.is_true(doubled)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    raise SystemExit(1 if failures else 0)
