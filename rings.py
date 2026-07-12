"""rings.py — a small change-ringing engine.

Change ringing is the English art of ringing tower bells in permutations
("rows") that never repeat. A "method" is described by place notation:
a compact string saying, for each change, which places hold still while
every other adjacent pair of bells swaps.

This module parses place notation, generates plain courses, and checks
truth (no repeated rows). Pure Python, no dependencies.

Vocabulary:
  row     — a permutation of the bells, e.g. (2, 1, 4, 3)
  rounds  — the identity row (1, 2, ..., n)
  change  — a set of places that stay fixed; all other adjacent pairs swap
  lead    — one pass through a method's place notation
  course  — leads repeated until rounds comes back
  true    — all rows distinct
  extent  — a true composition containing every possible row (n! rows)
"""

from itertools import count

BELL_SYMBOLS = "1234567890ETABCDFGHJKLMNPQRSUVWYZ"

STAGE_NAMES = {
    3: "Singles", 4: "Minimus", 5: "Doubles", 6: "Minor",
    7: "Triples", 8: "Major", 9: "Caters", 10: "Royal",
    11: "Cinques", 12: "Maximus",
}


def bell_char(bell):
    return BELL_SYMBOLS[bell - 1]


def bell_from_char(ch):
    idx = BELL_SYMBOLS.find(ch.upper())
    if idx < 0:
        raise ValueError(f"unknown bell symbol {ch!r}")
    return idx + 1


def rounds(n):
    return tuple(range(1, n + 1))


def row_str(row):
    return "".join(bell_char(b) for b in row)


def tokenize(notation):
    """Split place notation into tokens: 'x' (cross) or a tuple of places."""
    tokens = []
    current = ""

    def flush():
        nonlocal current
        if current:
            tokens.append(tuple(sorted(bell_from_char(c) for c in current)))
            current = ""

    for ch in notation.replace("-", "x").replace("X", "x"):
        if ch == ".":
            flush()
        elif ch == "x":
            flush()
            tokens.append("x")
        elif ch.isspace():
            flush()
        else:
            current += ch
    flush()
    return tokens


def parse(notation):
    """Expand place notation into a list of changes (one per row of a lead).

    Supports the symmetric shorthand with a comma: 'x14x14,12' means the
    first block is rung forwards then backwards (palindrome about its last
    change), followed by the second block treated the same way.
    """
    changes = []
    for block in notation.split(","):
        tokens = tokenize(block)
        if not tokens:
            continue
        if "," in notation:
            tokens = tokens + tokens[-2::-1]
        changes.extend(tokens)
    return changes


def apply_change(row, change):
    """Apply one change to a row. Fixed places keep their bell; every other
    adjacent pair swaps. Implicit places are inferred when a swap is
    impossible (the standard convention for odd stages)."""
    n = len(row)
    out = list(row)
    fixed = set() if change == "x" else set(change)
    i = 1
    while i <= n:
        if i in fixed:
            i += 1
        elif i + 1 <= n and (i + 1) not in fixed:
            out[i - 1], out[i] = out[i], out[i - 1]
            i += 2
        else:
            i += 1  # implicit place
    return tuple(out)


def lead(row, changes):
    """Ring one lead from `row`; yields each successive row."""
    for change in changes:
        row = apply_change(row, change)
        yield row


class Method:
    """A named method: place notation plus its standard calls.

    `notation` is a string, or a list of strings — *blocks* that cycle,
    one calling position per block. Most methods are one block (a lead);
    Stedman is two (its sixes, cut at the call sites), because its single
    replaces a different change in each: 345 mid slow six, 145 mid quick.

    A call is itself a scrap of place notation that replaces the same
    number of changes at the *end* of a block. E.g. a Plain Bob bob '14'
    replaces the lead-end '12'; a Grandsire bob '3.1' replaces '5.1'.
    Where a call differs by block, give a list, one entry per block.
    """

    def __init__(self, name, notation, stage, calls=None):
        self.name = name
        self.notation = notation
        self.stage = stage
        blocks = [notation] if isinstance(notation, str) else list(notation)
        self.blocks = [parse(b) for b in blocks]
        self.changes = [c for b in self.blocks for c in b]
        self.calls = {
            k: [parse(t) for t in ([v] * len(self.blocks) if isinstance(v, str) else v)]
            for k, v in (calls or {}).items()
        }

    def lead_changes(self, call="p", block=0):
        i = block % len(self.blocks)
        changes = self.blocks[i]
        if call == "p":
            return changes
        tail = self.calls[call][i]
        return changes[: -len(tail)] + tail


