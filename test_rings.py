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


def test_call_replaces_lead_end():
    pb = rings.METHODS["Plain Bob Doubles"]
    assert pb.lead_changes("p")[-1] == (1, 2, 5)
    assert pb.lead_changes("b")[-1] == (1, 4, 5)
    assert pb.lead_changes("s")[-1] == (1, 2, 3)
    # Grandsire's calls replace the last TWO changes: 5.1 -> 3.1 or 3.123
    g = rings.METHODS["Grandsire Doubles"]
    assert g.lead_changes("p")[-2:] == [(5,), (1,)]
    assert g.lead_changes("b")[-2:] == [(3,), (1,)]
    assert g.lead_changes("s")[-2:] == [(3,), (1, 2, 3)]


def test_standard_120_of_plain_bob_doubles():
    pb = rings.METHODS["Plain Bob Doubles"]
    rows = rings.touch(pb, "pppb" * 3)
    assert rows[-1] == (1, 2, 3, 4, 5)
    assert rings.is_extent(rows)


def test_bobs_only_extents_of_plain_bob_doubles():
    # The only bobs-only extents are the four rotations of PPPB x3
    pb = rings.METHODS["Plain Bob Doubles"]
    found = rings.search_extents(pb, "pb")
    assert sorted(found) == sorted(
        ["pppbpppbpppb", "ppbpppbpppbp", "pbpppbpppbpp", "bpppbpppbppp"]
    )


def test_thompson_no_bobs_only_grandsire_extent():
    # W. H. Thompson proved (1886) that no extent of Grandsire Doubles
    # can be rung with bobs alone. Exhaustive search agrees.
    g = rings.METHODS["Grandsire Doubles"]
    assert rings.search_extents(g, "pb") == []


def test_grandsire_extent_needs_singles():
    g = rings.METHODS["Grandsire Doubles"]
    found = rings.search_extents(g, "pbs")
    assert len(found) == 10
    for calling in found:
        assert rings.is_extent(rings.touch(g, calling))
        # singles are odd permutations, so an even nonzero number is needed
        assert calling.count("s") in (2, 6)


def test_stedman_doubles_course():
    st = rings.METHODS["Stedman Doubles"]
    rows = rings.course(st)
    assert len(rows) - 1 == 60  # 10 sixes
    assert rings.is_true(rows)
    assert not rings.is_extent(rows)
    assert rings.row_str(rows[12]) == "53412"  # lead head per CompLib


def test_stedman_single_is_mid_six():
    # The single replaces a different change in each block: 345 in the
    # slow six, 145 in the quick six (bells in 4-5 make places).
    st = rings.METHODS["Stedman Doubles"]
    assert st.lead_changes("s", 0)[-1] == (3, 4, 5)
    assert st.lead_changes("s", 1)[-1] == (1, 4, 5)
    assert st.lead_changes("p", 0)[-1] == (3,)
    assert st.lead_changes("p", 1)[-1] == (1,)


def test_stedman_doubles_extents():
    # Exhaustive search: exactly 15 singles-only extents from rounds.
    # 10 use two singles 10 sixes apart (swap a pair, ring the 60
    # out-of-course rows, swap back); 5 use four singles every 5 sixes.
    st = rings.METHODS["Stedman Doubles"]
    found = rings.search_extents(st, "ps")
    assert len(found) == 15
    for calling in found:
        assert rings.is_extent(rings.touch(st, calling))
        sites = [i for i, c in enumerate(calling) if c == "s"]
        if len(sites) == 2:
            assert sites[1] - sites[0] == 10
        else:
            assert len(sites) == 4
            assert [b - a for a, b in zip(sites, sites[1:])] == [5, 5, 5]
    assert sum(c.count("s") == 2 for c in found) == 10


def test_blue_line_connectors():
    # Treble hunting out and back: \ \ \ | / / / |
    rows = rings.plain_course("x14x14,12", 4)
    art = rings.blue_line(rows[:9])
    connectors = [line.strip() for line in art.splitlines()[1::2]]
    assert connectors == ["\\", "\\", "\\", "|", "/", "/", "/", "|"]


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
