"""Tests for rings.py. Run: python3 test_rings.py

Set RINGS_SLOW=1 to include the ~1 minute exhaustive census tests."""

import os

import rings

# The celebrated longest bobs-only touch of Grandsire Triples (357
# leads) and one of the two 4984s (356 leads); shared by several tests.
TOUCH_4998 = (
    "pbppbbppppbbpbbppbbpbbppbbpbbppbbpbppppbpppbbppbbppppbbppbp"
    "bbppppbpbbpbbppppbbpbbppbbpbpppbpppbbpbbpbbpppbppbpbbpbpbpp"
    "ppbpbbpppbpppbbppbbppbppbbpbbpbbppbbpbppbpppbpbbppbppbppppb"
    "bppbbppbpbpbbppbbpbbppbbpbbpbppppbpbbpppbbppbbppppbpbpbppbp"
    "pbpbpbbpppbppppbbpbbppbppbpbpbbpbbpbbppbbpbbpbpbbppbbpbbppb"
    "ppbppbpbbpbbppbppbbppbbpppbbpppbpbbppppbbpppbbpbpbbppppbpbb"
    "ppb"
)
TOUCH_4984_A = (
    "pppbpbppbppppbpbbppppbppppbppppbppbbppppbbpbbppppbppbppbpbb"
    "ppppbppppbbppppbbppbbpppbpbbppppbbpbpppbppppbbpbppbpbppbbpb"
    "pbppppbbppbppbpbpbppbppppbppppbbpbppbbppppbpbppppbbppbppppb"
    "bpppbppppbpbppbbppppbbpbbppbbpbbppbbpbpbpbbppppbpbbppbpbppb"
    "ppppbpbpbppbbpbppppbbpbpbpbbpbppbpppbbppppbbpppbppppbpppbpp"
    "bbppbppppbppppbpppbppbppppbbpbbppbbpbppppbppppbbpbbppppbbpp"
    "bb"
)


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


def test_thompson_theorem_proved():
    # Thompson (1886): no extent of Grandsire Triples can be rung with
    # bobs alone. Search cannot decide this (the space is astronomical);
    # the Q-set parity certificate proves it. Bobs-only, exactly 360
    # lead heads are reachable and an extent needs exactly 360 leads,
    # so every head is used once and 'next head' is a permutation F of
    # the heads — a single 360-cycle. Truth forces calls in whole
    # Q-sets, which here have FIVE members (sigma = gp.gb^-1 is
    # conjugate to the 5-cycle pi7.pi3), so F is the plain map times
    # even permutations: its cycle-count parity is stuck at that of the
    # 72 plain courses — even, never 1. No bobs-only extent.
    cert = rings.qset_parity_certificate(rings.METHODS["Grandsire Triples"])
    assert cert == {
        "heads": 360,
        "extent_leads": 360,
        "qsets": 72,
        "qset_sizes": [5],
        "plain_cycles": 72,
        "extent_impossible": True,
    }


def test_qset_certificate_scope():
    # The certificate only claims impossibility when its hypotheses
    # verify — and where extents are known to exist, they don't.
    def cert(name, call="b"):
        c = rings.qset_parity_certificate(rings.METHODS[name], call)
        return c["heads"], c["extent_leads"], c["extent_impossible"]

    # Plain Bob Minor bobs-only 720: a SECOND, independent proof —
    # 60 heads = 60 leads needed, Q-sets of 3, 12 plain courses (even).
    # The reachability argument (360 < 720 rows) blocks it too.
    assert cert("Plain Bob Minor") == (60, 60, True)
    # Grandsire Doubles likewise doubly impossible: parity AND reach.
    assert cert("Grandsire Doubles") == (12, 12, True)
    # PB Doubles: 12 leads needed but 24 heads reachable, so F needn't
    # be a permutation — silent, and indeed pppb x3 exists.
    assert cert("Plain Bob Doubles") == (24, 12, False)
    # Cambridge: 30 leads of 60 heads — silent; 400 extents exist.
    assert cert("Cambridge Surprise Minor") == (60, 30, False)
    # PB Minimus: hypotheses hold but 1 plain course is already odd —
    # silent, and the plain course IS the extent.
    assert cert("Plain Bob Minimus") == (3, 3, False)
    # Singles break the parity trap with EVEN Q-sets: PB Minor
    # singles-only has Q-sets of 2 (and 120 heads > 60 leads) — silent,
    # and singles-only extents exist. Grandsire Triples with singles
    # reaches all 720 heads with Q-sets of 6 — silent, extents exist.
    c = rings.qset_parity_certificate(rings.METHODS["Plain Bob Minor"], "s")
    assert (c["qset_sizes"], c["extent_impossible"]) == ([2], False)
    c = rings.qset_parity_certificate(
        rings.METHODS["Grandsire Triples"], "s"
    )
    assert (c["heads"], c["qset_sizes"], c["extent_impossible"]) == (
        720, [6], False
    )


