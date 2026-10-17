/* Check all triples, a two-sided identity, and two-sided inverses. */
#include <ctype.h>
#include <stdio.h>
#include <string.h>

enum { MAX_N = 16 };

/* Bounded token parsing: optional minus and 1..4 ASCII digits. */
static int number(int *value) {
    int ch;
    do { ch = getchar(); } while (ch != EOF && isspace((unsigned char)ch));
    if (ch == EOF) return 0;
    int sign = 1, digits = 0, total = 0, valid = 1;
    if (ch == '-') { sign = -1; ch = getchar(); }
    while (ch != EOF && !isspace((unsigned char)ch)) {
        if (ch < '0' || ch > '9' || digits == 4) valid = 0;
        if (valid) total = 10 * total + (ch - '0');
        if (digits < 5) ++digits;
        ch = getchar();
    }
    if (!valid || digits == 0) return -1;
    *value = sign * total;
    return 1;
}

int main(int argc, char **argv) {
    int n = 4, table[MAX_N][MAX_N] = {{0}};
    if (argc == 2 && strcmp(argv[1], "--stdin") == 0) {
        if (number(&n) != 1 || n < 1 || n > MAX_N) goto bad_input;
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j)
                if (number(&table[i][j]) != 1) goto bad_input;
        int extra;
        if (number(&extra) != 0 || ferror(stdin)) goto bad_input;
    } else if (argc == 1) {
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j) table[i][j] = i ^ j;
    } else goto bad_input;

    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j)
            if (table[i][j] < 0 || table[i][j] >= n) {
                printf("CLOSURE FAIL %d %d %d\nGROUP NO\n", i, j, table[i][j]);
                return 1;
            }
    puts("CLOSURE OK");
    int associative = 1;
    for (int a = 0; a < n && associative; ++a)
        for (int b = 0; b < n && associative; ++b)
            for (int c = 0; c < n; ++c) {
                int left = table[table[a][b]][c], right = table[a][table[b][c]];
                if (left != right) {
                    printf("ASSOCIATIVE FAIL %d %d %d %d %d\n", a, b, c, left, right);
                    associative = 0;
                    break;
                }
            }
    if (associative) puts("ASSOCIATIVE OK");
    int identity = -1;
    for (int e = 0; e < n && identity < 0; ++e) {
        int valid = 1;
        for (int a = 0; a < n; ++a)
            if (table[e][a] != a || table[a][e] != a) valid = 0;
        if (valid) identity = e;
    }
    int missing = -1;
    if (identity < 0) puts("IDENTITY NONE\nINVERSES UNDEFINED");
    else {
        printf("IDENTITY %d\n", identity);
        for (int a = 0; a < n && missing < 0; ++a) {
            int found = 0;
            for (int b = 0; b < n; ++b)
                if (table[a][b] == identity && table[b][a] == identity) found = 1;
            if (!found) missing = a;
        }
        if (missing < 0) puts("INVERSES OK");
        else printf("INVERSES FAIL %d\n", missing);
    }
    int group = associative && identity >= 0 && missing < 0;
    puts(group ? "GROUP YES" : "GROUP NO");
    return group ? 0 : 1;

bad_input:
    fputs("usage: tables [--stdin]; n in 1..16, then n*n integer entries (1..4 digits)\n", stderr);
    return 2;
}
