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


def grid(rows, track=1):
    """Pretty-print rows, one per line, with the tracked bell's path drawn."""
    lines = []
    for row in rows:
        line = "".join(
            f"({bell_char(b)})" if b == track else f" {bell_char(b)} "
            for b in row
        )
        lines.append(line.rstrip())
    return "\n".join(lines)


def describe(rows):
    n = len(rows[0])
    body = len(rows) - (1 if rows[-1] == rows[0] else 0)
    stage = STAGE_NAMES.get(n, f"on {n}")
    truth = "true" if is_true(rows) else "FALSE"
    extent = " (full extent!)" if is_extent(rows) else ""
    return f"{body} changes {stage}, {truth}{extent}"


def main(argv):
    if len(argv) != 3:
        print("usage: python3 rings.py <place-notation> <bells>")
        print("e.g.:  python3 rings.py 'x14x14,12' 4     # Plain Bob Minimus")
        print("       python3 rings.py '5.1.5.1.5,125' 5 # Plain Bob Doubles")
        print("       python3 rings.py '3,1.5.1.5.1' 5   # Grandsire Doubles")
        return 1
    notation, n = argv[1], int(argv[2])
    rows = plain_course(notation, n)
    print(grid(rows))
    print(describe(rows))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