def test_qset_lemmas_by_brute_force():
    # The two lemmas behind the certificate, verified exhaustively on
    # Grandsire Doubles (12 heads, 4096 call assignments): 'next head'
    # is a bijection exactly for the 2^4 = 16 whole-Q-set assignments,
    # and its cycle count is always even (like the 4 plain courses) —
    # never the single round block an extent would need.
    from itertools import product

    g = rings.METHODS["Grandsire Doubles"]
    gp, gb = rings.head_perm(g, "p"), rings.head_perm(g, "b")
    sigma = rings.compose(gp, rings.inverse(gb))
    heads, _ = rings.reachable_rows(g, "pb")
    H = sorted(heads)
    orbits, seen = [], set()
    for h in H:
        if h in seen:
            continue
        orb, x = set(), h
        while x not in seen:
            seen.add(x)
            orb.add(x)
            x = rings.compose(x, sigma)
        orbits.append(orb)
    assert sorted(len(o) for o in orbits) == [3, 3, 3, 3]
    bijective, parities = [], set()
    for f in product("pb", repeat=12):
        F = {h: rings.compose(h, gp if c == "p" else gb)
             for h, c in zip(H, f)}
        if len(set(F.values())) < 12:
            continue
        bijective.append(f)
        plain = {h for h, c in zip(H, f) if c == "p"}
        assert all(o <= plain or not (o & plain) for o in orbits)
        cycles, done = 0, set()
        for h in H:
            if h in done:
                continue
            cycles += 1
            while h not in done:
                done.add(h)
                h = F[h]
        parities.add(cycles % 2)
    assert len(bijective) == 16
    assert parities == {0}


def test_lead_multiplicity_census():
    # Yesterday's open question — why does each row lie in exactly TWO
    # possible leads? — answered by census. It holds wherever calls
    # differ only in the final change (the treble passes each place
    # twice per lead): Plain Bob and Cambridge are uniformly 2, except
    # Minimus, whose lead is half the extent (1). Grandsire's calls
    # strike a change earlier and break the pattern.
    def mult(name, calls="pb"):
        return rings.lead_multiplicity(rings.METHODS[name], calls)

    assert mult("Plain Bob Minimus") == {1: 24}
    assert mult("Plain Bob Doubles") == {2: 120}
    assert mult("Plain Bob Minor") == {2: 360}
    assert mult("Plain Bob Minor", "ps") == {2: 720}
    assert mult("Plain Bob Minor", "pbs") == {2: 720}
    assert mult("Cambridge Surprise Minor") == {2: 720}
    assert mult("Grandsire Doubles") == {2: 48, 3: 12}
    # Bobs-only Grandsire Triples: leads NEARLY partition the extent.
    assert mult("Grandsire Triples") == {1: 4680, 2: 360}


def test_grandsire_triples_leads_nearly_partition():
    # The fine structure behind {1: 4680, 2: 360}: a lead head lies in
    # no lead but its own, and the shared rows are exactly the OTHER
    # treble-lead rows (treble leading, not a head). So covering all
    # 5040 rows forces using all 360 heads exactly once — the
    # hypothesis of the Thompson certificate, visible row by row.
    m = rings.METHODS["Grandsire Triples"]
    heads, rows = rings.reachable_rows(m, "pb")
    owners = {r: set() for r in rows}
    for h in heads:
        owners[h].add(h)
        for c in "pb":
            for r in list(rings.lead(h, m.lead_changes(c)))[:-1]:
                owners[r].add(h)
    assert all(owners[h] == {h} for h in heads)
    shared = {r for r, o in owners.items() if len(o) == 2}
    assert shared == {r for r in rows if r[0] == 1 and r not in heads}


def test_grandsire_triples_bobs_only_4998():
    # Thompson forbids ONE round block; parity permits two — and two
    # suffice. Hillclimbing over whole-Q-set callings (the only ones
    # whose next-head map is a permutation) found an exact 2-block
    # cover of all 5040 rows: this bobs-only 4998 (357 leads) plus the
    # single bob course bbb from 1346725 (3 leads, 42 rows). 4998 is
    # the celebrated longest bobs-only touch of Grandsire Triples —
    # the extent minus one bob course, exactly as parity dictates.
    m = rings.METHODS["Grandsire Triples"]
    calling = TOUCH_4998
    assert len(calling) == 357
    rows = rings.touch(m, calling)
    assert rows[-1] == rings.rounds(7)
    assert rings.is_true(rows)
    assert len(rows) - 1 == 4998
    head = tuple(rings.bell_from_char(c) for c in "1346725")
    block2, h = [head], head
    for _ in "bbb":
        block2.extend(rings.lead(h, m.lead_changes("b")))
        h = block2[-1]
    assert h == head
    assert rings.is_true(block2)
    missing = set(block2[:-1])
    assert len(missing) == 42
    assert not missing & set(rows[:-1])
    assert len(missing | set(rows[:-1])) == 5040