METHODS = {
    m.name: m
    for m in [
        Method("Plain Bob Minimus", "x14x14,12", 4, {"b": "14", "s": "1234"}),
        Method("Plain Bob Doubles", "5.1.5.1.5,125", 5, {"b": "145", "s": "123"}),
        Method("Plain Bob Minor", "x16x16x16,12", 6, {"b": "14", "s": "1234"}),
        Method("Grandsire Doubles", "3,1.5.1.5.1", 5, {"b": "3.1", "s": "3.123"}),
        Method(
            "Grandsire Triples",
            "3,1.7.1.7.1.7.1",
            7,
            {"b": "3.1", "s": "3.123"},
        ),
        Method(
            "Cambridge Surprise Minor",
            "x36x14x12x36x14x56,12",
            6,
            {"b": "14", "s": "1234"},
        ),
        Method(
            "Stedman Doubles",
            ["3.1.5.3.1.3", "1.3.5.1.3.1"],
            5,
            {"s": ["345", "145"]},
        ),
    ]
}


def find_method(name):
    for m in METHODS.values():
        if m.name.lower() == name.lower():
            return m
    return None


def touch(method, calling):
    """Ring one block per character of `calling`: 'p' plain, 'b' bob,
    's' single. Returns the rows rung, starting from rounds."""
    row = rounds(method.stage)
    rows = [row]
    for i, call in enumerate(calling.replace(" ", "").lower()):
        for r in lead(row, method.lead_changes(call, i)):
            rows.append(r)
        row = rows[-1]
    return rows


def search_extents(method, calls="pb", limit=None, target=None):
    """Depth-first search for callings (one call per lead) whose touch is a
    true round block of exactly `target` rows (default n!: an extent).
    Returns the list of calling strings found (rotations count
    separately)."""
    start = rounds(method.stage)
    target = target or factorial(method.stage)
    found = []

    def dfs(row, seen, calling):
        if limit is not None and len(found) >= limit:
            return
        for c in calls:
            lead_rows = list(lead(row, method.lead_changes(c, len(calling))))
            head = lead_rows[-1]
            body = lead_rows[:-1]
            if len(set(lead_rows)) != len(lead_rows):
                continue
            if any(r in seen for r in body):
                continue
            if head == start:
                if len(seen) + len(body) == target:
                    found.append(calling + c)
                continue
            if head in seen or len(seen) + len(lead_rows) > target:
                continue
            dfs(head, seen | set(lead_rows), calling + c)

    dfs(start, {start}, "")
    return found


def reachable_rows(method, calls="pb"):
    """All lead heads, and all rows, that any touch of `method` using
    only `calls` could ever contain: the union of the leads rung from
    every reachable head. Returns (heads, rows) as sets.

    This bounds every true touch, and the bound bites: Plain Bob Minor
    with bobs only reaches just 360 of the 720 rows, and Grandsire
    Doubles with bobs only just 60 of the 120 — the head group and the
    lead's tail permutations together span only half the extent. Both
    famous 'no bobs-only extent' facts are reachability facts. Grandsire
    Triples, by contrast, reaches all 5040 rows bobs-only; Thompson's
    1886 impossibility proof is about how leads can be joined, which is
    why it needed a real argument — see qset_parity_certificate."""
    start = rounds(method.stage)
    nblocks = len(method.blocks)
    seen, rows = set(), set()
    stack = [(start, 0)]
    while stack:
        h, i = stack.pop()
        if (h, i) in seen:
            continue
        seen.add((h, i))
        rows.add(h)
        for c in calls:
            body = list(lead(h, method.lead_changes(c, i)))
            rows.update(body[:-1])
            stack.append((body[-1], (i + 1) % nblocks))
    return {h for h, i in seen}, rows


