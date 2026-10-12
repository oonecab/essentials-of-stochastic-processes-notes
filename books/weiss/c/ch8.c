#include <stdio.h>

#define NUM_SETS 8
typedef struct { int parent[NUM_SETS + 1]; } DisjSet;

static void initialize(DisjSet *s)
{
    for (int i = 1; i <= NUM_SETS; ++i) s->parent[i] = 0;
}

static int find_plain(int x, const DisjSet *s)
{
    return s->parent[x] <= 0 ? x : find_plain(s->parent[x], s);
}

static int find_compress(int x, DisjSet *s)
{
    if (s->parent[x] <= 0) return x;
    s->parent[x] = find_compress(s->parent[x], s);
    return s->parent[x];
}

static void union_simple(DisjSet *s, int root1, int root2)
{
    s->parent[root2] = root1;
}

static void union_height(DisjSet *s, int root1, int root2)
{
    if (s->parent[root2] < s->parent[root1]) s->parent[root1] = root2;
    else {
        if (s->parent[root2] == s->parent[root1]) --s->parent[root1];
        s->parent[root2] = root1;
    }
}

int weiss_run_ch8(int number)
{
    DisjSet s;
    initialize(&s);
    switch (number) {
    case 6: printf("DisjSet size = %d\n", NUM_SETS); break;
    case 7: printf("Initialize: S[1] = %d\n", s.parent[1]); break;
    case 8: union_simple(&s, 1, 2); printf("Union: Find(2) = %d\n", find_plain(2, &s)); break;
    case 9: union_simple(&s, 1, 2); printf("Find(2) = %d\n", find_plain(2, &s)); break;
    case 13: union_height(&s, 1, 2); printf("Union by height: Find(2) = %d\n", find_plain(2, &s)); break;
    case 15: union_simple(&s, 1, 2); printf("Path compression: Find(2) = %d\n", find_compress(2, &s)); break;
    default: fprintf(stderr, "unknown chapter 8 figure: %d\n", number); return 1;
    }
    return 0;
}
