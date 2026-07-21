"""Tests for rings.py. Run: python3 test_rings.py

Set RINGS_SLOW=1 to include the ~1 minute exhaustive census tests."""

import itertools
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
# The LONGEST palindromic bobs-only touches of Grandsire Triples:
# 339 leads (4746 changes) and 338 leads (4732), found 2026-07-21 by
# the exhaustive mu-matching sweeps of test_no_palindromic_long_
# touches_grandsire_triples. Each was the unique "family B"
# complement of its length (all usable alpha-fixed heads, no extra
# cross pairs). No palindromic touch of 340..357 leads exists, so
# 4746 is the exact palindromic ceiling.
PAL_4746 = (
    "pbppppbbpbbpppbbppppbbppppbpbpbppbpbbppppbbppppbbppppbbppbbp"
    "ppbbpppbbppbpppbbpbppppbbpbbppppbbpbppbbpppbpbbppppbbppbbppb"
    "pbppbppbbpbpbppppbbppppbbpppbbpbppbbpbpbbppbbpbppbppbpbbppbb"
    "pbpbbppbpbbpppbbppppbbppppbpbpbbppbppbpbppbbppbbppppbbpbpppb"
    "bppbpbbppppbbpbbppppbpbbpppbppbbpppbbpppbbppbbppppbbppppbbpp"
    "ppbbpbppbpbpbppppbbppppbbpppbbpbbppppbp"
)
PAL_4732 = (
    "ppbpppbppppbbppbbpppbppppbbppbbppbppppbbpppbbppbbppppbbppbpb"
    "bpbpppbbpppbppbpbbppppbbpbppbpbpbppppbbppppbbpppbpppbpbbppbb"
    "pbpbbppppbpbbppbppbbppppbbppbppbppppbbpbbppppbbppppbbppppbbp"
    "bbppppbppbppbbppppbbppbppbbpbppppbbpbpbbppbbpbpppbpppbbppppb"
    "bppppbpbpbppbpbbppppbbpbppbpppbbpppbpbbpbppbbppppbbppbbpppbb"
    "ppppbppbbppbbppppbpppbbppbbppppbpppbpp"
)
# Whole-Q-set callings, one 72-bit toggle vector per Q-set (in
# sorted-head sigma-orbit order): bit q set means Q-set q is bobbed.
# The cycle of the resulting next-head permutation through rounds has
# the keyed length. Found by Q-set-toggle hillclimbs, 2026-07-15.
WHOLE_QSET_TOGGLES = {
    3: "1" * 72,
    5: "0" * 72,
    8: "00010100100010010110110101100111100001000000011100"
       "1100010011001010010100",
    12: "11001001000111111001101001111111000000001010100101"
        "1011011000010111110011",
    17: "00111101110111010000001000100111001010010001000111"
        "0100111001100111000011",
    344: "0001011001100100011010011100000000010111000011001"
         "01000101100010011110101",
    345: "0011101001011011000000011001000011010110100100001"
         "11011001000010100101010",
    346: "0001101101000011000101000111010000100001010110111"
         "11011000001100110000010",
    347: "0001100010110100110001100010010011001101000000110"
         "01110001011000110001011",
    348: "0000101101010011101011001010000000100000110010011"
         "01001001000101111100111",
    349: "0010101101000001000111011010010010000110010010110"
         "10100010001100000101001",
    351: "0011000101000110101001000111010010111101000111111"
         "10100010110110010100000",
    352: "0000000101101000100000011001010010001010010100110"
         "01011010001111011111000",
    355: "0100110010101110000010101100100100000010110101000"
         "00010101101110001000101",
}


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


