#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct TreapNode {
    int element, priority;
    struct TreapNode *left, *right;
} TreapNode;

static uint32_t random_state = 1;
static int next_priority(void)
{
    random_state = (uint32_t)(((uint64_t)random_state * 48271U) % 2147483647U);
    return (int)random_state;
}

static TreapNode *rotate_left_child(TreapNode *root)
{
    TreapNode *child = root->left;
    root->left = child->right; child->right = root;
    return child;
}

static TreapNode *rotate_right_child(TreapNode *root)
{
    TreapNode *child = root->right;
    root->right = child->left; child->left = root;
    return child;
}

static TreapNode *insert(int item, TreapNode *root)
{
    if (root == NULL) {
        TreapNode *node = calloc(1, sizeof(*node));
        if (node == NULL) exit(EXIT_FAILURE);
        node->element = item; node->priority = next_priority();
        return node;
    }
    if (item < root->element) {
        root->left = insert(item, root->left);
        if (root->left->priority < root->priority) root = rotate_left_child(root);
    } else if (item > root->element) {
        root->right = insert(item, root->right);
        if (root->right->priority < root->priority) root = rotate_right_child(root);
    }
    return root;
}

static TreapNode *merge(TreapNode *left, TreapNode *right)
{
    if (left == NULL) return right;
    if (right == NULL) return left;
    if (left->priority < right->priority) {
        left->right = merge(left->right, right);
        return left;
    }
    right->left = merge(left, right->left);
    return right;
}

static TreapNode *remove_item(int item, TreapNode *root)
{
    if (root == NULL) return NULL;
    if (item < root->element) root->left = remove_item(item, root->left);
    else if (item > root->element) root->right = remove_item(item, root->right);
    else {
        TreapNode *next = merge(root->left, root->right);
        free(root);
        return next;
    }
    return root;
}

static int contains(int item, const TreapNode *root)
{
    while (root != NULL) {
        if (item < root->element) root = root->left;
        else if (item > root->element) root = root->right;
        else return 1;
    }
    return 0;
}

static void destroy(TreapNode *root)
{
    if (root == NULL) return;
    destroy(root->left); destroy(root->right); free(root);
}

int weiss_run_ch12_treap(int number)
{
    TreapNode *root = NULL;
    random_state = 1;
    if (number != 39) {
        int values[] = {5, 2, 8, 1, 3};
        for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i)
            root = insert(values[i], root);
    }
    switch (number) {
    case 39: printf("Initialize: empty = %d\n", root == NULL); break;
    case 40: root = insert(4, root); printf("Insert(4) = %d\n", contains(4, root)); break;
    case 41: root = remove_item(2, root); printf("Remove(2): found = %d\n", contains(2, root)); break;
    default: destroy(root); return 1;
    }
    destroy(root);
    return 0;
}
