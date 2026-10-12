#include <stdio.h>
#include <stdlib.h>

typedef struct PairNode {
    int element;
    struct PairNode *left_child, *next_sibling, *prev;
} PairNode;

static PairNode *new_node(int element)
{
    PairNode *node = calloc(1, sizeof(*node));
    if (node == NULL) exit(EXIT_FAILURE);
    node->element = element;
    return node;
}

static PairNode *compare_and_link(PairNode *first, PairNode *second)
{
    if (second == NULL) return first;
    if (first->element <= second->element) {
        second->prev = first;
        second->next_sibling = first->left_child;
        if (first->left_child != NULL) first->left_child->prev = second;
        first->left_child = second;
        return first;
    }
    first->prev = second;
    first->next_sibling = second->left_child;
    if (second->left_child != NULL) second->left_child->prev = first;
    second->left_child = first;
    return second;
}

static PairNode *insert(int item, PairNode **heap)
{
    PairNode *node = new_node(item);
    *heap = *heap == NULL ? node : compare_and_link(*heap, node);
    return node;
}

static int decrease_key(PairNode *node, int new_value, PairNode **heap)
{
    if (new_value > node->element) return 0;
    node->element = new_value;
    if (node != *heap) {
        if (node->next_sibling != NULL) node->next_sibling->prev = node->prev;
        if (node->prev->left_child == node) node->prev->left_child = node->next_sibling;
        else node->prev->next_sibling = node->next_sibling;
        node->next_sibling = NULL;
        node->prev = NULL;
        *heap = compare_and_link(*heap, node);
    }
    return 1;
}

static PairNode *combine_siblings(PairNode *first)
{
    PairNode *trees[64];
    int count = 0;
    while (first != NULL) {
        if (count == 64) exit(EXIT_FAILURE);
        PairNode *next = first->next_sibling;
        first->next_sibling = NULL;
        first->prev = NULL;
        trees[count++] = first;
        first = next;
    }
    for (int i = 0; i + 1 < count; i += 2)
        trees[i] = compare_and_link(trees[i], trees[i + 1]);
    int last = count % 2 == 0 ? count - 2 : count - 1;
    PairNode *result = trees[last];
    for (int i = last - 2; i >= 0; i -= 2)
        result = compare_and_link(trees[i], result);
    result->prev = NULL;
    return result;
}

static int delete_min(PairNode **heap, int *minimum)
{
    if (*heap == NULL) return 0;
    PairNode *old = *heap;
    *minimum = old->element;
    *heap = old->left_child == NULL ? NULL : combine_siblings(old->left_child);
    free(old);
    return 1;
}

static void destroy(PairNode *root)
{
    if (root == NULL) return;
    destroy(root->left_child); destroy(root->next_sibling); free(root);
}

int weiss_run_ch12_pair(int number)
{
    PairNode *heap = NULL;
    insert(7, &heap);
    insert(3, &heap);
    PairNode *node = insert(9, &heap);
    insert(5, &heap);
    switch (number) {
    case 53: printf("CompareAndLink minimum = %d\n", heap->element); break;
    case 54: decrease_key(node, 1, &heap); printf("DecreaseKey minimum = %d\n", heap->element); break;
    case 55: { int minimum; delete_min(&heap, &minimum); printf("DeleteMin = %d\n", minimum); break; }
    case 56: { int minimum; delete_min(&heap, &minimum); printf("CombineSiblings minimum = %d\n", heap->element); break; }
    default: destroy(heap); return 1;
    }
    destroy(heap);
    return 0;
}