def test_short_bobs_only_touch_census_grandsire_triples():
    # Refining the spectrum: not just WHICH small lead-counts occur,
    # but exactly how many touches realise each. The depth-22 DFS
    # (~1.5s) enumerates every bobs-only round block of at most 22
    # leads. The short ones are astonishingly rigid — every touch of
    # at most 15 leads is a k-part for some k >= 3:
    #   3 = (b)^3 and 5 = (p)^5, uniquely (the two courses);
    #   8 = (pb)^4, uniquely up to rotation — plain and bob strictly
    #       alternating, so gp.gb has order 4;
    #   12 = (pppb)^3, (ppb)^4 or (ppbb)^3, nothing else;
    #   15 = (pbb)^5, uniquely up to rotation.
    # The first touch with NO rotational symmetry has 16 leads (two
    # full-period classes alongside four 2-parts), and at the prime
    # length 17 all 17 callings are rotations of one asymmetric
    # touch. Counts of callings (= cycles through rounds) and of
    # rotation classes, exhaustively:
    #   L        3  5  8  12  15  16  17  18  19   20   21   22
    #   touches  1  1  2  11   3  64  17  33  95  530  497  495
    #   classes  1  1  1   3   1   6   1   3   5   29   25   25
    #   mirror   1  1  1   3   1   3   1   3   4   17   16   16
    # The reversal relabelling t = (35)(47) (next test) closes every
    # level under reading the calling backwards and pairs rotation
    # classes into mirror classes. Chirality first appears alongside
    # asymmetry: at 16 ALL six rotation classes are chiral (three
    # mirror pairs — even the four 2-parts), while the lone 17-class,
    # rotationally asymmetric, is nonetheless self-mirror: its
    # reversal is one of its own rotations. Chiral pairs per L:
    # 3 at 16, 1 at 19, 12 at 20, 9 at 21, 9 at 22.
    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    heads, _ = rings.reachable_rows(m, "pb")
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    P = [idx[rings.compose(h, gp)] for h in H]
    B = [idx[rings.compose(h, gb)] for h in H]
    root = idx[rings.rounds(7)]
    callings = {}
    onpath = [False] * n
    onpath[root] = True
    word = []

    def dfs(v, depth):
        for w, c in ((P[v], "p"), (B[v], "b")):
            word.append(c)
            if w == root:
                callings.setdefault(depth + 1, []).append("".join(word))
            elif not onpath[w] and depth + 1 < 22:
                onpath[w] = True
                dfs(w, depth + 1)
                onpath[w] = False
            word.pop()

    dfs(root, 0)
    assert {L: len(cs) for L, cs in callings.items()} == {
        3: 1, 5: 1, 8: 2, 12: 11, 15: 3, 16: 64, 17: 17, 18: 33,
        19: 95, 20: 530, 21: 497, 22: 495,
    }
    classes = {L: rings.rotation_classes(cs) for L, cs in callings.items()}
    assert {L: len(c) for L, c in classes.items()} == {
        3: 1, 5: 1, 8: 1, 12: 3, 15: 1, 16: 6, 17: 1, 18: 3,
        19: 5, 20: 29, 21: 25, 22: 25,
    }
    assert callings[3] == ["bbb"]
    assert callings[5] == ["ppppp"]
    assert list(classes[8]) == ["bpbpbpbp"]
    assert sorted(classes[12]) == [
        "bbppbbppbbpp", "bppbppbppbpp", "bpppbpppbppp"
    ]
    assert list(classes[15]) == ["bbpbbpbbpbbpbbp"]

    def period(w):
        return next(
            d for d in range(1, len(w) + 1)
            if len(w) % d == 0 and w == w[:d] * (len(w) // d)
        )

    for L, cs in callings.items():
        if L <= 15:
            assert all(L // period(w) >= 3 for w in cs)
    sym16 = sorted(len(w) // period(w) for w in classes[16])
    assert sym16 == [1, 1, 2, 2, 2, 2]  # asymmetry first appears at 16
    assert all(period(w) == 17 for w in callings[17])

    # reversal symmetry: every level closed under reading backwards
    for L, cs in callings.items():
        assert {c[::-1] for c in cs} == set(cs)
    mirror = {L: rings.reversal_classes(cs) for L, cs in callings.items()}
    assert {L: len(c) for L, c in mirror.items()} == {
        3: 1, 5: 1, 8: 1, 12: 3, 15: 1, 16: 3, 17: 1, 18: 3,
        19: 4, 20: 17, 21: 16, 22: 16,
    }

    def self_mirror(canon):
        return canon[::-1] in {
            canon[i:] + canon[:i] for i in range(len(canon))
        }

    chiral = {
        L: sum(not self_mirror(c) for c in cls) // 2
        for L, cls in classes.items()
    }
    assert chiral == {
        3: 0, 5: 0, 8: 0, 12: 0, 15: 0, 16: 3, 17: 0, 18: 0,
        19: 1, 20: 12, 21: 9, 22: 9,
    }
    assert not any(self_mirror(c) for c in classes[16])  # 16 all chiral
    assert all(self_mirror(c) for c in classes[17])


def test_reversal_relabelling_grandsire_triples():
    # Grandsire is not palindromic — a lead rung backwards is not a
    # Grandsire lead — yet its bobs-only compositions DO reverse: the
    # calling of any true round block, read backwards, is again one.
    # The reason is startlingly concrete: relabelling the bells by
    # t = 1257364 = (35)(47) conjugates BOTH lead-head permutations
    # to their inverses, so alpha: h -> t.h.t^-1 fixes rounds and
    # reverses every edge of the 360-head digraph. Each simple
    # L-cycle maps to a simple L-cycle traversed the other way, and a
    # touch with calling c to a touch with calling reversed(c) — by
    # the row-truth lemma, genuinely true touches. t is the ONLY
    # element of all S_7 with this property; it is an involution and
    # is itself a reachable lead head, so alpha is inner: its 8 fixed
    # heads are exactly the centraliser of t in the head group. No
    # label-SWAPPING reversal can exist for any relabelling or indeed
    # any bijection of heads whatsoever: plain-only cycles are the
    # 5-lead plain courses and bob-only cycles the 3-lead bob
    # courses, and reversal preserves single-label cycle lengths.
    m = rings.METHODS["Grandsire Triples"]
    ts = rings.reversal_relabellings(m, "pb")
    assert ts == [(1, 2, 5, 7, 3, 6, 4)]
    t = ts[0]
    ti = rings.inverse(t)
    assert rings.compose(t, t) == rings.rounds(7)  # an involution
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    heads, _ = rings.reachable_rows(m, "pb")
    assert t in heads
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    P = [idx[rings.compose(h, gp)] for h in H]
    B = [idx[rings.compose(h, gb)] for h in H]
    Pi, Bi = [0] * n, [0] * n
    for i in range(n):
        Pi[P[i]], Bi[B[i]] = i, i
    A = [idx[rings.compose(rings.compose(t, h), ti)] for h in H]
    assert sorted(A) == list(range(n))  # heads closed under alpha
    root = idx[rings.rounds(7)]
    assert A[root] == root
    assert all(A[P[v]] == Pi[A[v]] for v in range(n))  # plain reversed
    assert all(A[B[v]] == Bi[A[v]] for v in range(n))  # bob reversed
    fixed = [v for v in range(n) if A[v] == v]
    centraliser = [
        h for h in H if rings.compose(t, h) == rings.compose(h, t)
    ]
    assert len(fixed) == 8
    assert [H[v] for v in fixed] == centraliser
    assert t in {H[v] for v in fixed}

    # reversal in action on the record touches: the 4998 and the
    # 4984, callings read backwards, ring true end to end
    for calling in (TOUCH_4998, TOUCH_4984_A):
        rows = rings.touch(m, calling[::-1])
        assert rows[-1] == rings.rounds(7)
        assert rings.is_true(rows)
        assert len(rows) - 1 == 14 * len(calling)

    # no label-swapping reversal: single-label cycle lengths differ
    def orbit_sizes(g):
        sizes, seen = [], set()
        for h in heads:
            if h in seen:
                continue
            size, x = 0, h
            while x not in seen:
                seen.add(x)
                x = rings.compose(x, g)
                size += 1
            sizes.append(size)
        return set(sizes)

    assert orbit_sizes(gp) == {5} and orbit_sizes(gb) == {3}

    # the same reversal-by-relabelling exists for every stock
    # single-block method — unique except at Minimus, where the tiny
    # head group leaves room for three
    counts = {
        "Plain Bob Minimus": 3, "Plain Bob Doubles": 1,
        "Plain Bob Minor": 1, "Grandsire Doubles": 1,
        "Cambridge Surprise Minor": 1,
    }
    for name, k in counts.items():
        assert len(rings.reversal_relabellings(rings.METHODS[name])) == k


def test_singles_break_reversal_grandsire_triples():
    # The mirror symmetry of the previous test is a bobs-only
    # phenomenon. Admitting singles, the head group doubles — from
    # A_6 (360 heads) to all 720 treble-led rows — and reversal
    # BREAKS: no relabelling inverts all three lead-head permutations
    # at once, and no bijection of heads whatsoever reverses the
    # 3-labelled digraph. (Only gp has order 5 so a reversal must
    # send plain edges to reversed plain edges; the deterministic
    # extension of rounds -> rounds fails for both label pairings
    # b->b and b->s, and left-translations move any anti-automorphism
    # to one fixing rounds, so none exists at all.) The breakage is
    # not merely abstract: in the exhaustive census of true touches
    # with singles up to 10 leads, the 7 + 4 + 30 touches of 6, 8, 9
    # leads all still reverse by coincidence, but ALL TEN true
    # 10-lead touches fail — pbspspbsps is the shortest calling of a
    # true touch (140 changes) whose reversal does not even come
    # round. Singles also break the row-truth lemma the bobs-only
    # theory leans on: ppppbpbssbb rings true while ppppbpbbsbs
    # visits 11 distinct heads yet repeats a row (a bob lead and a
    # single lead from different heads can share one).
    m = rings.METHODS["Grandsire Triples"]
    assert rings.reversal_relabellings(m, "pbs") == []
    gp, gb, gs = (rings.head_perm(m, c) for c in "pbs")

    def order(g):
        x, k = g, 1
        while x != rings.rounds(7):
            x, k = rings.compose(x, g), k + 1
        return k

    assert (order(gp), order(gb), order(gs)) == (5, 3, 6)
    heads, _ = rings.reachable_rows(m, "pbs")
    assert len(heads) == 720 and all(h[0] == 1 for h in heads)
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    T = {c: [idx[rings.compose(h, g)] for h in H]
         for c, g in zip("pbs", (gp, gb, gs))}
    inv = {}
    for c, t in T.items():
        inv[c] = [0] * n
        for i, w in enumerate(t):
            inv[c][w] = i
    root = idx[rings.rounds(7)]

    def anti(pairing):
        A = [-1] * n
        A[root] = root
        stack = [root]
        while stack:
            v = stack.pop()
            for c, d in pairing.items():
                w, target = T[c][v], inv[d][A[v]]
                if A[w] < 0:
                    A[w] = target
                    stack.append(w)
                elif A[w] != target:
                    return None
        return A

    assert anti({"p": "p", "b": "b", "s": "s"}) is None
    assert anti({"p": "p", "b": "s", "s": "b"}) is None

    def rev_returns(calling):
        v = root
        for c in reversed(calling):
            v = T[c][v]
        return v == root

    stats = {}
    onpath = [False] * n
    onpath[root] = True
    word = []

    def dfs(v, depth):
        for c in "pbs":
            w = T[c][v]
            word.append(c)
            if w == root:
                calling = "".join(word)
                if "s" in calling and rings.is_true(
                    rings.touch(m, calling)
                ):
                    k = "ok" if rev_returns(calling) else "cex"
                    s = stats.setdefault(len(calling), [0, 0, None])
                    s[0 if k == "ok" else 1] += 1
                    if k == "cex" and s[2] is None:
                        s[2] = calling
            elif not onpath[w] and depth + 1 < 10:
                onpath[w] = True
                dfs(w, depth + 1)
                onpath[w] = False
            word.pop()

    dfs(root, 0)
    assert stats == {
        6: [7, 0, None], 8: [4, 0, None], 9: [30, 0, None],
        10: [0, 10, "pbspspbsps"],
    }
    rows = rings.touch(m, "pbspspbsps")
    assert rows[-1] == rings.rounds(7) and rings.is_true(rows)
    assert len(rows) - 1 == 140
    assert rings.touch(m, "pbspspbsps"[::-1])[-1] != rings.rounds(7)

    rows = rings.touch(m, "ppppbpbssbb")
    assert rows[-1] == rings.rounds(7) and rings.is_true(rows)
    assert rings.touch(m, "ppppbpbssbb"[::-1])[-1] != rings.rounds(7)
    rows = rings.touch(m, "ppppbpbbsbs")
    assert rows[-1] == rings.rounds(7) and not rings.is_true(rows)
    assert len({tuple(rows[i * 14]) for i in range(11)}) == 11


def test_whole_qset_spectrum_near_the_ends():
    # Which lengths admit a WHOLE-Q-SET touch — a bobs-only round
    # block whose calling is constant on every Q-set it meets, i.e.
    # extends to a permutation F~ of all 360 heads (the callings that
    # Q-set-toggle search can reach)? Near the top this spectrum is
    # strictly smaller than the full one, which is why 350 and
    # 353/354 resisted the toggle hillclimbs on 2026-07-14.
    #
    # Impossibility: toggling a Q-set composes F~ with a 5-cycle on
    # it (B = P.sigma^-1, verified below), an even permutation, so
    # every whole-Q-set F~ has the sign of the plain map and, on 360
    # points, a cycle count of fixed parity — even, like the 72 plain
    # courses. A whole-Q-set touch of L leads puts rounds on an
    # L-cycle of F~, so the 360 - L complement heads split into an
    # ODD number of F~-cycles; each is a simple digraph cycle, and by
    # translation onto rounds the DFS below shows no cycle has length
    # in {1, 2, 4, 6, 7, 9, 10, 11, 13, 14}. Hence the complement
    # cannot have size 0 (an odd number of cycles is at least one),
    # 1, 2, 4, 6 or 7 (no cycle lengths sum to these), or 10 (not a
    # length; three or more cycles total >= 9 but never 10): no
    # whole-Q-set touch of 360 (Thompson restricted to this class,
    # by a two-line argument), 359, 358, 356, 354, 353 or 350.
    #
    # Sufficiency: the stored WHOLE_QSET_TOGGLES vectors witness every
    # other length in [344, 360) plus both small-end survivors 8 and
    # 12 (and a 17, kept as a search seed for the complete-spectrum
    # test below); 3 is the all-bob F~ (a bob course), 5 the
    # all-plain, and 357 the 4998 itself, whose calling is checked to
    # be whole-Q-set. The complement arithmetic is sharp: 351 = 360 -
    # (3+3+3), 349 = 360 - (3+3+5), 347 = 360 - (3+5+5), 346 = 360 -
    # (3+3+8), 344 = 360 - (3+5+8) — every sum an odd number of
    # genuine cycle lengths, exactly as the parity invariant demands.
    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    sigma = rings.compose(gp, rings.inverse(gb))
    heads, _ = rings.reachable_rows(m, "pb")
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    P = [idx[rings.compose(h, gp)] for h in H]
    B = [idx[rings.compose(h, gb)] for h in H]
    S = [idx[rings.compose(h, sigma)] for h in H]
    Si = [0] * n
    for i in range(n):
        Si[S[i]] = i
    root = idx[rings.rounds(7)]
    # a toggle is composition with the 5-cycle sigma^-1 on the Q-set
    assert all(B[v] == P[Si[v]] for v in range(n))
    orbit, orbits = [-1] * n, []
    for i in range(n):
        if orbit[i] >= 0:
            continue
        o, j = [], i
        while orbit[j] < 0:
            orbit[j] = len(orbits)
            o.append(j)
            j = S[j]
        orbits.append(o)
    assert len(orbits) == 72 and all(len(o) == 5 for o in orbits)

    # cycle lengths through rounds up to 14: {3, 5, 8, 12} only
    small = set()
    onpath = [False] * n
    onpath[root] = True

    def dfs(v, depth):
        for w in (P[v], B[v]):
            if w == root:
                small.add(depth + 1)
            elif not onpath[w] and depth + 1 < 14:
                onpath[w] = True
                dfs(w, depth + 1)
                onpath[w] = False

    dfs(root, 0)
    assert small == {3, 5, 8, 12}

    complements = {
        3: [3] * 119, 5: [5] * 71,
        344: [3, 5, 8], 345: [3, 3, 3, 3, 3], 346: [3, 3, 8],
        347: [3, 5, 5], 348: [12], 349: [3, 3, 5], 351: [3, 3, 3],
        352: [8], 355: [5],
    }
    achieved = set()
    for L, bits in WHOLE_QSET_TOGGLES.items():
        F = [B[v] if bits[orbit[v]] == "1" else P[v] for v in range(n)]
        cycles, done = [], [False] * n
        for i in range(n):
            if done[i]:
                continue
            c = []
            while not done[i]:
                done[i] = True
                c.append(i)
                i = F[i]
            cycles.append(c)
        assert len(cycles) % 2 == 0  # the parity invariant, in action
        mine = next(c for c in cycles if root in c)
        assert len(mine) == L
        if L in complements:
            comp = sorted(len(c) for c in cycles if root not in c)
            assert comp == complements[L]
        k = mine.index(root)
        calling = "".join(
            "b" if bits[orbit[v]] == "1" else "p"
            for v in mine[k:] + mine[:k]
        )
        rows = rings.touch(m, calling)
        assert rows[-1] == rings.rounds(7)
        assert rings.is_true(rows)
        assert len(rows) - 1 == 14 * L
        achieved.add(L)

    # the 4998 is itself whole-Q-set: its 357 used heads never split
    # a Q-set between plain and bob
    rows = rings.touch(m, TOUCH_4998)
    call_of = {idx[rows[i * 14]]: c for i, c in enumerate(TOUCH_4998)}
    assert all(
        len({call_of[v] for v in o if v in call_of}) <= 1 for o in orbits
    )
    achieved.add(357)

    assert achieved == {3, 5, 8, 12, 17} | (
        set(range(344, 358)) - {350, 353, 354, 356}
    )


def test_whole_qset_spectrum_complete():
    # The FULL whole-Q-set spectrum: L admits a whole-Q-set bobs-only
    # round block iff L is in the length spectrum {3, 5, 8, 12} or
    # [15, 357] MINUS {350, 353, 354, 356}. The four missing lengths
    # are the parity theorem of the previous test (complements of
    # size 10, 7, 6, 4 cannot be an odd number of digraph cycles);
    # everything else is witnessed constructively here: breadth-first
    # search over single-Q-set toggles from the stored vectors covers
    # every remaining length in two generations (~36000 permutations
    # F~, each cycle through rounds a genuine touch by the row-truth
    # lemma). Along the way every F~ visited has its rounds-cycle
    # length checked against the theorem: the forbidden lengths never
    # appear, a 36000-fold empirical echo of the parity invariant.
    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    sigma = rings.compose(gp, rings.inverse(gb))
    heads, _ = rings.reachable_rows(m, "pb")
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    P = [idx[rings.compose(h, gp)] for h in H]
    B = [idx[rings.compose(h, gb)] for h in H]
    S = [idx[rings.compose(h, sigma)] for h in H]
    root = idx[rings.rounds(7)]
    orbit, norb = [-1] * n, 0
    for i in range(n):
        if orbit[i] >= 0:
            continue
        j = i
        while orbit[j] < 0:
            orbit[j] = norb
            j = S[j]
        norb += 1

    def rounds_len(mask):
        v, L = root, 0
        while True:
            v = B[v] if (mask >> orbit[v]) & 1 else P[v]
            L += 1
            if v == root:
                return L

    target = ({3, 5, 8, 12} | set(range(15, 358))) - {350, 353, 354, 356}
    frontier = [
        int(bits[::-1], 2) for _, bits in sorted(WHOLE_QSET_TOGGLES.items())
    ]
    visited = set(frontier)
    achieved = {rounds_len(mk) for mk in frontier} | {357}
    gen = 0
    while target - achieved and gen < 3:
        gen += 1
        nxt = []
        for mask in frontier:
            for q in range(72):
                nm = mask ^ (1 << q)
                if nm in visited:
                    continue
                visited.add(nm)
                L = rounds_len(nm)
                assert L in target  # the theorem, checked in passing
                if L not in achieved:
                    achieved.add(L)
                    nxt.append(nm)
                elif len(nxt) < 4000 and gen < 3:
                    nxt.append(nm)
        frontier = nxt
    assert gen == 2 and achieved == target


def test_whole_qset_mirror_invariance_grandsire_triples():
    # The reversal of a whole-Q-set touch is whole-Q-set. NOT because
    # the mirror alpha respects Q-sets — it doesn't: alpha maps the
    # sigma-orbits (Q-sets, sigma = gp.gb^-1) onto the orbits of
    # tau = gp^-1.gb, the REVERSE Q-sets (h plained and h' bobbed
    # collide at their PREDECESSORS iff h' = h.tau), a genuinely
    # different partition into 72 fives. The theorem is the dual of
    # forced-call propagation: the identity tau.gb^-1 = gp^-1 says
    # the bob-predecessor of h.tau IS the plain-predecessor of h, so
    # under any toggle permutation F~ (a whole-Q-set assignment on
    # all 360 heads), if h is fed by its plain predecessor then
    # h.tau's bob predecessor is already spoken for, forcing h.tau
    # to be fed by its plain predecessor too: in-call p propagates
    # forwards and in-call b backwards along each tau-orbit, and
    # each closes around the finite orbit. In-calls are therefore
    # constant on reverse Q-sets; the reversed touch's call at
    # alpha(h) is exactly the in-call of h, and alpha carries
    # tau-orbits back to sigma-orbits — so the reversed calling is
    # whole-Q-set. With the reversal theorem this makes the
    # whole-Q-set spectrum mirror-symmetric level by level, matching
    # its palindromic look ({350,353,354,356} missing at the top,
    # nothing extra at the bottom).
    import random

    m = rings.METHODS["Grandsire Triples"]
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    comp, inv = rings.compose, rings.inverse
    sigma, tau = comp(gp, inv(gb)), comp(inv(gp), gb)
    heads, _ = rings.reachable_rows(m, "pb")
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    P = [idx[comp(h, gp)] for h in H]
    B = [idx[comp(h, gb)] for h in H]
    S = [idx[comp(h, sigma)] for h in H]
    T = [idx[comp(h, tau)] for h in H]
    Pi, Bi = [0] * n, [0] * n
    for i in range(n):
        Pi[P[i]], Bi[B[i]] = i, i
    root = idx[rings.rounds(7)]

    # the dual identity: bob-predecessor of h.tau = plain-pred of h
    assert all(Bi[T[v]] == Pi[v] for v in range(n))

    def orbits_of(M):
        orb, out = [-1] * n, []
        for i in range(n):
            if orb[i] >= 0:
                continue
            o, j = [], i
            while orb[j] < 0:
                orb[j] = len(out)
                o.append(j)
                j = M[j]
            out.append(o)
        return orb, out

    sorb, sorbs = orbits_of(S)
    torb, torbs = orbits_of(T)
    assert len(torbs) == 72 and all(len(o) == 5 for o in torbs)
    t = (1, 2, 5, 7, 3, 6, 4)  # the reversal relabelling
    A = [idx[comp(comp(t, H[v]), inv(t))] for v in range(n)]
    qsets = {frozenset(o) for o in sorbs}
    rev_qsets = {frozenset(o) for o in torbs}
    assert {frozenset(A[v] for v in o) for o in sorbs} == rev_qsets
    assert qsets != rev_qsets  # alpha does NOT respect Q-sets

    random.seed(7)
    masks = [
        [c == "1" for c in bits] for bits in WHOLE_QSET_TOGGLES.values()
    ] + [[random.random() < 0.5 for _ in range(72)] for _ in range(40)]
    for mask in masks:
        F = [B[v] if mask[sorb[v]] else P[v] for v in range(n)]
        Finv = [0] * n
        for i, w in enumerate(F):
            Finv[w] = i
        incall = ["p" if Finv[v] == Pi[v] else "b" for v in range(n)]
        assert all(len({incall[v] for v in o}) == 1 for o in torbs)
        # hence the reversed rounds-cycle calling is whole-Q-set
        v, calling = root, []
        while True:
            calling.append("b" if mask[sorb[v]] else "p")
            v = F[v]
            if v == root:
                break
        v, per = root, {}
        for c in reversed(calling):
            per.setdefault(sorb[v], set()).add(c)
            v = B[v] if c == "b" else P[v]
        assert v == root
        assert all(len(s) == 1 for s in per.values())


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


def test_no_palindromic_long_touches_grandsire_triples():
    # The mirror alpha: h -> t.h.t^-1 (t = (35)(47)) reverses every
    # bobs-only touch, so its fixed points would be PALINDROMIC
    # callings: c == c[::-1] anchored at rounds. A touch of L leads is
    # palindromic iff its head sequence satisfies h_i = alpha(h_{L-i}),
    # i.e. beta(h) := alpha(F(h)) is an involution on the used heads
    # (one fixed point for L odd, none for L even). Since F(h) is
    # h.gp or h.gb and alpha(h.g) = alpha(h).g^-1, beta must pair h
    # with mu_p(h) = alpha(h).gp^-1 or mu_b(h) = alpha(h).gb^-1 —
    # a perfect matching in the mu-graph, whose shape this test pins
    # down mechanically. Consequences (arithmetic below): NO
    # palindromic touch has more than 343 leads. In particular no
    # palindromic 4998 exists: the mirror acts freely on the 4998s of
    # any alpha-invariant complement, so their number is even.
    m = rings.find_method("Grandsire Triples")
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    gpi, gbi = rings.inverse(gp), rings.inverse(gb)
    t = (1, 2, 5, 7, 3, 6, 4)
    ti = rings.inverse(t)
    heads = {rings.rounds(7)}
    stack = [rings.rounds(7)]
    while stack:
        h = stack.pop()
        for g in (gp, gb):
            nh = rings.compose(h, g)
            if nh not in heads:
                heads.add(nh)
                stack.append(nh)
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)

    def conj(h):
        return rings.compose(rings.compose(t, h), ti)

    A = [idx[conj(h)] for h in H]
    MUP = [idx[rings.compose(conj(h), gpi)] for h in H]
    MUB = [idx[rings.compose(conj(h), gbi)] for h in H]
    # mu_p, mu_b are involutions (pairing is symmetric, same call both
    # ways) and alpha(h.g) == alpha(h).g^-1
    assert all(MUP[MUP[i]] == i and MUB[MUB[i]] == i for i in range(n))
    assert A[idx[rings.compose(H[5], gp)]] == idx[
        rings.compose(H[A[5]], gpi)
    ]
    # components of the mu-graph: 32 alternating 10-cycles (loop-free)
    # and 8 paths of 5 with one mu_p-loop end and one mu_b-loop end
    comp_id, comps = [-1] * n, []
    for i in range(n):
        if comp_id[i] >= 0:
            continue
        cset, st = [], [i]
        while st:
            j = st.pop()
            if comp_id[j] >= 0:
                continue
            comp_id[j] = len(comps)
            cset.append(j)
            st.extend([MUP[j], MUB[j]])
        comps.append(cset)
    sizes = sorted(len(c) for c in comps)
    assert sizes == [5] * 8 + [10] * 32
    for c in comps:
        loops_p = [i for i in c if MUP[i] == i]
        loops_b = [i for i in c if MUB[i] == i]
        if len(c) == 10:
            assert not loops_p and not loops_b
        else:
            assert len(loops_p) == 1 and len(loops_b) == 1
    # the 8 alpha-fixed heads all live in DISTINCT 10-components, and
    # alpha sends every 5-component vertex into a 10-component
    afix = [i for i in range(n) if A[i] == i]
    assert len(afix) == 8
    assert len({comp_id[i] for i in afix}) == 8
    assert all(
        len(comps[comp_id[A[i]]]) == 10
        for c in comps if len(c) == 5 for i in c
    )
    # Arithmetic on those facts: beta fixed points need a mu-loop, so
    # every 5-component the complement D misses (or hits evenly) holds
    # at least one unmatched head; a palindromic touch allows at most
    # one, so D hits >= 7 of the eight 5-components oddly. D is
    # alpha-invariant, alpha moves every 5-component vertex to a
    # 10-component and only 8 heads are alpha-fixed, so |D| >= 14; the
    # sign of F = alpha.beta (an L-cycle) then forces the number of
    # alpha-fixed heads in D to be 3 mod 4 for odd L, 2 mod 4 for even
    # L, pushing |D| to >= 17 (odd L) or >= 18 (even L). Hence
    # palindromic touches have at most 343 leads; 344..357 (the 4998!)
    # are impossible, and the reversal pairs the 4998s two by two.
    assert TOUCH_4998 != TOUCH_4998[::-1]
    # the reversed 4998 is nonetheless a (different) true 4998, and
    # short palindromic touches do exist: bbb and ppppp
    for calling in ("bbb", "ppppp"):
        assert calling == calling[::-1]
        rows = rings.touch(m, calling)
        assert rings.is_true(rows) and rows[0] == rows[-1]
    # For the extremal case L = 343 the candidate complements can be
    # classified completely. |D| = 17 forces: exactly seven of the
    # eight 5-components hit exactly once (the untouched one supplies
    # the single beta-fixed point), three alpha-fixed heads removed,
    # plus the alpha-images of the seven. A hit 5-path must keep a
    # perfect matching with no NEW fixed point, so the removed vertex
    # sits at even position 0, 2 or 4 (counted from the mup-loop end),
    # and every 10-component must be hit evenly. Where the images land
    # decides everything:
    paths = {}
    for ci, c in enumerate(comps):
        if len(c) != 5:
            continue
        path = [i for i in c if MUP[i] == i]
        for mu in (MUB, MUP, MUB, MUP):
            path.append(mu[path[-1]])
        paths[ci] = path
    land = {
        ci: {p: comp_id[A[path[p]]] for p in (0, 2, 4)}
        for ci, path in paths.items()
    }
    afix_comps = {comp_id[i] for i in afix}
    pos0 = [land[ci][0] for ci in paths]
    pos2 = [land[ci][2] for ci in paths]
    # pos-0 images land in eight DISTINCT 10-components, disjoint from
    # every other hit component -- an unpaired odd hit, so position 0
    # is never usable
    assert len(set(pos0)) == 8
    assert not set(pos0) & (set(pos2) | afix_comps)
    # pos-2 images pair the 5-components into four pairs, each pair
    # sharing one 10-component; pos-4 images biject onto the eight
    # alpha-fixed-head components. Rounds is alpha-fixed, so the
    # 5-component whose pos-4 image is rounds' own component can never
    # take position 4 (it would delete rounds)
    assert len(set(pos2)) == 4
    assert all(pos2.count(x) == 2 for x in pos2)
    assert {land[ci][4] for ci in paths} == afix_comps
    r = idx[rings.rounds(7)]
    assert A[r] == r
    partner = {}
    for shared in set(pos2):
        a, b = [ci for ci in paths if land[ci][2] == shared]
        partner[a], partner[b] = b, a
    # so a valid complement = an untouched 5-component c0, its pos-2
    # partner forced to position 4, one further whole pair on position
    # 4 (fixing the three removed alpha-fixed heads), the rest on
    # position 2 -- and rounds' component excluded from pos-4 duty:
    # exactly 15 candidate complements survive
    banned = [ci for ci in paths if land[ci][4] == comp_id[r]]
    assert len(banned) == 1
    count = 0
    for c0 in paths:
        if partner[c0] == banned[0]:
            continue
        for pr in {frozenset((a, b)) for a, b in partner.items()}:
            if c0 in pr or banned[0] in pr:
                continue
            pos4set = {partner[c0]} | set(pr)
            D = set()
            for ci in paths:
                if ci == c0:
                    continue
                p = 4 if ci in pos4set else 2
                v = paths[ci][p]
                D |= {v, A[v]}
                if p == 4:
                    D.add([i for i in afix if comp_id[i] == land[ci][4]][0])
            assert len(D) == 17 and r not in D
            assert {A[v] for v in D} == D
            # every component of the mu-graph minus D retains a
            # perfect matching (allowing only loop fixed points):
            # hit components uniquely, untouched ones freely
            nfree = 0
            for ci2, c in enumerate(comps):
                keep = [v for v in c if v not in D]
                ways = _mu_matchings(keep, MUP, MUB)
                assert ways >= 1
                if len(keep) == len(c):
                    assert ways == 2
                    nfree += 1
                else:
                    assert ways == 1
            assert nfree == 28
            count += 1
    assert count == 15
    # THEOREM (exhaustive Gray-code C sweep, 15 x 2^28 matchings,
    # 2026-07-18/19): none of the fifteen complements admits a
    # single-cycle F. NO PALINDROMIC 343 EXISTS, even at the
    # head-cycle level. The palindromic ceiling is < 343.
    #
    # Descending. A palindromic involution has exactly ONE fixed
    # point for odd L (the middle lead), NONE for even L, and a
    # 5-path with an odd-position removal forces BOTH loop ends
    # fixed, so odd positions stay dead:
    for ci, path in paths.items():
        for p, want in ((0, [0]), (1, [2]), (2, [0]), (3, [2]),
                        (4, [0])):
            fx = _mu_match_fixes(
                [v for v in comps[ci] if v != path[p]], MUP, MUB)
            assert fx == want
    # Hence a palindromic 341 needs: seven 5-paths hit once at even
    # positions, one untouched (supplying the fixed point), three
    # alpha-fixed heads (sign, as before: 3 mod 4), and ONE extra
    # alpha-pair {v, alpha(v)} wholly inside 10-components:
    # 7*2 + 3 + 2 = 19. Every 10-component must still be hit evenly.
    # alpha is NOT a mu-graph automorphism: no moved vertex shares a
    # component with its alpha-image, so the extra pair always
    # toggles TWO distinct 10-components and must cancel the hit
    # parity defect T exactly. The pair supply is rigid: 136
    # component-pairs, one vertex pair each
    cross = {}
    for v in range(n):
        av = A[v]
        if av == v:
            continue
        assert comp_id[v] != comp_id[av]
        if av < v or len(comps[comp_id[v]]) != 10 or \
                len(comps[comp_id[av]]) != 10:
            continue
        cross.setdefault(
            frozenset((comp_id[v], comp_id[av])), []).append((v, av))
    assert len(cross) == 136
    assert all(len(x) == 1 for x in cross.values())
    # parity enumeration: T empty would need a same-component pair
    # (none exist -- those 15 survivors are exactly the 343 configs
    # reborn, all dead), T = {X, Y} must be a cross pair
    heads3 = []
    for hs in itertools.combinations(afix, 3):
        if r not in hs:
            heads3.append((hs, frozenset(comp_id[h] for h in hs)))
    survivors = []
    n_t0 = 0
    for c0 in paths:
        others = [ci for ci in paths if ci != c0]
        for pos in itertools.product((0, 2, 4), repeat=7):
            tog = frozenset()
            for ci, p in zip(others, pos):
                tog ^= {land[ci][p]}
            for hs, hc in heads3:
                T = tog ^ hc
                if not T:
                    n_t0 += 1
                elif len(T) == 2 and T in cross:
                    survivors.append((c0, others, pos, hs, T))
    assert n_t0 == 15
    assert len(survivors) == 545
    # matching filter: exactly 125 candidate complements survive,
    # each with 27 free matching bits and total fixed-point count 1
    n341 = 0
    for c0, others, pos, hs, T in survivors:
        v1, v2 = cross[T][0]
        D = {v1, v2} | set(hs)
        for ci, p in zip(others, pos):
            w = paths[ci][p]
            D |= {w, A[w]}
        if len(D) != 19 or r in D:
            continue
        assert {A[v] for v in D} == D
        ok, nfix, nfree = True, 0, 0
        for c in comps:
            fx = _mu_match_fixes([v for v in c if v not in D], MUP, MUB)
            if not fx or len(set(fx)) != 1:
                ok = False
                break
            nfix += fx[0]
            if len(fx) > 1:
                nfree += 1
        if ok and nfix == 1:
            assert nfree == 27
            n341 += 1
    assert n341 == 125
    # THEOREM (exhaustive sweep, 125 x 2^27, 2026-07-19/20): none of
    # the 125 admits a single-cycle F -- NO PALINDROMIC 341 EXISTS.
    #
    # L = 342, |D| = 18, zero fixed points: ALL eight 5-paths hit
    # once at even positions + two alpha-fixed heads, no extra pair.
    # Parity leaves exactly 3 complements (all matching-valid, 27
    # free bits). THEOREM (exhaustive sweep, 3 x 2^27, 2026-07-19):
    # none admits a single-cycle F -- NO PALINDROMIC 342 EXISTS.
    #
    # L = 340, |D| = 20, zero fixed points: all eight 5-paths hit
    # once at even positions + two heads + ONE extra cross pair
    # cancelling the parity defect (T = 0 would need a same-component
    # pair; none exist):
    heads2 = []
    for hs in itertools.combinations(afix, 2):
        if r not in hs:
            heads2.append((hs, frozenset(comp_id[h] for h in hs)))
    surv340 = []
    for pos in itertools.product((0, 2, 4), repeat=8):
        tog = frozenset()
        for ci, p in zip(paths, pos):
            tog ^= {land[ci][p]}
        for hs, hc in heads2:
            T = tog ^ hc
            if len(T) == 2 and T in cross:
                surv340.append((pos, hs, T))
    assert len(surv340) == 102
    n340 = 0
    for pos, hs, T in surv340:
        v1, v2 = cross[T][0]
        D = {v1, v2} | set(hs)
        for ci, p in zip(paths, pos):
            w = paths[ci][p]
            D |= {w, A[w]}
        if len(D) != 20 or r in D:
            continue
        assert {A[v] for v in D} == D
        ok, nfix, nfree = True, 0, 0
        for c in comps:
            fx = _mu_match_fixes([v for v in c if v not in D], MUP, MUB)
            if not fx or len(set(fx)) != 1:
                ok = False
                break
            nfix += fx[0]
            if len(fx) > 1:
                nfree += 1
        if ok and nfix == 0:
            assert nfree == 26
            n340 += 1
    assert n340 == 18
    # THEOREM (exhaustive sweep, 18 x 2^26, 2026-07-20): none of the
    # 18 admits a single-cycle F -- NO PALINDROMIC 340 EXISTS. The
    # palindromic ceiling is <= 339.
    # L = 339, |D| = 21, one fixed point, heads = 3 mod 4 so 3 or 7
    # (only 7 usable): family A = 3 heads + 7 even hits + untouched
    # path + TWO cross pairs jointly cancelling T (|T| in {2, 4};
    # T = 0 forces equal comp-pairs, i.e. the same vertex pair --
    # dead). Family B = all 7 usable heads, no extra pair, T = 0.
    # Enumeration (2026-07-20, /tmp/pal339.py): 10755 A-survivors +
    # exactly ONE B-survivor; matching filter leaves 925 + 1 = 926
    # complements (876 with 26 free bits, 50 with 27).
    # L = 338, |D| = 22, no fixed point, heads 2 or 6: the same
    # two-family split (2 heads + 2 cross pairs / 6 heads + none)
    # gives 1977 + 1 parity survivors and 132 + 1 = 133 complements
    # (121 with 25 free bits, 12 with 26).
    # SWEEP VERDICT (2026-07-21): the 339 sweep (926 x 2^26) and the
    # 338 sweep (133 x 2^25) each produced exactly one FOUND -- and
    # in BOTH cases it was the unique family-B complement (all
    # usable heads, no extra pairs), the last index. Both verified
    # TRUE (see test_palindromic_ceiling_attained_grandsire_triples).
    # With no 340/341/342/343 and nothing above 343, the palindromic
    # ceiling of Grandsire Triples is EXACTLY 339 leads.
    # FULL CENSUS of the two B-configs (all free-bit settings,
    # 2^26 / 2^25, 2026-07-21): exactly 135 single-cycle settings at
    # L = 339 and 226 at L = 338 -- every one a TRUE touch (no
    # falseness ever appeared), every calling distinct. So Grandsire
    # Triples has exactly 135 palindromic 4746s and 226 palindromic
    # 4732s, all sharing their length's unique family-B complement.


def test_palindromic_ceiling_attained_grandsire_triples():
    # The extremal witnesses: true palindromic bobs-only touches of
    # 339 leads (the exact ceiling -- see the sweep theorems in
    # test_no_palindromic_long_touches_grandsire_triples) and 338.
    # Both came from the unique family-B complement of their length:
    # all usable alpha-fixed heads removed, no extra cross pairs.
    m = rings.find_method("Grandsire Triples")
    t = (1, 2, 5, 7, 3, 6, 4)
    ti = rings.inverse(t)
    for calling, nleads, changes in (
        (PAL_4746, 339, 4746),
        (PAL_4732, 338, 4732),
    ):
        assert len(calling) == nleads
        assert calling == calling[::-1]
        rows = rings.touch(m, calling)
        assert rings.is_true(rows)
        assert rows[-1] == rings.rounds(7)
        assert len(rows) - 1 == changes
        # palindromic in the structural sense too: the head sequence
        # satisfies h_i = alpha(h_{L-i}) with alpha = conjugation by
        # t = (35)(47), the row-reversal mirror
        hs = [rows[i * 14] for i in range(nleads)]
        assert all(
            hs[i] == rings.compose(rings.compose(t, hs[-i % nleads]), ti)
            for i in range(nleads)
        )


def test_grandsire_triples_falseness_is_convergence():
    # Why every single-cycle F in the palindrome sweeps verified TRUE
    # (361 out of 361, no exceptions): the ONLY row shared between
    # bobs-only Grandsire Triples leads of distinct heads is the
    # lead-END row (index 13), and h1's b-lead shares it with h2's
    # p-lead exactly when both converge on the SAME next head
    # (h1.gb == h2.gp). A touch visits each head once, so no head has
    # two predecessors: distinct heads => true, automatically. Truth
    # of a bobs-only round block is purely combinatorial.
    m = rings.find_method("Grandsire Triples")
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    heads = {rings.rounds(7)}
    stack = [rings.rounds(7)]
    while stack:
        h = stack.pop()
        for g in (gp, gb):
            nh = rings.compose(h, g)
            if nh not in heads:
                heads.add(nh)
                stack.append(nh)
    assert len(heads) == 360
    occ = {}
    for h in heads:
        for call in "pb":
            rows = rings.touch(m, call)
            assert len(rows) == 15
            for i, r in enumerate(rows[:-1]):
                occ.setdefault(rings.compose(h, r), []).append((h, call, i))
    conv = rings.compose(gb, rings.inverse(gp))
    shared = 0
    for r, slots in occ.items():
        hs = {h for h, c, i in slots}
        if len(hs) == 1:
            continue
        shared += 1
        # exactly two heads, both at index 13, one b one p, converging
        assert len(slots) == 2 and {c for _, c, _ in slots} == {"p", "b"}
        assert all(i == 13 for _, _, i in slots)
        (h1, c1, _), (h2, c2, _) = slots
        hb, hp = (h1, h2) if c1 == "b" else (h2, h1)
        assert rings.compose(hb, gb) == rings.compose(hp, gp)
        assert hp == rings.compose(hb, conv)
    assert shared == 360


def _mu_matchings(verts, MUP, MUB):
    if not verts:
        return 1
    v, rest = verts[0], verts[1:]
    total = 0
    for u in (MUP[v], MUB[v]):
        if u == v:
            total += _mu_matchings(rest, MUP, MUB)
        elif u in rest:
            total += _mu_matchings([x for x in rest if x != u], MUP, MUB)
    return total


def _mu_match_fixes(verts, MUP, MUB):
    # fixed-point count of every matching (one list entry each)
    if not verts:
        return [0]
    v, rest = verts[0], verts[1:]
    out = []
    for u in (MUP[v], MUB[v]):
        if u == v:
            out.extend(f + 1 for f in _mu_match_fixes(rest, MUP, MUB))
        elif u in rest:
            out.extend(_mu_match_fixes(
                [x for x in rest if x != u], MUP, MUB))
    return out


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
