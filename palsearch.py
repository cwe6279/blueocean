"""palsearch.py — family-B palindromic-touch machinery, Grandsire Triples.

Reconstructed 2026-08-10 after a host reboot wiped /tmp, where every
solver script since 07-20 had lived (pal339..pal317, harvest, verify,
encode).  The theory survives in test_no_palindromic_long_touches_
grandsire_triples; this module makes the machinery durable.

Structure (see the test for proofs).  The 360 reachable lead heads H
carry two involutions mu_p(h) = alpha(h).gp^-1 and mu_b(h) =
alpha(h).gb^-1 (alpha = conjugation by t = (35)(47), the row-reversal
mirror).  A palindromic touch of L leads is exactly: an alpha-invariant
complement D (|D| = 360 - L, rounds not in D) plus a perfect matching
of the mu-graph on H \\ D whose loop-fixed-point count is 1 for odd L
and 0 for even L, such that the induced successor F (call at h = the
matching edge's flavour) is a single L-cycle.  Truth is automatic
(falseness-is-convergence).

The mu-graph is 32 ten-cycles + 8 five-paths.  Family B complements:
  odd L:  all 7 usable alpha-fixed heads, one untouched 5-path (the
          fixed point), the other 7 paths hit once at an even position,
          plus k = (339 - L) // 2 cross pairs;
  even L: 6 of the 7 usable heads, all 8 paths hit at even positions,
          plus k = (338 - L) // 2 cross pairs.
The k cross pairs are drawn from the 136 component-pairs (one vertex
pair {v, alpha(v)} each) and must XOR (as sets of hit 10-components)
to the parity defect of the pos-vector + head choice.
"""

import itertools

import rings


class G:
    pass


def build():
    g = G()
    m = rings.find_method("Grandsire Triples")
    g.method = m
    gp, gb = rings.head_perm(m, "p"), rings.head_perm(m, "b")
    g.gp, g.gb = gp, gb
    gpi, gbi = rings.inverse(gp), rings.inverse(gb)
    t = (1, 2, 5, 7, 3, 6, 4)
    ti = rings.inverse(t)
    heads = {rings.rounds(7)}
    stack = [rings.rounds(7)]
    while stack:
        h = stack.pop()
        for gg in (gp, gb):
            nh = rings.compose(h, gg)
            if nh not in heads:
                heads.add(nh)
                stack.append(nh)
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    g.H, g.idx, g.n = H, idx, n

    def conj(h):
        return rings.compose(rings.compose(t, h), ti)

    g.A = [idx[conj(h)] for h in H]
    g.MUP = [idx[rings.compose(conj(h), gpi)] for h in H]
    g.MUB = [idx[rings.compose(conj(h), gbi)] for h in H]
    g.FP = [idx[rings.compose(h, gp)] for h in H]
    g.FB = [idx[rings.compose(h, gb)] for h in H]
    g.r = idx[rings.rounds(7)]

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
            st.extend([g.MUP[j], g.MUB[j]])
        comps.append(cset)
    g.comps, g.comp_id = comps, comp_id

    g.afix = [i for i in range(n) if g.A[i] == i]
    g.usable = [i for i in g.afix if i != g.r]

    paths = {}
    for ci, c in enumerate(comps):
        if len(c) != 5:
            continue
        path = [i for i in c if g.MUP[i] == i]
        for mu in (g.MUB, g.MUP, g.MUB, g.MUP):
            path.append(mu[path[-1]])
        paths[ci] = path
    g.paths = paths
    g.land = {
        ci: {p: comp_id[g.A[path[p]]] for p in (0, 2, 4)}
        for ci, path in paths.items()
    }

    cross = {}
    for v in range(n):
        av = g.A[v]
        if av == v or av < v:
            continue
        if len(comps[comp_id[v]]) != 10 or len(comps[comp_id[av]]) != 10:
            continue
        key = frozenset((comp_id[v], comp_id[av]))
        assert key not in cross
        cross[key] = (v, av)
    assert len(cross) == 136
    g.cross = cross
    return g


def matchings(verts, MUP, MUB):
    """All perfect matchings (mu-loops allowed) of `verts`, each as
    (calls dict v -> 'p'/'b', fixed point count)."""
    if not verts:
        return [({}, 0)]
    v, rest = verts[0], verts[1:]
    out = []
    for u, call in ((MUP[v], "p"), (MUB[v], "b")):
        if u == v:
            for d, f in matchings(rest, MUP, MUB):
                d2 = dict(d)
                d2[v] = call
                out.append((d2, f + 1))
        elif u in rest:
            for d, f in matchings([x for x in rest if x != u], MUP, MUB):
                d2 = dict(d)
                d2[v] = call
                d2[u] = call
                out.append((d2, f))
    return out