def test_no_5026_bobs_only_grandsire_triples():
    # Sharper than Thompson: no 359-lead (5026) bobs-only round block
    # exists either. A lone touch needn't call whole Q-sets, but a
    # missing head m still forces calls: neither predecessor may ring
    # into m, so P^-1(m) must be bobbed and B^-1(m) plained. But the
    # two predecessors of ANY head lie in the same Q-set — P^-1(m) =
    # sigma^4(B^-1(m)) — and that Q-set never contains m itself, so
    # with only m missing all five of its heads are used and truth
    # (successors in a cycle are distinct) forces it all-plain or
    # all-bobbed. Contradiction: 4998 cannot be beaten by one lead.
    # Left-multiplication symmetry makes m = rounds check every m.
    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    sigma = rings.compose(gp, rings.inverse(gb))
    pred_p, pred_b = rings.inverse(gp), rings.inverse(gb)
    assert pred_p != pred_b
    orbit, x = [pred_b], pred_b
    for _ in range(4):
        x = rings.compose(x, sigma)
        orbit.append(x)
    assert orbit[4] == pred_p  # same Q-set, four sigma-steps apart
    assert len(set(orbit)) == 5
    assert rings.rounds(7) not in orbit


def test_no_5012_bobs_only_grandsire_triples():
    # The last gap between the 4998 and a maximality theorem. The
    # deficit certificate mechanises the predecessor argument: fixing
    # rounds as one missing head (left-relabelling), ALL 359 choices of
    # the second missing head die of forced-call contradictions — the
    # calls forced by 'nothing rings into a missing head' cannot
    # coexist with Q-set propagation. No 358-lead block, no 5012; with
    # yesterday's no-5026 and Thompson's no-5040, nothing between 4998
    # and the extent survives.
    m = rings.METHODS["Grandsire Triples"]
    for k, configs in [(1, 1), (2, 359)]:
        cert = rings.qset_deficit_certificate(m, "b", k)
        assert cert["applicable"]
        assert cert["configs"] == configs
        assert cert["forced"] == configs  # every config self-destructs
        assert cert["block_impossible"]


def test_4998_is_maximal_and_complement_unique():
    # The whole theorem in one sweep: missing 3 heads, exactly ONE of
    # the 64261 normalised configurations survives (64259 forced-call
    # contradictions, 1 killed by parity) — and the survivor is the bob
    # course through rounds, precisely the complement of the explicit
    # 4998. So 4998 is the longest bobs-only round block of Grandsire
    # Triples, and any 4998's omitted heads are a single bob course,
    # uniquely up to relabelling.
    m = rings.METHODS["Grandsire Triples"]
    cert = rings.qset_deficit_certificate(m, "b", 3)
    assert cert["configs"] == 64261
    assert cert["forced"] == 64259
    assert cert["parity"] == 1
    assert len(cert["open_configs"]) == 1
    gb = rings.head_perm(m, "b")
    h, bob_course = rings.rounds(7), set()
    for _ in range(3):
        bob_course.add(h)
        h = rings.compose(h, gb)
    assert h == rings.rounds(7)
    assert set(cert["open_configs"][0]) == bob_course


def test_4998_realises_the_open_configuration():
    # Glue between the explicit 4998 and the k=3 sweep: relabelling the
    # 4998 by the inverse of its missing course's head sends its omitted
    # heads onto the bob course through rounds — the unique open
    # configuration — and its calling then satisfies every call the
    # certificate forces. Why the bob course escapes the k<=2
    # contradictions: a missing head's bob-predecessor lies in the
    # missing course itself (a gb-orbit), so the plain-forcing half of
    # the predecessor conflict vanishes; only P^-1 forces, bob floods
    # each broken Q-set, and just 12 calls are forced in all.
    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    sigma = rings.compose(gp, rings.inverse(gb))
    calling = TOUCH_4998
    rows = rings.touch(m, calling)
    heads = [rows[i] for i in range(0, len(rows) - 1, 14)]
    lam = rings.inverse(tuple(rings.bell_from_char(c) for c in "1346725"))
    call_of = {rings.compose(lam, h): c for h, c in zip(heads, calling)}
    missing = set()
    h = rings.rounds(7)
    for _ in range(3):
        missing.add(h)
        h = rings.compose(h, gb)
    assert not missing & set(call_of)
    assert len(call_of) == 357
    forced = {}
    for mm in missing:
        assert rings.compose(mm, rings.inverse(gb)) in missing
        hb = rings.compose(mm, rings.inverse(gp))
        while hb not in forced and hb not in missing:
            forced[hb] = "b"
            hb = rings.compose(hb, rings.inverse(sigma))
    assert len(forced) == 12
    assert all(call_of[h] == c for h, c in forced.items())


