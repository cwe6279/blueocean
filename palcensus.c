/* palcensus.c — count single-cycle settings of one family-B
 * complement of palindromic Grandsire Triples (see palsearch.py).
 *
 * stdin:  L r
 *         360 ints: base successor array (option 0 everywhere;
 *                   -1 for complement vertices)
 *         F                      number of free mu-components
 *         then F blocks:  nopt m   followed by nopt blocks of
 *                         m lines  "v s"  (same vertex set per option)
 * stdout: the number of settings (product of the nopt's) whose
 *         successor map is a single L-cycle through r.
 *
 * The walk from r returning to r in exactly L steps IS the full
 * single-cycle condition: exactly L vertices are active.
 * Enumeration is depth-first over components, patching in place —
 * the same per-component-patch idea as palsearch.sweep, ~40x faster.
 */
#include <stdio.h>

#define N 360
#define MAXF 40
#define MAXOPT 16
#define MAXM 12

static int succ[N];
static int L, r, F;
static int nopt[MAXF], m[MAXF];
static int vv[MAXF][MAXOPT][MAXM], ss[MAXF][MAXOPT][MAXM];
static long long count;

static void apply(int d, int o)
{
    for (int i = 0; i < m[d]; i++)
        succ[vv[d][o][i]] = ss[d][o][i];
}

static void rec(int d)
{
    if (d == F) {
        int v = r, steps = 0;
        do {
            v = succ[v];
            steps++;
        } while (v != r && steps < L);
        if (v == r && steps == L)
            count++;
        return;
    }
    for (int o = 0; o < nopt[d]; o++) {
        apply(d, o);
        rec(d + 1);
    }
    apply(d, 0);
}

int main(void)
{
    if (scanf("%d %d", &L, &r) != 2)
        return 1;
    for (int i = 0; i < N; i++)
        if (scanf("%d", &succ[i]) != 1)
            return 1;
    if (scanf("%d", &F) != 1 || F > MAXF)
        return 1;
    for (int d = 0; d < F; d++) {
        if (scanf("%d %d", &nopt[d], &m[d]) != 2 ||
            nopt[d] > MAXOPT || m[d] > MAXM)
            return 1;
        for (int o = 0; o < nopt[d]; o++)
            for (int i = 0; i < m[d]; i++)
                if (scanf("%d %d", &vv[d][o][i], &ss[d][o][i]) != 2)
                    return 1;
    }
    rec(0);
    printf("%lld\n", count);
    return 0;
}
