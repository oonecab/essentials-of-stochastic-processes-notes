#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct SkipNode {
    int element;
    struct SkipNode *right, *down;
} SkipNode;
typedef struct { SkipNode *head, *bottom, *tail; } SkipList;

static SkipNode *new_node(int item, SkipNode *right, SkipNode *down)
{
    SkipNode *p = malloc(sizeof(*p));
    if (p == NULL) exit(EXIT_FAILURE);
    p->element = item; p->right = right; p->down = down;
    return p;
}

static void initialize(SkipList *list)
{
    list->bottom = new_node(0, NULL, NULL);
    list->bottom->right = list->bottom;
    list->bottom->down = list->bottom;
    list->tail = new_node(INT_MAX, NULL, list->bottom);
    list->tail->right = list->tail;
    list->head = new_node(INT_MAX, list->tail, list->bottom);
}

static SkipNode *find(int item, SkipList *list)
{
    SkipNode *current = list->head;
    list->bottom->element = item;
    while (item != current->element)
        current = item < current->element ? current->down : current->right;
    return current;
}

/* fig12.25: promote the middle item when a gap grows to three. */
static void insert(int item, SkipList *list)
{
    SkipNode *current = list->head;
    list->bottom->element = item;
    while (current != list->bottom) {
        while (item > current->element) current = current->right;
        if (current->element > current->down->right->right->element) {
            SkipNode *node = new_node(current->element, current->right,
                                      current->down->right->right);
            current->right = node;
            current->element = current->down->right->element;
        }
        current = current->down;
    }
    if (list->head->right != list->tail)
        list->head = new_node(INT_MAX, list->tail, list->head);
}

static void destroy(SkipList *list)
{
    SkipNode *level = list->head;
    while (level != list->bottom) {
        SkipNode *next_level = level->down;
        SkipNode *node = level;
        while (node != list->tail) {
            SkipNode *next = node->right;
            free(node);
            node = next;
        }
        level = next_level;
    }
    free(list->tail);
    free(list->bottom);
}

int weiss_run_ch12_skip(int number)
{
    SkipList list;
    initialize(&list);
    if (number != 23) {
        int values[] = {2, 5, 8, 1, 3};
        for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i)
            insert(values[i], &list);
    }
    switch (number) {
    case 23: printf("Initialize: head = %d\n", list.head->element); break;
    case 24: printf("Find(5) = %d; Find(6) is bottom = %d\n",
                    find(5, &list)->element, find(6, &list) == list.bottom); break;
    case 25: insert(7, &list); printf("Insert(7): found = %d\n", find(7, &list) != list.bottom); break;
    default: destroy(&list); return 1;
    }
    destroy(&list);
    return 0;
}