def test_deficit_certificate_scope():
    # missing=0 is Thompson's certificate again, by parity, wherever it
    # applied; and the sharper deficits transfer: Grandsire Doubles has
    # no 11-lead bobs-only block (certificate AND exhaustive search),
    # and at 10 leads the certificate is honestly silent — one open
    # configuration whose head-level successor map genuinely works —
    # while search shows no true 100 exists: Doubles leads share rows
    # (multiplicity {2,3}), a row-level obstruction the head-level
    # certificate cannot see. Plain Bob Minor kills 1 and 2 by forced
    # calls alike.
    gd = rings.METHODS["Grandsire Doubles"]
    pb = rings.METHODS["Plain Bob Minor"]
    for m in (gd, pb):
        cert = rings.qset_deficit_certificate(m, "b", 0)
        assert (cert["parity"], cert["block_impossible"]) == (1, True)
    assert rings.qset_deficit_certificate(gd, "b", 1)["block_impossible"]
    assert rings.search_extents(gd, "pb", target=110) == []
    cert = rings.qset_deficit_certificate(gd, "b", 2)
    assert not cert["block_impossible"]
    assert [
        [rings.row_str(h) for h in oc] for oc in cert["open_configs"]
    ] == [["12345", "14523"]]
    assert rings.search_extents(gd, "pb", target=100) == []
    for k in (1, 2):
        cert = rings.qset_deficit_certificate(pb, "b", k)
        assert cert["forced"] == cert["configs"]
        assert cert["block_impossible"]


def test_row_truth_is_head_truth_bobs_only_grandsire_triples():
    # The lemma that makes head-level certificates EXACT at Triples:
    # every row lies in exactly two (head, call) leads; a head's plain
    # and bob leads share their first 13 rows, and the only cross-head
    # sharing is the final body row of plain-from-h, which is also the
    # final body row of bob-from-sigma(h) — the very pair 'plained h
    # with sigma(h) bobbed' that injectivity of the next-head map
    # already forbids. So ANY call assignment whose next-head map is
    # injective rings distinct rows: row truth = head truth, and the
    # deficit certificate's open configurations are genuinely
    # realisable (no Doubles-style row-level trap on 7 bells).
    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    sigma = rings.compose(gp, rings.inverse(gb))
    heads, _ = rings.reachable_rows(m, "pb")
    bodies = {}
    for h in heads:
        for c in "pb":
            bodies[(h, c)] = [h] + list(rings.lead(h, m.lead_changes(c)))[:-1]
    owners = {}
    for key, body in bodies.items():
        for r in body:
            owners.setdefault(r, []).append(key)
    assert len(owners) == 5040
    assert all(len(o) == 2 for o in owners.values())
    cross = [o for o in owners.values() if o[0][0] != o[1][0]]
    assert len(cross) == 360
    for pair in cross:
        (hp, cp), (hb, cb) = sorted(pair, key=lambda k: k[1], reverse=True)
        assert (cp, cb) == ("p", "b")
        assert rings.compose(hp, sigma) == hb
        shared = set(bodies[(hp, "p")]) & set(bodies[(hb, "b")])
        assert shared == {bodies[(hp, "p")][13]} == {bodies[(hb, "b")][13]}