def compose(a, b):
    """Compose permutations as rows: compose(h, g) is the row reached by
    applying to h whatever took rounds to g. (h∘g)[i] = h[g[i]-1]."""
    return tuple(a[i - 1] for i in b)


def inverse(g):
    out = [0] * len(g)
    for i, v in enumerate(g):
        out[v - 1] = i + 1
    return tuple(out)


def head_perm(method, call="p"):
    """The lead-head permutation g of a single-block method rung with
    `call`: one lead sends head h to compose(h, g)."""
    if len(method.blocks) != 1:
        raise ValueError("head_perm needs a single-block method")
    return tuple(lead(rounds(method.stage), method.lead_changes(call)))[-1]


def qset_parity_certificate(method, call="b"):
    """Thompson's Q-set parity argument (1886), with every hypothesis
    checked mechanically rather than assumed.

    Setting: touches of `method` using plain and `call` only. Let gp, gb
    be the two lead-head permutations and H the heads reachable from
    rounds. An extent has n!/lead_len leads whose heads are distinct
    rows in H; IF that count equals |H|, every head is used exactly
    once, so 'next head' is a permutation F of H — and a one-round-block
    extent makes F a single |H|-cycle.

    Truth forces calls in whole Q-sets: F(h1) = F(h2) with h1 bobbed,
    h2 plained means h1 = sigma(h2) for sigma = gp.gb^-1, so the plained
    heads are closed under sigma — a union of sigma-orbits (Q-sets).
    Hence F is the plain map composed with one |Q|-cycle per bobbed
    Q-set. IF every |Q| is odd, those cycles are even permutations, so
    the parity of F's cycle count equals that of the plain map's — and
    a single cycle needs it odd.

    Returns the computed facts; 'extent_impossible' is True only when
    all hypotheses verify. For Grandsire Triples bobs-only: |H| = 360 =
    extent leads, 72 Q-sets of size 5 (sigma is conjugate to the
    5-cycle pi7.pi3), 72 plain courses — even, so no bobs-only extent
    exists. This is Thompson's 1886 theorem, proved."""
    gp = head_perm(method, "p")
    gb = head_perm(method, call)
    sigma = compose(gp, inverse(gb))
    start = rounds(method.stage)
    heads = {start}
    stack = [start]
    while stack:
        h = stack.pop()
        for g in (gp, gb):
            nh = compose(h, g)
            if nh not in heads:
                heads.add(nh)
                stack.append(nh)

    def orbit_sizes(g):
        sizes, seen = [], set()
        for h in heads:
            if h in seen:
                continue
            size, x = 0, h
            while x not in seen:
                seen.add(x)
                x = compose(x, g)
                size += 1
            sizes.append(size)
        return sizes

    qset_sizes = orbit_sizes(sigma)
    plain_cycles = len(orbit_sizes(gp))
    extent_leads, rem = divmod(factorial(method.stage), len(method.changes))
    return {
        "heads": len(heads),
        "extent_leads": extent_leads,
        "qsets": len(qset_sizes),
        "qset_sizes": sorted(set(qset_sizes)),
        "plain_cycles": plain_cycles,
        "extent_impossible": (
            rem == 0
            and extent_leads == len(heads)
            and all(s % 2 for s in qset_sizes)
            and plain_cycles % 2 == 0
        ),
    }