def xor_table(g, k):
    """dict: XOR of component sets -> list of k-subsets of the 136
    cross comp-pairs achieving it.  C(136, k) entries; fine for
    k <= 3, deeper Ls need the MITM joins (to be reconstructed)."""
    if not hasattr(g, "_xt"):
        g._xt = {}
    if k in g._xt:
        return g._xt[k]
    keys = sorted(g.cross, key=sorted)
    table = {}
    for combo in itertools.combinations(keys, k):
        acc = frozenset()
        for key in combo:
            acc ^= key
        table.setdefault(acc, []).append(list(combo))
    g._xt[k] = table
    return table


def _pairs_dict(g):
    """(keys, masks, dict XOR-mask -> list of index pairs) over the
    136 cross comp-pair keys; built once."""
    if not hasattr(g, "_pd"):
        keys = sorted(g.cross, key=sorted)
        mask = [sum(1 << c for c in key) for key in keys]
        pd = {}
        for i in range(len(keys) - 1):
            mi = mask[i]
            for j in range(i + 1, len(keys)):
                pd.setdefault(mi ^ mask[j], []).append((i, j))
        g._pd = (keys, mask, pd)
    return g._pd


def ksubsets(g, k, target):
    """All k-subsets of the cross comp-pair keys XOR-ing (as sets of
    hit 10-components) to `target`.  Full table for k <= 3; k = 4 by
    meet-in-the-middle over pair XORs (C(136,4) ~ 13.6M would not fit
    in RAM as a table).  Each quad arises from three pair-splittings,
    deduped via canonical sorted tuples."""
    if k <= 3:
        return xor_table(g, k).get(target, [])
    assert k == 4, "k >= 5 needs the palmitm joins"
    keys, mask, pd = _pairs_dict(g)
    tm = 0
    for c in target:
        tm |= 1 << c
    out = set()
    for x, ps in pd.items():
        y = tm ^ x
        if y < x:
            continue
        qs = pd.get(y)
        if not qs:
            continue
        if y == x:
            combos = [(p, q) for ii, p in enumerate(ps)
                      for q in ps[ii + 1:]]
        else:
            combos = [(p, q) for p in ps for q in qs]
        for (a, b), (c, d) in combos:
            if a != c and a != d and b != c and b != d:
                out.add(tuple(sorted((a, b, c, d))))
    return [[keys[i] for i in quad] for quad in sorted(out)]


def family_b_complements(g, L):
    """Yield family-B complements for lead count L as
    (D frozenset, options list-of-matching-lists, meta dict).
    `options` has one entry per mu-component: the list of (calls, nfix)
    matchings of that component minus D.  Complements failing the
    matching filter (some component unmatched, or mixed / wrong total
    fixed count) are skipped."""
    odd = L % 2 == 1
    k = ((339 if odd else 338) - L) // 2
    assert k >= 0
    want_fix = 1 if odd else 0
    path_ids = sorted(g.paths)
    if odd:
        head_choices = [tuple(g.usable)]
        c0_choices = path_ids
    else:
        head_choices = list(itertools.combinations(g.usable, 6))
        c0_choices = [None]
    seen = set()
    for c0 in c0_choices:
        hit = [ci for ci in path_ids if ci != c0]
        for pos in itertools.product((0, 2, 4), repeat=len(hit)):
            tog = frozenset()
            for ci, p in zip(hit, pos):
                tog ^= {g.land[ci][p]}
            for hs in head_choices:
                target = tog
                for h in hs:
                    target ^= {g.comp_id[h]}
                for pairs in ksubsets(g, k, target):
                    D = set(hs)
                    for ci, p in zip(hit, pos):
                        w = g.paths[ci][p]
                        D |= {w, g.A[w]}
                    for key in pairs:
                        v, av = g.cross[key]
                        D |= {v, av}
                    if len(D) != 360 - L or g.r in D:
                        continue
                    Df = frozenset(D)
                    if Df in seen:
                        continue
                    seen.add(Df)
                    if {g.A[v] for v in D} != D:
                        continue
                    options, nfix, ok = [], 0, True
                    for c in g.comps:
                        keep = [v for v in c if v not in D]
                        ms = matchings(keep, g.MUP, g.MUB)
                        if not ms or len({f for _, f in ms}) != 1:
                            ok = False
                            break
                        nfix += ms[0][1]
                        options.append(ms)
                    if not ok or nfix != want_fix:
                        continue
                    yield Df, options, {
                        "c0": c0, "pos": pos, "heads": hs,
                        "pairs": pairs,
                    }


