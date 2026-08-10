"""palmitm.py — deep-k family-B search for the last open lengths.

Meet-in-the-middle over cross-pair XORs, reconstructed from the
07-28..08-01 journal notes after the reboot.  For k cross pairs the
survivors of the parity condition are k-subsets of the 136 comp-pairs
XOR-ing to the defect T of a (c0, pos, heads) frame.  Shape (pal321's,
extended): split the 136 keys interleaved into halfA/halfB (68 each),
dictB maps XOR -> quads of halfB (68C4).  k = 9: quints-A x quads-B.
k = 10 (L = 319/318): one folded pair (all 136) reduces T, then the
9-join.  k = 11 (L = 317): two folded pairs.

Usage: python3 palmitm.py <L> [max_cfgs] [settings_cap]
Existence hunt: first single-cycle setting is verified end-to-end and
printed; exit 0.  Progress on stderr.
"""

import itertools
import sys
import time

import palsearch


def build_dictB(keys_b):
    dictB = {}
    nb = len(keys_b)
    for i in range(nb - 3):
        xi = keys_b[i]
        for j in range(i + 1, nb - 2):
            xj = xi ^ keys_b[j]
            for k in range(j + 1, nb - 1):
                xk = xj ^ keys_b[k]
                for l in range(k + 1, nb):
                    dictB.setdefault(xk ^ keys_b[l], []).append(
                        (i, j, k, l))
    return dictB


def nonets(target, keys_a, dictB, keys_b, cap):
    """9-subsets: quints of halfA x quads of halfB XOR-ing to target."""
    out = []
    na = len(keys_a)
    for a in range(na - 4):
        xa = target ^ keys_a[a]
        for b in range(a + 1, na - 3):
            xb = xa ^ keys_a[b]
            for c in range(b + 1, na - 2):
                xc = xb ^ keys_a[c]
                for d in range(c + 1, na - 1):
                    xd = xc ^ keys_a[d]
                    for e in range(d + 1, na):
                        quads = dictB.get(xd ^ keys_a[e])
                        if not quads:
                            continue
                        quint = (keys_a[a], keys_a[b], keys_a[c],
                                 keys_a[d], keys_a[e])
                        for q in quads:
                            out.append(quint + tuple(
                                keys_b[i] for i in q))
                            if len(out) >= cap:
                                return out
    return out


def ksets(target, k, keys, keys_a, dictB, keys_b, cap):
    """k-subsets (k in 9..11) of all 136 keys XOR-ing to target, via
    0..2 folded loose pairs + the 5x4 MITM nonet join."""
    if k == 9:
        return nonets(target, keys_a, dictB, keys_b, cap)
    out = []
    for fold in itertools.combinations(keys, k - 9):
        t2 = target
        for f in fold:
            t2 ^= f
        for nine in nonets(t2, keys_a, dictB, keys_b, cap):
            if any(f in nine for f in fold):
                continue
            out.append(tuple(fold) + nine)
            if len(out) >= cap:
                return out
    return out


def hunt(L, max_cfgs=400, settings_cap=300000, decet_cap=64):
    g = palsearch.build()
    odd = L % 2 == 1
    k = ((339 if odd else 338) - L) // 2
    keys = sorted(g.cross, key=sorted)
    keys_a, keys_b = keys[0::2], keys[1::2]
    t0 = time.time()
    dictB = build_dictB(keys_b)
    print(f"dictB {len(dictB)} keys {time.time()-t0:.1f}s",
          file=sys.stderr, flush=True)
    path_ids = sorted(g.paths)
    if odd:
        head_choices = [tuple(g.usable)]
        c0_choices = path_ids
    else:
        head_choices = list(itertools.combinations(g.usable, 6))
        c0_choices = [None]
    want_fix = 1 if odd else 0
    seen, ncfg = set(), 0
    for c0 in c0_choices:
        hit_paths = [ci for ci in path_ids if ci != c0]
        for pos in itertools.product((0, 2, 4), repeat=len(hit_paths)):
            for hs in head_choices:
                target = frozenset()
                for ci, p in zip(hit_paths, pos):
                    target ^= {g.land[ci][p]}
                for h in hs:
                    target ^= {g.comp_id[h]}
                for combo in ksets(target, k, keys, keys_a, dictB,
                                   keys_b, decet_cap):
                    if len(set(combo)) != k:
                        continue
                    D = set(hs)
                    for ci, p in zip(hit_paths, pos):
                        w = g.paths[ci][p]
                        D |= {w, g.A[w]}
                    for key in combo:
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
                        ms = palsearch.matchings(keep, g.MUP, g.MUB)
                        if not ms or len({f for _, f in ms}) != 1:
                            ok = False
                            break
                        nfix += ms[0][1]
                        options.append(ms)
                    if not ok or nfix != want_fix:
                        continue
                    ncfg += 1
                    for calling in palsearch.sweep(
                            g, L, options, limit=settings_cap):
                        palsearch.verify(g, calling)
                        print(f"L={L} FOUND cfg{ncfg} {calling}",
                              flush=True)
                        return calling
                    print(f"cfg{ncfg} empty "
                          f"({time.time()-t0:.0f}s)",
                          file=sys.stderr, flush=True)
                    if ncfg >= max_cfgs:
                        print(f"L={L} exhausted {ncfg} cfgs",
                              flush=True)
                        return None
    print(f"L={L} no cfgs left", flush=True)
    return None


if __name__ == "__main__":
    L = int(sys.argv[1])
    max_cfgs = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 300000
    r = hunt(L, max_cfgs, cap)
    sys.exit(0 if r else 1)