def qset_deficit_certificate(method, call="b", missing=1):
    """The Q-set machinery sharpened to near-extents: can a true round
    block fall exactly `missing` leads short of the extent?

    Hypotheses as in qset_parity_certificate (reachable heads == extent
    leads, all Q-sets odd), else {'applicable': False}. Then a block of
    extent_leads - missing leads rings that many distinct heads, and its
    successor map F is a single cycle on the used heads. Necessary facts:

      * nothing may ring into a missing head m: its plain predecessor,
        if used, is bobbed, and its bob predecessor plained;
      * F injective forbids a plained h with sigma(h) bobbed, so plain
        propagates forwards and bob backwards along each Q-set.

    Left-multiplying by the inverse of a missing head is a relabelling
    that keeps the method, calls and truth and moves that head to
    rounds, so fixing rounds missing and looping the rest is exhaustive.
    Each configuration then either dies of a forced-call contradiction;
    dies of parity — adjoining the missing heads as fixed points makes a
    permutation F~ of all heads that a block would give 1 + missing
    cycles, yet every consistent assignment is the forced baseline plus
    whole-Q-set toggles, and a toggle multiplies F~ by a |Q|-cycle (even
    when |Q| is odd), so the cycle-count parity of the baseline is an
    invariant — or stays open (the certificate is silent; head-level
    necessary conditions cannot refute such a block).

    Grandsire Triples bobs-only: missing 0 is Thompson's theorem again
    (parity); missing 1 and 2 die entirely of forced contradictions —
    no 5026, no 5012 — and missing 3 leaves exactly ONE open
    configuration, the bob course through rounds, which the known 4998
    realises. So 4998 is the longest bobs-only round block, and its
    complement is a single bob course, uniquely up to relabelling."""
    from itertools import combinations

    gp = head_perm(method, "p")
    gb = head_perm(method, call)
    sigma = compose(gp, inverse(gb))
    start = rounds(method.stage)
    heads = {start}
    stack = [start]
    while stack:
        h = stack.pop()
        for g in (gp, gb):
            nh = compose(h, g)
            if nh not in heads:
                heads.add(nh)
                stack.append(nh)
    extent_leads, rem = divmod(factorial(method.stage), len(method.changes))
    if rem or extent_leads != len(heads):
        return {"applicable": False}
    H = sorted(heads)
    idx = {h: i for i, h in enumerate(H)}
    n = len(H)
    P = [idx[compose(h, gp)] for h in H]
    B = [idx[compose(h, gb)] for h in H]
    S = [idx[compose(h, sigma)] for h in H]
    Pi, Bi, Si = [0] * n, [0] * n, [0] * n
    for i in range(n):
        Pi[P[i]], Bi[B[i]], Si[S[i]] = i, i, i
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
    if not all(len(o) % 2 for o in orbits):
        return {"applicable": False}
    root = idx[start]
    combos = (
        [()] if missing == 0
        else combinations([i for i in range(n) if i != root], missing - 1)
    )
    target, nconfigs = 1 + missing, 0
    tallies = {"forced": 0, "parity": 0}
    open_configs = []
    for rest in combos:
        nconfigs += 1
        miss = {root, *rest} if missing else set()
        calls, work, conflict = {}, [], False
        seeds = [(Pi[m], 1) for m in miss] + [(Bi[m], 0) for m in miss]
        while (seeds or work) and not conflict:
            h, c = (work or seeds).pop()
            if h in miss:
                continue
            prev = calls.get(h)
            if prev is None:
                calls[h] = c
                work.append((S[h] if c == 0 else Si[h], c))
            elif prev != c:
                conflict = True
        if conflict:
            tallies["forced"] += 1
            continue
        touched = {orbit[m] for m in miss} | {orbit[h] for h in calls}
        free_ok = all(
            x in miss or x in calls for oi in touched for x in orbits[oi]
        )
        F = [i if i in miss else (B[i] if calls.get(i) else P[i])
             for i in range(n)]
        cycles, done = 0, [False] * n
        for i in range(n):
            if done[i]:
                continue
            cycles += 1
            while not done[i]:
                done[i] = True
                i = F[i]
        if free_ok and len(set(F)) == n and cycles % 2 != target % 2:
            tallies["parity"] += 1
        else:
            open_configs.append(tuple(H[i] for i in sorted(miss)))
    return {
        "applicable": True,
        "missing": missing,
        "configs": nconfigs,
        "forced": tallies["forced"],
        "parity": tallies["parity"],
        "open_configs": open_configs,
        "block_impossible": not open_configs,
    }