def sweep(g, L, options, cap=None, limit=None):
    """Iterate free-bit settings of one complement; yield the calling
    string of every single-cycle F.  Stops after `cap` hits or after
    examining `limit` settings."""
    found = tried = 0
    succ = [-1] * g.n
    call_of = [""] * g.n
    free = []
    for ms in options:
        if len(ms) == 1:
            for v, c in ms[0][0].items():
                succ[v] = g.FP[v] if c == "p" else g.FB[v]
                call_of[v] = c
        else:
            free.append([
                [(v, g.FP[v] if c == "p" else g.FB[v], c)
                 for v, c in d.items()]
                for d, _ in ms
            ])
    r = g.r
    for combo in itertools.product(*free):
        tried += 1
        if limit is not None and tried > limit:
            return
        for patch in combo:
            for v, s, c in patch:
                succ[v] = s
                call_of[v] = c
        v, steps = r, 0
        while True:
            v = succ[v]
            steps += 1
            if v == r or steps > L:
                break
        if v == r and steps == L:
            out, v = [], r
            for _ in range(L):
                out.append(call_of[v])
                v = succ[v]
            yield "".join(out)
            found += 1
            if cap is not None and found >= cap:
                return


def _census_bin():
    """Compile palcensus.c (once) and return the binary path."""
    import os
    import subprocess

    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "palcensus.c")
    exe = "/tmp/palcensus"
    if (not os.path.exists(exe)
            or os.path.getmtime(exe) < os.path.getmtime(src)):
        subprocess.run(["gcc", "-O2", "-o", exe, src], check=True)
    return exe


def _count_settings_c(g, L, options, exe):
    """Count single-cycle settings of one complement via the C
    sweeper.  Same semantics as len(list(sweep(g, L, options)))."""
    import subprocess

    base = [-1] * g.n
    free = []
    for ms in options:
        opts = [
            sorted((v, g.FP[v] if c == "p" else g.FB[v])
                   for v, c in d.items())
            for d, _ in ms
        ]
        if len(ms) == 1:
            for v, s in opts[0]:
                base[v] = s
        else:
            assert len(ms) <= 16 and len(opts[0]) <= 12
            free.append(opts)
    lines = [f"{L} {g.r}", " ".join(map(str, base)), str(len(free))]
    for opts in free:
        lines.append(f"{len(opts)} {len(opts[0])}")
        for patch in opts:
            lines.extend(f"{v} {s}" for v, s in patch)
    out = subprocess.run([exe], input="\n".join(lines) + "\n",
                         capture_output=True, text=True, check=True)
    return int(out.stdout)


def census(g, L, log=None, use_c=True):
    """Exact census: sweep EVERY family-B complement of L uncapped,
    return (total single-cycle settings, complement count, nonzero
    complement count).  Progress lines to `log` (a writable stream).
    With use_c the per-complement count runs in the compiled C
    sweeper (~40x); the pure-Python sweep is the fallback."""
    import time

    exe = _census_bin() if use_c else None
    t0 = time.time()
    total = ncfg = nonzero = 0
    for D, options, meta in family_b_complements(g, L):
        ncfg += 1
        if exe:
            n = _count_settings_c(g, L, options, exe)
        else:
            n = sum(1 for _ in sweep(g, L, options))
        total += n
        if n:
            nonzero += 1
        if log:
            print(f"cfg{ncfg} {n} total={total} "
                  f"({time.time()-t0:.0f}s)", file=log, flush=True)
    if log:
        print(f"L={L} census EXACT {total} over {ncfg} complements "
              f"({nonzero} nonzero) in {time.time()-t0:.0f}s",
              file=log, flush=True)
    return total, ncfg, nonzero


def verify(g, calling):
    """End-to-end check: true, closes at rounds, palindromic, right
    length."""
    L = len(calling)
    assert calling == calling[::-1]
    rows = rings.touch(g.method, calling)
    assert rings.is_true(rows)
    assert rows[-1] == rings.rounds(7)
    assert len(rows) - 1 == 14 * L
    return True


if __name__ == "__main__":
    import sys

    g = build()
    if sys.argv[1] == "census":
        L = int(sys.argv[2])
        census(g, L, log=sys.stdout)
        sys.exit(0)
    L = int(sys.argv[1])
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    for D, options, meta in family_b_complements(g, L):
        for calling in sweep(g, L, options, cap=cap):
            verify(g, calling)
            print(f"L={L} FOUND {calling}", flush=True)
            sys.exit(0)
    print(f"L={L} none found", flush=True)
    sys.exit(1)
