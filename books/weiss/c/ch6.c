#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

#define HEAP_CAPACITY 32
typedef struct { int element[HEAP_CAPACITY + 1], size; } BinaryHeap;

static void binary_init(BinaryHeap *h)
{
    h->size = 0;
    h->element[0] = INT_MIN;
}

static int binary_insert(int x, BinaryHeap *h)
{
    if (h->size == HEAP_CAPACITY) return 0;
    int i = ++h->size;
    while (h->element[i / 2] > x) {
        h->element[i] = h->element[i / 2];
        i /= 2;
    }
    h->element[i] = x;
    return 1;
}

static int binary_delete_min(BinaryHeap *h, int *result)
{
    if (h->size == 0) return 0;
    *result = h->element[1];
    int last = h->element[h->size--];
    int i = 1;
    while (2 * i <= h->size) {
        int child = 2 * i;
        if (child < h->size && h->element[child + 1] < h->element[child]) ++child;
        if (last <= h->element[child]) break;
        h->element[i] = h->element[child];
        i = child;
    }
    h->element[i] = last;
    return 1;
}

typedef struct LeftistNode {
    int element, npl;
    struct LeftistNode *left, *right;
} LeftistNode;

static LeftistNode *leftist_new(int x)
{
    LeftistNode *p = calloc(1, sizeof(*p));
    if (p == NULL) exit(EXIT_FAILURE);
    p->element = x;
    return p;
}

static int leftist_npl(const LeftistNode *p) { return p == NULL ? -1 : p->npl; }

static LeftistNode *leftist_merge(LeftistNode *a, LeftistNode *b)
{
    if (a == NULL) return b;
    if (b == NULL) return a;
    if (a->element > b->element) { LeftistNode *tmp = a; a = b; b = tmp; }
    a->right = leftist_merge(a->right, b);
    if (leftist_npl(a->left) < leftist_npl(a->right)) {
        LeftistNode *tmp = a->left; a->left = a->right; a->right = tmp;
    }
    a->npl = leftist_npl(a->right) + 1;
    return a;
}

static void leftist_insert(int x, LeftistNode **h)
{
    *h = leftist_merge(*h, leftist_new(x));
}

static int leftist_delete_min(LeftistNode **h, int *result)
{
    if (*h == NULL) return 0;
    LeftistNode *old = *h;
    *result = old->element;
    *h = leftist_merge(old->left, old->right);
    free(old);
    return 1;
}

static void leftist_destroy(LeftistNode *h)
{
    if (h == NULL) return;
    leftist_destroy(h->left); leftist_destroy(h->right); free(h);
}

typedef struct BinomialNode {
    int element, rank;
    struct BinomialNode *child, *sibling;
} BinomialNode;

static BinomialNode *binomial_new(int x)
{
    BinomialNode *p = calloc(1, sizeof(*p));
    if (p == NULL) exit(EXIT_FAILURE);
    p->element = x;
    return p;
}

static BinomialNode *binomial_merge_tree(BinomialNode *a, BinomialNode *b)
{
    if (a->element > b->element) { BinomialNode *tmp = a; a = b; b = tmp; }
    b->sibling = a->child;
    a->child = b;
    ++a->rank;
    return a;
}

/* Merge root lists in rank order, then link equal-rank trees. */
static BinomialNode *binomial_merge(BinomialNode *a, BinomialNode *b)
{
    BinomialNode dummy = {0, 0, NULL, NULL}, *tail = &dummy;
    while (a != NULL || b != NULL) {
        BinomialNode **source = b == NULL || (a != NULL && a->rank <= b->rank) ? &a : &b;
        tail->sibling = *source;
        *source = (*source)->sibling;
        tail = tail->sibling;
    }
    tail->sibling = NULL;
    BinomialNode *prev = NULL, *curr = dummy.sibling;
    while (curr != NULL && curr->sibling != NULL) {
        BinomialNode *next = curr->sibling;
        if (curr->rank != next->rank ||
            (next->sibling != NULL && next->sibling->rank == curr->rank)) {
            prev = curr; curr = next;
        } else if (curr->element <= next->element) {
            curr->sibling = next->sibling;
            binomial_merge_tree(curr, next);
        } else {
            if (prev == NULL) dummy.sibling = next;
            else prev->sibling = next;
            binomial_merge_tree(next, curr);
            curr = next;
        }
    }
    return dummy.sibling;
}

static void binomial_destroy(BinomialNode *h)
{
    if (h == NULL) return;
    binomial_destroy(h->child); binomial_destroy(h->sibling); free(h);
}

int weiss_run_ch6(int number)
{
    if (number == 4 || number == 8 || number == 12) {
        BinaryHeap h; int min = 0;
        binary_init(&h);
        binary_insert(7, &h); binary_insert(2, &h); binary_insert(5, &h);
        if (number == 4) printf("Binary heap capacity = %d\n", HEAP_CAPACITY);
        else if (number == 8) printf("Insert: minimum = %d\n", h.element[1]);
        else { binary_delete_min(&h, &min); printf("DeleteMin = %d; new minimum = %d\n", min, h.element[1]); }
        return 0;
    }
    if (number == 25 || number == 26 || number == 27 || number == 29 || number == 30) {
        LeftistNode *h = NULL; int min = 0;
        leftist_insert(7, &h); leftist_insert(2, &h); leftist_insert(5, &h);
        switch (number) {
        case 25: printf("Leftist node NPL = %d\n", h->npl); break;
        case 26: case 27: printf("Merge: minimum = %d\n", h->element); break;
        case 29: leftist_insert(1, &h); printf("Insert: minimum = %d\n", h->element); break;
        case 30: leftist_delete_min(&h, &min); printf("DeleteMin = %d\n", min); break;
        default: break;
        }
        leftist_destroy(h);
        return 0;
    }
    if (number == 52 || number == 54 || number == 55) {
        BinomialNode *a = binomial_new(7), *b = binomial_new(2);
        if (number == 52) {
            printf("Binomial rank = %d\n", a->rank);
            binomial_destroy(a); binomial_destroy(b);
        } else if (number == 54) {
            BinomialNode *h = binomial_merge_tree(a, b);
            printf("MergeTree: minimum = %d, rank = %d\n", h->element, h->rank);
            binomial_destroy(h);
        } else {
            BinomialNode *h = binomial_merge(a, b);
            printf("Merge: minimum = %d, rank = %d\n", h->element, h->rank);
            binomial_destroy(h);
        }
        return 0;
    }
    fprintf(stderr, "unknown chapter 6 figure: %d\n", number);
    return 1;
}