def lead_multiplicity(method, calls="pb"):
    """In how many reachable leads does each reachable row lie? A lead
    from head h 'owns' h and every later row before the next head; this
    counts, for each reachable row, the heads owning it under any of
    `calls`, returning {multiplicity: number of rows}.

    Where calls differ only in the final change (Plain Bob, Cambridge)
    the leads from a head own the same rows and the multiplicity is
    uniformly 2 — the treble passes each place twice per lead — except
    at Minimus, where a lead is half the extent and multiplicity is 1.
    Grandsire's calls differ a change earlier, so a head owns two
    variants of its penultimate row and the picture shifts: bobs-only
    Grandsire Triples has multiplicity 1 almost everywhere — a head
    lies in no lead but its own, and only the non-head treble-lead
    rows are shared — so leads nearly partition the extent, which is
    why an extent must use every reachable head exactly once (the
    hypothesis qset_parity_certificate leans on)."""
    if len(method.blocks) != 1:
        raise ValueError("lead_multiplicity needs a single-block method")
    heads, rows = reachable_rows(method, calls)
    owners = {r: set() for r in rows}
    for h in heads:
        owners[h].add(h)
        for c in calls:
            for r in list(lead(h, method.lead_changes(c)))[:-1]:
                owners[r].add(h)
    counts = {}
    for owning in owners.values():
        counts[len(owning)] = counts.get(len(owning), 0) + 1
    return counts


def rotation_classes(callings):
    """Group calling strings that are rotations of one another: the same
    cyclic composition started at a different point. Returns a dict of
    canonical (lexicographically least) rotation -> members found."""
    classes = {}
    for c in callings:
        canon = min(c[i:] + c[:i] for i in range(len(c)))
        classes.setdefault(canon, []).append(c)
    return classes


def reversal_classes(callings):
    """Group callings that are rotations or reversals of one another.
    Ringing a touch of a palindromic method backwards reverses its
    calling string (up to rotation), so this classifies compositions up
    to rotation and reversal. Canonical form -> members found."""
    classes = {}
    for c in callings:
        canon = min(
            w[i:] + w[:i] for w in (c, c[::-1]) for i in range(len(w))
        )
        classes.setdefault(canon, []).append(c)
    return classes


def course(method):
    """Ring a method's plain blocks until rounds returns at the end of a
    full cycle of blocks. Returns the rows, rounds to rounds."""
    row = rounds(method.stage)
    rows = [row]
    for i in count():
        for r in lead(row, method.lead_changes("p", i)):
            rows.append(r)
        row = rows[-1]
        if row == rows[0] and (i + 1) % len(method.blocks) == 0:
            return rows
        if len(rows) > 2 * factorial(method.stage):
            raise ValueError("course does not return to rounds")


def plain_course(notation, n):
    """Ring leads from rounds until rounds returns. Returns the list of rows
    rung, starting with rounds and ending with rounds again."""
    changes = parse(notation)
    start = rounds(n)
    rows = [start]
    row = start
    for _ in count():
        for r in lead(row, changes):
            rows.append(r)
        row = rows[-1]
        if row == start:
            return rows
        if len(rows) > 2 * factorial(n):
            raise ValueError("course does not return to rounds")


def factorial(n):
    out = 1
    for k in range(2, n + 1):
        out *= k
    return out


def is_true(rows):
    """True iff no row repeats (ignoring the final return to rounds)."""
    body = rows[:-1] if rows[-1] == rows[0] else rows
    return len(set(body)) == len(body)


def is_extent(rows):
    n = len(rows[0])
    body = rows[:-1] if rows[-1] == rows[0] else rows
    return is_true(rows) and len(body) == factorial(n)


def _grid_line(row, track):
    line = "".join(
        f"({bell_char(b)})" if b == track else f" {bell_char(b)} " for b in row
    )
    return line.rstrip()


def grid(rows, track=1):
    """Pretty-print rows, one per line, with the tracked bell highlighted."""
    return "\n".join(_grid_line(row, track) for row in rows)


def blue_line(rows, track=1):
    """Like grid(), but with the tracked bell's path drawn between rows —
    the 'line' a ringer learns for their bell."""
    width = 3
    out = []
    prev = None
    for row in rows:
        pos = row.index(track)
        if prev is not None:
            mid = ((prev * width + 1) + (pos * width + 1)) // 2
            ch = "|" if pos == prev else ("\\" if pos > prev else "/")
            out.append(" " * mid + ch)
        out.append(_grid_line(row, track))
        prev = pos
    return "\n".join(out)


