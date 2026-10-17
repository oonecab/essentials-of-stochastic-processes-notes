/* D_n, 3 <= n <= 12. Temporal words: r then f is written rf. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { CAPACITY = 24 };
typedef struct { int sign, shift, edge[2]; char word[CAPACITY + 1]; } State;

static int modulo(int x, int n) { return (x % n + n) % n; }

int main(int argc, char **argv) {
    int n = 4;
    if (argc > 2) { fputs("usage: cayley [3..12]\n", stderr); return 2; }
    if (argc == 2) {
        n = 0;
        for (int candidate = 3; candidate <= 12; ++candidate) {
            char expected[4];
            (void)snprintf(expected, sizeof expected, "%d", candidate);
            if (strcmp(argv[1], expected) == 0) n = candidate;
        }
        if (n == 0) { fputs("usage: cayley [3..12]\n", stderr); return 2; }
    }
    State states[CAPACITY] = {{0}};
    states[0].sign = 1;
    int count = 1;
    for (int head = 0; head < count; ++head) {
        for (int g = 0; g < 2; ++g) {
            int sign = g == 0 ? states[head].sign : -states[head].sign;
            int shift = modulo(g == 0 ? states[head].shift + 1 : -states[head].shift, n);
            int dest = 0;
            while (dest < count && !(states[dest].sign == sign && states[dest].shift == shift)) ++dest;
            if (dest == count) {
                if (count == CAPACITY) { fputs("capacity exceeded\n", stderr); return 3; }
                states[dest].sign = sign;
                states[dest].shift = shift;
                size_t length = strlen(states[head].word);
                if (length >= CAPACITY) { fputs("word too long\n", stderr); return 3; }
                memcpy(states[dest].word, states[head].word, length);
                states[dest].word[length] = g == 0 ? 'r' : 'f';
                states[dest].word[length + 1] = '\0';
                ++count;
            }
            states[head].edge[g] = dest;
        }
    }
    printf("D%d: %d actions\nid word sign shift r f\n", n, count);
    for (int i = 0; i < count; ++i)
        printf("%d %s %d %d %d %d\n", i, states[i].word[0] ? states[i].word : "e",
               states[i].sign, states[i].shift, states[i].edge[0], states[i].edge[1]);
    return 0;
}