def test_4984_exists_and_comes_in_two_kinds():
    # The k=4 question answered: 4984s EXIST. The deficit certificate's
    # missing=4 sweep (513s, journal 2026-07-12) leaves exactly two
    # open configurations, and hillclimbing over free-Q-set toggles for
    # a next-head map with five cycles (four fixed missing heads + one
    # 356-cycle) realises BOTH — row truth is free by the lemma above.
    # So bobs-only Grandsire Triples lengths run ..., 4984, 4998, and
    # then nothing until impossibility; and unlike the 4998 (complement
    # a bob course, one class), the 4984s come in exactly two
    # inequivalent complement classes, neither of which is itself a
    # touch (no length-4 word in gp, gb is the identity).
    m = rings.METHODS["Grandsire Triples"]
    configs = {
        "A": {"1234567", "1243765", "1657423", "1675324"},
        "B": {"1234567", "1456372", "1637524", "1752346"},
    }
    callings = {
        "A": TOUCH_4984_A,
        "B": (
            "bppbppppbbpbbppbbpbbppbbpbbppbbpbpbbppbppbpbpbppbppbpbpppbp"
            "pbppbbpbbppbbpbpppbbpbppbbpppbbpbppppbbpbbppbbppbpbpbbppbpp"
            "ppbbpbppppbppbbpbppppbpbpbbpbpppbpbpbbpbpbpbbpppbpbpppbbppp"
            "pbbpppbpbbpbbppbpbbppbbpbbppbbpbbppbbpbbpppbbpppbbppppbpppp"
            "bpbbpppbpbpbbpbpbpbbpbpppbpbbppbpbpppbbpbpbpbbpbppppbppppbp"
            "pbbpbppppbpbppbpbbppppbppbbpbppbpppbbpbbpbpbppbbpbppbbpbbpp"
            "pb"
        ),
    }
    heads_all, _ = rings.reachable_rows(m, "pb")
    norm_classes = {}
    for name, calling in callings.items():
        assert len(calling) == 356
        rows = rings.touch(m, calling)
        assert rows[-1] == rings.rounds(7)
        assert rings.is_true(rows)
        assert len(rows) - 1 == 4984
        heads = {rows[i] for i in range(0, len(rows) - 1, 14)}
        assert len(heads) == 356
        omitted = heads_all - heads
        assert len(omitted) == 4
        norms = {
            frozenset(
                rings.row_str(rings.compose(rings.inverse(o), x))
                for x in omitted
            )
            for o in omitted
        }
        # each complement class is closed under its own normalisations
        assert norms == {frozenset(configs[name])}
        norm_classes[name] = norms
    assert norm_classes["A"] != norm_classes["B"]