def to_svg(rows, tracks=(1,), per_column=None, rule=None):
    """Render rows as a classic printed method diagram: one column per
    lead, grey figures, each tracked bell's path drawn over them — red
    for the treble, blue (then green, orange) for the rest. Non-treble
    tracked bells get their place-bell number at each column top; pass
    `rule` to draw a light line every that many rows (six ends etc)."""
    n = len(rows[0])
    per = per_column or (len(rows) - 1)
    columns = [rows[i : i + per + 1] for i in range(0, len(rows) - 1, per)]
    cw, ch, pad = 16, 15, 24
    col_w = (n + 2) * cw
    width = 2 * pad + len(columns) * col_w - 2 * cw
    height = 2 * pad + per * ch
    palette = iter(["#2050c0", "#20a040", "#e08020", "#8040c0"])
    colors = {t: "#c02020" if t == 1 else next(palette) for t in tracks}

    def xy(col, j, place):
        return (pad + col * col_w + place * cw, pad + j * ch)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" font-family="monospace" font-size="12">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]
    for c, chunk in enumerate(columns):
        if rule:
            for j in range(rule, len(chunk) - 1, rule):
                (x0, y0), (x1, _) = xy(c, j, 0), xy(c, j, n - 1)
                y = y0 + ch // 2
                parts.append(
                    f'<line x1="{x0 - cw // 2}" y1="{y}" '
                    f'x2="{x1 + cw // 2}" y2="{y}" stroke="#ccc"/>'
                )
        for t in tracks:
            if t == 1:
                continue
            x, y = xy(c, 0, chunk[0].index(t))
            parts.append(
                f'<text x="{x}" y="{y - 12}" fill="{colors[t]}" '
                f'text-anchor="middle" font-weight="bold">'
                f"{chunk[0].index(t) + 1}</text>"
            )
        for j, row in enumerate(chunk):
            for p, b in enumerate(row):
                if b in tracks and j > 0:
                    continue
                x, y = xy(c, j, p)
                parts.append(
                    f'<text x="{x}" y="{y + 4}" fill="#999" '
                    f'text-anchor="middle">{bell_char(b)}</text>'
                )
        for t in tracks:
            pts = " ".join(
                "%d,%d" % xy(c, j, row.index(t)) for j, row in enumerate(chunk)
            )
            parts.append(
                f'<polyline points="{pts}" fill="none" stroke="{colors[t]}" '
                f'stroke-width="1.8" stroke-linejoin="round"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def describe(rows):
    n = len(rows[0])
    body = len(rows) - (1 if rows[-1] == rows[0] else 0)
    stage = STAGE_NAMES.get(n, f"on {n}")
    truth = "true" if is_true(rows) else "FALSE"
    extent = " (full extent!)" if is_extent(rows) else ""
    return f"{body} changes {stage}, {truth}{extent}"


def main(argv):
    args = []
    svg_path = None
    for a in argv[1:]:
        if a.endswith(".svg"):
            svg_path = a
        else:
            args.append(a)
    track = 1
    if len(args) >= 2 and args[-1].isdigit() and (
        find_method(args[0]) or len(args) > 2
    ):
        track = int(args.pop())
    method = find_method(args[0]) if args else None
    if method is not None:
        if len(args) == 2:
            rows = touch(method, args[1])
        else:
            rows = course(method)
    elif len(args) == 2:
        rows = plain_course(args[0], int(args[1]))
    else:
        print("usage: python3 rings.py <place-notation> <bells> [track-bell] [out.svg]")
        print("       python3 rings.py <method-name> [calling] [track-bell] [out.svg]")
        print("e.g.:  python3 rings.py 'x14x14,12' 4")
        print("       python3 rings.py 'Plain Bob Doubles' pppbpppbpppb 5")
        print("methods:", ", ".join(METHODS))
        return 1
    if svg_path:
        per = sum(len(b) for b in method.blocks) if method else None
        rule = (
            len(method.blocks[0])
            if method and len(method.blocks) > 1
            else None
        )
        tracks = (1,) if track == 1 else (1, track)
        with open(svg_path, "w") as f:
            f.write(to_svg(rows, tracks, per, rule))
        print(f"wrote {svg_path}")
    else:
        print(blue_line(rows, track))
    print(describe(rows))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
