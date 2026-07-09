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

    A call is itself a scrap of place notation that replaces the same
    number of changes at the *end* of a lead. E.g. a Plain Bob bob '14'
    replaces the lead-end '12'; a Grandsire bob '3.1' replaces '5.1'.
    """

    def __init__(self, name, notation, stage, calls=None):
        self.name = name
        self.notation = notation
        self.stage = stage
        self.changes = parse(notation)
        self.calls = {k: parse(v) for k, v in (calls or {}).items()}

    def lead_changes(self, call="p"):
        if call == "p":
            return self.changes
        tail = self.calls[call]
        return self.changes[: -len(tail)] + tail


METHODS = {
    m.name: m
    for m in [
        Method("Plain Bob Minimus", "x14x14,12", 4, {"b": "14", "s": "1234"}),
        Method("Plain Bob Doubles", "5.1.5.1.5,125", 5, {"b": "145", "s": "123"}),
        Method("Plain Bob Minor", "x16x16x16,12", 6, {"b": "14", "s": "1234"}),
        Method("Grandsire Doubles", "3,1.5.1.5.1", 5, {"b": "3.1", "s": "3.123"}),
    ]
}


def find_method(name):
    for m in METHODS.values():
        if m.name.lower() == name.lower():
            return m
    return None


def touch(method, calling):
    """Ring one lead per character of `calling`: 'p' plain, 'b' bob,
    's' single. Returns the rows rung, starting from rounds."""
    row = rounds(method.stage)
    rows = [row]
    for call in calling.replace(" ", "").lower():
        for r in lead(row, method.lead_changes(call)):
            rows.append(r)
        row = rows[-1]
    return rows


def search_extents(method, calls="pb", limit=None):
    """Depth-first search for callings (one call per lead) whose touch is a
    true round block containing every row: an extent. Returns the list of
    calling strings found (rotations count separately)."""
    start = rounds(method.stage)
    target = factorial(method.stage)
    found = []

    def dfs(row, seen, calling):
        if limit is not None and len(found) >= limit:
            return
        for c in calls:
            lead_rows = list(lead(row, method.lead_changes(c)))
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


def describe(rows):
    n = len(rows[0])
    body = len(rows) - (1 if rows[-1] == rows[0] else 0)
    stage = STAGE_NAMES.get(n, f"on {n}")
    truth = "true" if is_true(rows) else "FALSE"
    extent = " (full extent!)" if is_extent(rows) else ""
    return f"{body} changes {stage}, {truth}{extent}"


def main(argv):
    args = argv[1:]
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
            rows = plain_course(method.notation, method.stage)
    elif len(args) == 2:
        rows = plain_course(args[0], int(args[1]))
    else:
        print("usage: python3 rings.py <place-notation> <bells> [track-bell]")
        print("       python3 rings.py <method-name> [calling] [track-bell]")
        print("e.g.:  python3 rings.py 'x14x14,12' 4")
        print("       python3 rings.py 'Plain Bob Doubles' pppbpppbpppb 5")
        print("methods:", ", ".join(METHODS))
        return 1
    print(blue_line(rows, track))
    print(describe(rows))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