def test_bobs_only_length_spectrum_grandsire_triples():
    # WHICH lead-counts L admit a bobs-only round block? Row truth =
    # head truth turns this into pure graph theory: a block of L leads
    # is exactly a simple L-cycle through rounds in the 360-head
    # digraph with edges h -> h.gp, h -> h.gb (in a cycle every vertex
    # has in-degree 1, so the forbidden pair 'h plained, sigma(h)
    # bobbed' — both feeding h.gp — cannot occur). Left-translation
    # moves any cycle onto rounds, so the spectrum is the digraph's
    # cycle spectrum. Answer: L works iff L in {3, 5, 8, 12} or
    # 15 <= L <= 357. Proof: exhaustive DFS below settles L <= 22
    # (killing 1, 2, 4, 6, 7, 9-11, 13, 14); chord-closure from the
    # known 356/357-cycles witnesses everything from 23 to 348 except
    # a handful near the top; stored callings (found by chord+ear
    # surgery and Q-set-toggle hillclimbs) witness 344 and 349-355;
    # and 358, 359, 360 are the deficit/Thompson theorems above.
    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    heads, _ = rings.reachable_rows(m, "pb")
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    P = [idx[rings.compose(h, gp)] for h in H]
    B = [idx[rings.compose(h, gb)] for h in H]
    root = idx[rings.rounds(7)]

    # exhaustive small-cycle census through rounds, L <= 22
    small = set()
    onpath = [False] * n
    onpath[root] = True

    def dfs(v, depth):
        for w in (P[v], B[v]):
            if w == root:
                small.add(depth + 1)
            elif not onpath[w] and depth + 1 < 22:
                onpath[w] = True
                dfs(w, depth + 1)
                onpath[w] = False

    dfs(root, 0)
    assert small == {3, 5, 8, 12, 15, 16, 17, 18, 19, 20, 21, 22}

    # stored witnesses for the stubborn lengths, verified end to end
    hard = {
        344: "pppbbpbppppbppppbbpbpbpppbpbbppbbpbpbbppbppppbppbbppbbppppb"
             "bppppbbppppbbpbpppbppppbbppppbbpppbbpbbpppbbppbbppbppbbpbpp"
             "pbbpbppbpbbppbppbbppbpppbppppbbppbbpppbbpppbpppbbppbbpppbbp"
             "bpbpbbppbpbbpppbbpbppppbppbpbppppbbppbppbpbbpbppbbpbpbpbbpb"
             "ppbbppbbppppbppbppbpbbpbbppppbppppbpbbppbpbbpbbpbppppbpbbpp"
             "ppbppppbppbppbpbppbbpbpbpppbppbbppbbppppbbppbppbp",
        349: "bppbpbppbbpbpbpppbppbbppbbppppbbppbpbbppppbbpbpbpppbpbbppbb"
             "pbpbbppbppppbppbbppbbppppbbppppbbppppbbpbpppbppppbbppppbbpp"
             "pbbpbbpppbbppbbppbppbbpbpppbbpbppbpbbppbppbbppbpppbppppbbpp"
             "bbpppbbpppbpppbbppbbpppbbpbpbpbbppbpbbpppbbpbppppbppbpbpppp"
             "bbppbppbpbbpbppbbpbpbpbbpbppbbppbbppppbppbppbpbbpbbppppbppp"
             "pbpbbppbpbbpbbpbppppbpbbppppbppppbpbpppbpbbpppbbpbpppb",
        350: "pbpbppppbpbbpppbpppbbppbbppbppbbpbbpbbppbbpbppbpppbpbbppbpp"
             "bppppbbppbbppbpbpbbppbbpbbppbbpbbpbppppbpbbpppbbppbbppppbpb"
             "pbppbppbpbpbbpppbppppbbpbbppbppbpbpbbpbbpbbppbbpbbpbpbbppbb"
             "pbbppbppbppbpbbpbbppbppbbppbbpppbbpppbpbbppppbbpppbbpbpbbpp"
             "ppbpbbppbpbppbbppppbbpbbppbbpbbppbbpbbppbbpbppppbpppbbppbbp"
             "pppbbppbpbbppppbpbbpbbppppbbpbbppbbpbpppbpppbbpbbpbpbbp",
        351: "pbppbbppbbpppbbpppbpbbppppbbpppbbpbpbbppppbpbbppbpbppbbpppp"
             "bbpbbppbbpbbppbbpbbppbbpbppppbpbppbbppbpbbppppbpbbpbbppppbb"
             "pbbppbbpbpppbpppbbpbbpbbpppbppbpbbpbpbppppbpbbpppbpppbbppbb"
             "ppbppbbpbbpbbppbbpbppbpppbpbbppbppbppppbbppbbppbpbpbbppbbpb"
             "bppbbpbbpbppppbpbbpppbbppbbppppbpbpbppbppbpbpbbpppbppppbbpb"
             "bppbppbpbpbbpbbpbbppbbpbbpbpbbppbbpbbppbppbppbbpbbppbbpb",
        352: "pppbbpbppbbpbppbbppppbppppbpppbbppbbppbpbpbbppppbppppbbpppb"
             "bpppbbpppbppbppppbbpbpbppbbpbbppbbpbpbbpppbbpbbppbpbppbbpbb"
             "ppbpbbppbppppbpppbppppbpbpppbppbbpppbbpbpbbppbbpbbpbpbppbbp"
             "bppbbpppbppppbppbppppbpbbppppbppbppbbpbbpbbppbpppbpbppbbppp"
             "bppppbpppbbppbpbbppbbpbbppbpbppbbpbbppbpbbpbbppppbbpbbppbpp"
             "ppbbppbbppppbbpbpppbppbppbpbppbbppbbppppbpbppbpbbpppbpbbp",
        353: "pbpppbppbppppbbpbbppbbpbppppbppppbbpbbppppbbppbbpppbpbppbpp"
             "ppbpbbppppbppppbppppbppbbppppbbpbbppppbppbppbpbbppppbppppbb"
             "ppppbbppbbpppbpbbppppbbpbpppbppppbbpbppbpbppbbpbpbppppbbppb"
             "ppbpbpbppbppppbppppbbpbppbbppbbppppbpbppbbppppbbpbbppbbpbbp"
             "pbbpbpbpbbppppbpbbppbpbppbppppbpbpbppbbpbppppbbpbpbpbbpbppb"
             "pppbbppppbbpppbppppbpppbppbbppbppppbpbbpbppppbbppbppppbbpb",
        354: "bppbbpbpppbpppbbpbbpbpbbppbpbppppbpbbpppbpppbbppbbppbppbbpb"
             "bpbbppbbpbppbpppbpbbppbppbppppbbppbbppbpbpbbppbbpbbppbbpbbp"
             "bppppbpbbpppbbppbbppppbpbpbppbppbpbpbbpppbppppbbpbbppbppbpb"
             "pbbpbbpbbppbbpbbpbpbbppbbpbbppbppbppbpbbpbbppbppbbppbbpppbb"
             "pppbpbbppppbbpppbbpbpbbppppbpbbppbpbppbbppppbbpbbppbbpbbppb"
             "bpbbppbbpbppppbpppbbppbbppppbbppbpbbppppbpbbpbbppbppbppbpbp",
        355: "bbppppbbppbppbbpbbppppbpbbpppbbpbppppbppppbbpbpbpppbpbbppbb"
             "pbpbbppbppppbppbbppbbppppbbppppbbppppbbpbpppbppppbbppppbbpp"
             "pbbpbbpppbbppbbppbppbbpbpppbbpbppbpbbppbppbbppbpppbppppbbpp"
             "bbpppbbpppbpppbbppbbpppbbpbpbpbbppbpbbpppbbpbppppbppbpbpppp"
             "bbppbppbpbbpbppbbpbpbpbbpbppbbppbbppppbppbppbpbbpbbppppbppp"
             "pbpbbppbpbbpbbpbppppbpbbppppbppppbppbppbpbppbbpbpbpppbppbbpp",
    }
    achieved = set(small)
    for L, calling in hard.items():
        assert len(calling) == L
        rows = rings.touch(m, calling)
        assert rows[-1] == rings.rounds(7)
        assert rings.is_true(rows)
        assert len(rows) - 1 == 14 * L
        achieved.add(L)

    # chord closure: an alternate edge landing back on a cycle closes
    # a shorter cycle; iterating from the 3-, 5-, 356- and 357-cycles
    # witnesses every remaining length. Each new cycle is checked to
    # be a genuine simple cycle in the digraph, which by the row-truth
    # lemma IS a true touch (translated to pass through rounds).
    def cycle_of(calling):
        v, cyc = root, []
        for c in calling:
            cyc.append(v)
            v = P[v] if c == "p" else B[v]
        assert v == root
        return cyc

    from collections import deque
    queue = deque([
        cycle_of("bbb"),
        cycle_of("ppppp"),
        cycle_of(TOUCH_4984_A),
        cycle_of(TOUCH_4998),
    ])
    achieved.update(len(c) for c in queue)
    while queue:
        C = queue.popleft()
        ln = len(C)
        pos = {v: i for i, v in enumerate(C)}
        assert len(pos) == ln
        assert all(C[(i + 1) % ln] in (P[v], B[v]) for i, v in enumerate(C))
        for i, v in enumerate(C):
            alt = B[v] if P[v] == C[(i + 1) % ln] else P[v]
            j = pos.get(alt)
            if j is None or j == (i + 1) % ln:
                continue
            L = (i - j) % ln + 1
            if L not in achieved:
                achieved.add(L)
                queue.append([C[(j + t) % ln] for t in range(L)])

    assert achieved == {3, 5, 8, 12} | set(range(15, 358))


