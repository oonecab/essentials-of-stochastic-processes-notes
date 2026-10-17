/* Explicit small symmetric groups; composition executes the left action first. */
#include <stdio.h>
#include <string.h>

#define MAX 120
static int n, count;
static int perms[MAX][5], table[MAX][MAX], inverse[MAX];
static int groups[MAX][MAX], sizes[MAX], group_count;

static void enumerate(int depth, int *a, int *used) {
    if (depth == n) {
        for (int i = 0; i < n; ++i) perms[count][i] = a[i];
        ++count;
        return;
    }
    for (int i = 0; i < n; ++i) if (!used[i]) {
        used[i] = 1; a[depth] = i;
        enumerate(depth + 1, a, used);
        used[i] = 0;
    }
}

static int lookup(const int *a) {
    for (int i = 0; i < count; ++i) {
        int equal = 1;
        for (int j = 0; j < n; ++j) if (perms[i][j] != a[j]) equal = 0;
        if (equal) return i;
    }
    return -1;
}

static int compare(const int *a, const int *b, int size) {
    for (int i = 0; i < size; ++i) {
        if (a[i] < b[i]) return -1;
        if (a[i] > b[i]) return 1;
    }
    return 0;
}

static void conjugate(const int *h, int size, int g, int *out) {
    int seen[MAX] = {0}, k = 0;
    for (int i = 0; i < size; ++i) seen[table[table[g][h[i]]][inverse[g]]] = 1;
    for (int i = 0; i < count; ++i) if (seen[i]) out[k++] = i;
}

int main(int argc, char **argv) {
    int p = 2; n = 4;
    if (argc == 3 && strlen(argv[1]) == 1 && strlen(argv[2]) == 1) {
        n = argv[1][0] - '0'; p = argv[2][0] - '0';
    } else if (argc != 1) n = 0;
    if (n < 2 || n > 5 || (p != 2 && p != 3 && p != 5) || p > n) {
        fputs("usage: sylow [n p], 2 <= n <= 5; p prime <= n\n", stderr);
        return 2;
    }
    int a[5] = {0}, used[5] = {0}; enumerate(0, a, used);
    for (int i = 0; i < count; ++i) for (int j = 0; j < count; ++j) {
        for (int k = 0; k < n; ++k) a[k] = perms[j][perms[i][k]];
        int result = lookup(a);
        if (result < 0) return 1;
        table[i][j] = result;
        if (result == 0) inverse[i] = j;
    }
    int length = p == 2 && n >= 4 ? 4 : p;
    for (int i = 0; i < n; ++i) a[i] = i < length ? (i + 1) % length : i;
    int gens[2] = {lookup(a), 0}, ng = 1;
    if (length == 4) {
        for (int i = 0; i < n; ++i) a[i] = i;
        a[0] = 2; a[2] = 0; gens[ng++] = lookup(a);
    }
    int seen[MAX] = {0}, seed[MAX] = {0}, size = 1; seen[0] = 1;
    for (int head = 0; head < size; ++head) for (int j = 0; j < ng; ++j) {
        int x = table[seed[head]][gens[j]];
        if (!seen[x]) { seen[x] = 1; seed[size++] = x; }
    }
    for (int g = 0; g < count; ++g) {
        int h[MAX]; conjugate(seed, size, g, h);
        int found = 0;
        for (int i = 0; i < group_count; ++i) if (compare(groups[i], h, size) == 0) found = 1;
        if (!found) {
            int at = group_count;
            while (at > 0 && compare(h, groups[at - 1], size) < 0) {
                memcpy(groups[at], groups[at - 1], sizeof groups[at]);
                sizes[at] = sizes[at - 1]; --at;
            }
            memcpy(groups[at], h, (size_t)size * sizeof h[0]);
            sizes[at] = size; ++group_count;
        }
    }
    printf("S%d order=%d p=%d sylow_order=%d\n", n, count, p, size);
    for (int i = 0; i < count; ++i) {
        printf("perm %d: ", i);
        for (int j = 0; j < n; ++j) printf("%s%d", j ? "," : "", perms[i][j] + 1);
        putchar('\n');
    }
    for (int i = 0; i < group_count; ++i) {
        int norm = 0;
        for (int g = 0; g < count; ++g) {
            int h[MAX]; conjugate(groups[i], sizes[i], g, h);
            if (compare(groups[i], h, size) == 0) ++norm;
        }
        printf("H={");
        for (int j = 0; j < size; ++j) printf("%s%d", j ? "," : "", groups[i][j]);
        printf("} normalizer=%d\n", norm);
    }
    printf("sylow_count=%d\n", group_count);
    int stab = 0;
    for (int i = 0; i < count; ++i) if (perms[i][0] == 0) ++stab;
    printf("point_orbit=%d point_stabilizer=%d\n", n, stab);
    return 0;
}
