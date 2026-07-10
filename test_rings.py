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


def test_grandsire_triples_course():
    # Where Thompson's theorem actually lives: bobs-only Grandsire
    # Triples reaches all 5040 rows (see the reachability census), so
    # its impossibility is deep. The Doubles case is a shallow
    # reachability fact by comparison.
    g = rings.METHODS["Grandsire Triples"]
    rows = rings.course(g)
    assert len(rows) - 1 == 70  # 5 leads of 14
    assert rings.is_true(rows)
    # double-hunt method: both the treble and the 2nd are home at each
    # lead head
    assert rings.row_str(rows[14])[:2] == "12"


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
    # No extent of Grandsire Doubles can be rung with bobs alone.
    # Exhaustive search agrees — though at Doubles this is shallow:
    # bobs only ever reach 60 of the 120 rows (see the census below).
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


def test_plain_bob_leadheads_form_cyclic_group():
    # The lead heads of a Plain Bob plain course are the powers of the
    # first lead head: a cyclic group (order 5 on six bells).
    rows = rings.course(rings.METHODS["Plain Bob Minor"])
    heads = [rows[i] for i in range(0, len(rows), 12)]
    g = heads[1]
    h = rings.rounds(6)
    powers = []
    for _ in range(5):
        powers.append(h)
        h = tuple(g[x - 1] for x in h)
    assert h == rings.rounds(6)  # g has order 5
    assert heads == powers + [rings.rounds(6)]


def test_plain_bob_minimus_unique_extent():
    # On four bells the plain course is already the extent, and no other
    # calling gives one: calls cannot help at Minimus.
    pb = rings.METHODS["Plain Bob Minimus"]
    assert rings.search_extents(pb, "pbs") == ["ppp"]


def test_no_bobs_only_extent_of_plain_bob_minor():
    # A 720 of Plain Bob Minor cannot be rung with bobs alone,
    # confirmed by exhaustive search. The reason is reachability, not
    # anything subtle: see test_bobs_only_ceilings_are_attained.
    pb = rings.METHODS["Plain Bob Minor"]
    assert rings.search_extents(pb, "pb") == []


def test_reachable_rows_census():
    # How much of the extent can each call set ever touch? The union of
    # all reachable leads bounds every true touch. Heads x rows:
    def census(name, calls):
        heads, rows = rings.reachable_rows(rings.METHODS[name], calls)
        return len(heads), len(rows)

    assert census("Plain Bob Minimus", "pb") == (3, 24)
    assert census("Plain Bob Doubles", "pb") == (24, 120)
    assert census("Plain Bob Minor", "pb") == (60, 360)  # half!
    assert census("Plain Bob Minor", "pbs") == (120, 720)
    assert census("Grandsire Doubles", "pb") == (12, 60)  # half!
    assert census("Grandsire Doubles", "pbs") == (24, 120)
    assert census("Cambridge Surprise Minor", "pb") == (60, 720)
    assert census("Stedman Doubles", "p") == (10, 60)
    assert census("Stedman Doubles", "ps") == (120, 120)
    # Thompson's 1886 theorem is the deep one: Grandsire Triples
    # bobs-only reaches ALL 5040 rows, yet no extent exists.
    assert census("Grandsire Triples", "pb") == (360, 5040)


def test_bobs_only_ceilings_are_attained():
    # Plain Bob Minor bobs-only reaches only 360 rows — THAT is why no
    # bobs-only 720 exists — and the bound is sharp: a true 360 exists
    # covering every reachable row (a three-part, ppppbpppbb x3).
    pb = rings.METHODS["Plain Bob Minor"]
    found = rings.search_extents(pb, "pb", limit=1, target=360)
    assert found == ["ppppbpppbb" * 3]
    rows = rings.touch(pb, found[0])
    assert rings.is_true(rows)
    assert set(rows[:-1]) == rings.reachable_rows(pb, "pb")[1]
    # Grandsire Doubles likewise: 60 reachable, attained by pbpbpb.
    g = rings.METHODS["Grandsire Doubles"]
    found = rings.search_extents(g, "pb", limit=1, target=60)
    assert found == ["pbpbpb"]
    rows = rings.touch(g, found[0])
    assert rings.is_true(rows)
    assert set(rows[:-1]) == rings.reachable_rows(g, "pb")[1]


def test_plain_bob_minor_extent_needs_singles():
    pb = rings.METHODS["Plain Bob Minor"]
    found = rings.search_extents(pb, "pbs", limit=1)
    assert len(found) == 1
    calling = found[0]
    assert len(calling) == 60  # 60 leads of 12
    assert rings.is_extent(rings.touch(pb, calling))
    assert calling.count("s") % 2 == 0  # singles are odd permutations


def test_extents_up_to_rotation():
    # A rotation of a calling is the same cyclic composition started at a
    # different lead. Up to rotation each family collapses to almost
    # nothing: PB Doubles has ONE bobs-only extent, Grandsire and Stedman
    # Doubles two each. (Cambridge's 400 form 16 classes, 4 three-parts.)
    classes = rings.rotation_classes(
        rings.search_extents(rings.METHODS["Plain Bob Doubles"], "pb")
    )
    assert list(classes) == ["bpppbpppbppp"]
    classes = rings.rotation_classes(
        rings.search_extents(rings.METHODS["Grandsire Doubles"], "pbs")
    )
    assert sorted(classes) == ["bpbpspbpbpsp", "bspsbspsbsps"]
    classes = rings.rotation_classes(
        rings.search_extents(rings.METHODS["Stedman Doubles"], "ps")
    )
    assert sorted(classes) == [
        "pppppppppsppppppppps",
        "ppppsppppsppppspppps",
    ]


def test_cambridge_surprise_minor_course():
    cam = rings.METHODS["Cambridge Surprise Minor"]
    rows = rings.course(cam)
    assert len(rows) - 1 == 120  # 5 leads of 24
    assert rings.is_true(rows)
    assert rings.row_str(rows[24]) == "156342"  # lead head per CompLib
    # the treble dodges: 1-2 up, 3-4 up, 5-6 up, 5-6 down, 3-4 down, 1-2 down
    path = [row.index(1) + 1 for row in rows[:25]]
    assert path == [1, 2, 1, 2, 3, 4, 3, 4, 5, 6, 5, 6,
                    6, 5, 6, 5, 4, 3, 4, 3, 2, 1, 2, 1, 1]


def test_cambridge_has_bobs_only_extents():
    # Unlike Plain Bob Minor, Cambridge admits bobs-only 720s (the full
    # search finds exactly 400 in ~50s; here we just take the first,
    # which is a tidy three-part).
    cam = rings.METHODS["Cambridge Surprise Minor"]
    found = rings.search_extents(cam, "pb", limit=1)
    assert found == ["ppppbppbpb" * 3]
    assert rings.is_extent(rings.touch(cam, found[0]))


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


def test_svg_diagram():
    st = rings.METHODS["Stedman Doubles"]
    rows = rings.course(st)
    svg = rings.to_svg(rows, tracks=(1, 2), per_column=12)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    # 5 columns x 2 tracked bells = 10 polylines, 13 points each
    lines = [l for l in svg.splitlines() if l.startswith("<polyline")]
    assert len(lines) == 10
    assert all(l.count(",") == 13 for l in lines)
    assert '"#c02020"' in svg and '"#2050c0"' in svg  # red treble, blue line


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