def test_grandsire_extent_needs_singles():
    g = rings.METHODS["Grandsire Doubles"]
    found = rings.search_extents(g, "pbs")
    assert len(found) == 10
    for calling in found:
        assert rings.is_extent(rings.touch(g, calling))
        # singles are odd permutations, so an even nonzero number is needed
        assert calling.count("s") in (2, 6)


def test_plain_bob_minor_singles_only_extent():
    # The mirror image of the bobs-only ceiling: the single (1234) is an
    # odd change, so singles alone reach all 720 rows — and singles-only
    # extents exist.
    pb = rings.METHODS["Plain Bob Minor"]
    heads, rows = rings.reachable_rows(pb, "ps")
    assert (len(heads), len(rows)) == (120, 720)
    found = rings.search_extents(pb, "ps", limit=1)
    assert len(found) == 1 and len(found[0]) == 60
    assert rings.is_extent(rings.touch(pb, found[0]))
    assert found[0].count("s") % 2 == 0


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


def test_plain_bob_doubles_all_extents_with_singles():
    # Allowing singles too, PB Doubles has exactly 12 extent callings:
    # three three-part classes, each its own reverse — the classic
    # bobs-only bppp x3, a singles-only ppps x3, and the mixed bpsp x3.
    pb = rings.METHODS["Plain Bob Doubles"]
    found = rings.search_extents(pb, "pbs")
    assert len(found) == 12
    canons = ["bpppbpppbppp", "bpspbpspbpsp", "pppspppsppps"]
    assert sorted(rings.rotation_classes(found)) == canons
    assert sorted(rings.reversal_classes(found)) == canons


def test_maximal_bobs_only_censuses():
    # The reachability ceilings are not just attained but attained in
    # style. Grandsire Doubles: exactly 2 bobs-only 60s, one class —
    # bob every other lead. Plain Bob Minor: exactly 140 bobs-only
    # 360s — 2 three-parts (orbit 10) and 4 full-period (orbit 30),
    # pairing under reversal with no fixed points into 3.
    g = rings.METHODS["Grandsire Doubles"]
    found = rings.search_extents(g, "pb", target=60)
    assert sorted(found) == ["bpbpbp", "pbpbpb"]
    pb = rings.METHODS["Plain Bob Minor"]
    found = rings.search_extents(pb, "pb", target=360)
    assert len(found) == 140
    rot = rings.rotation_classes(found)
    assert sorted(len(v) for v in rot.values()) == [10] * 2 + [30] * 4
    three_parts = sorted(c for c, v in rot.items() if len(v) == 10)
    assert three_parts == [
        "bbpppbppppbbpppbppppbbpppbpppp",
        "bbppppbpppbbppppbpppbbppppbppp",
    ]
    rev = rings.reversal_classes(found)
    assert sorted(len(v) for v in rev.values()) == [20, 60, 60]


def test_reversal_classes():
    # Cambridge is palindromic, so the reverse of an extent calling is
    # again one — in fact every rotation of the reverse is.
    cam = rings.METHODS["Cambridge Surprise Minor"]
    c = ("ppppbppbpb" * 3)[::-1]
    rotations = [c[i:] + c[:i] for i in range(len(c))]
    assert all(rings.is_extent(rings.touch(cam, r)) for r in rotations)
    # At Doubles every rotation class is its own reverse: classifying up
    # to rotation+reversal changes nothing (1, 2 and 2 classes stand).
    for name, calls, canons in [
        ("Plain Bob Doubles", "pb", ["bpppbpppbppp"]),
        ("Grandsire Doubles", "pbs", ["bpbpspbpbpsp", "bspsbspsbsps"]),
        ("Stedman Doubles", "ps",
         ["pppppppppsppppppppps", "ppppsppppsppppspppps"]),
    ]:
        found = rings.search_extents(rings.METHODS[name], calls)
        assert sorted(rings.reversal_classes(found)) == canons


def test_relabelling_cambridge_extents_gives_only_rotations():
    # Could relabelling the bells (conjugation) relate two of
    # Cambridge's extent classes? Relabelling a touch by the inverse of
    # any of its 720 rows gives a sequence through rounds with the SAME
    # change at every step; it is a touch of Cambridge again only if
    # lead boundaries realign. Cambridge's 24-change sequence matches
    # itself at no nonzero offset (even letting each lead end be 12 or
    # 14), so the only relabellings are by lead heads \u2014 exactly the 30
    # rotations of the calling, already counted. The census 400/16/8
    # stands under conjugation.
    cam = rings.METHODS["Cambridge Surprise Minor"]
    tokens = cam.lead_changes("p")
    body, seq = tokens[:23], tokens * 2
    viable = []
    for k in range(24):
        ok = True
        for i, b in enumerate(body):
            if (k + i) % 24 == 23:
                ok = ok and b in [(1, 2), (1, 4)]
            else:
                ok = ok and seq[k + i] == b
        if ok:
            viable.append(k)
    assert viable == [0]
    # and relabelling by a lead head really does rotate the calling:
    calling = "ppppbppbpb" * 3
    rows = rings.touch(cam, calling)[:-1]
    lam = {b: i + 1 for i, b in enumerate(rows[24])}
    relabelled = [tuple(lam[b] for b in r) for r in rows[24:] + rows[:24]]
    assert relabelled == rings.touch(cam, calling[1:] + calling[:1])[:-1]


def test_cambridge_full_census_slow():
    # The complete bobs-only census of Cambridge Surprise Minor (~1 min):
    # exactly 400 extents; 16 rotation classes — 4 three-parts (orbit
    # 10) and 12 full-period (orbit 30); reversal pairs the 16 with no
    # fixed points, three-parts among themselves: 8 up to rotation and
    # reversal. Run with RINGS_SLOW=1.
    if not os.environ.get("RINGS_SLOW"):
        return
    cam = rings.METHODS["Cambridge Surprise Minor"]
    found = rings.search_extents(cam, "pb")
    assert len(found) == 400
    rot = rings.rotation_classes(found)
    assert len(rot) == 16
    orbits = sorted(len(v) for v in rot.values())
    assert orbits == [10] * 4 + [30] * 12
    three_parts = [c for c, v in rot.items() if len(v) == 10]
    assert all(c == c[:10] * 3 for c in three_parts)
    rev = rings.reversal_classes(found)
    assert len(rev) == 8  # no class is its own reverse
    assert sorted(len(v) for v in rev.values()) == [20] * 2 + [60] * 6


def test_blue_line_connectors():
    # Treble hunting out and back: \ \ \ | / / / |
    rows = rings.plain_course("x14x14,12", 4)
    art = rings.blue_line(rows[:9])
    connectors = [line.strip() for line in art.splitlines()[1::2]]
    assert connectors == ["\\", "\\", "\\", "|", "/", "/", "/", "|"]


def test_svg_diagram():
    st = rings.METHODS["Stedman Doubles"]
    rows = rings.course(st)
    svg = rings.to_svg(rows, tracks=(1, 2), per_column=12, rule=6)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    # 5 columns x 2 tracked bells = 10 polylines, 13 points each
    lines = [l for l in svg.splitlines() if l.startswith("<polyline")]
    assert len(lines) == 10
    assert all(l.count(",") == 13 for l in lines)
    assert '"#c02020"' in svg and '"#2050c0"' in svg  # red treble, blue line
    # one rule at the six end mid-column, per column
    assert sum(l.startswith("<line") for l in svg.splitlines()) == 5
    # the non-treble track gets a place-bell number at each column top
    labels = [l for l in svg.splitlines() if "font-weight" in l]
    assert [l[-8] for l in labels] == [
        str(chunk.index(2) + 1) for chunk in
        (rows[0], rows[12], rows[24], rows[36], rows[48])
    ]


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
