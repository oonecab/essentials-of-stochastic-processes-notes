#include <stdio.h>
#include <stdlib.h>

typedef struct SplayNode {
    int element;
    struct SplayNode *left, *right;
} SplayNode;

static SplayNode *new_node(int element)
{
    SplayNode *p = calloc(1, sizeof(*p));
    if (p == NULL) exit(EXIT_FAILURE);
    p->element = element;
    return p;
}

static SplayNode *rotate_left_child(SplayNode *root)
{
    SplayNode *child = root->left;
    root->left = child->right;
    child->right = root;
    return child;
}

static SplayNode *rotate_right_child(SplayNode *root)
{
    SplayNode *child = root->right;
    root->right = child->left;
    child->left = root;
    return child;
}

/* fig12.6: top-down splay, including searches for absent items. */
static SplayNode *splay(int item, SplayNode *root)
{
    if (root == NULL) return NULL;
    SplayNode header = {0, NULL, NULL};
    SplayNode *left_max = &header, *right_min = &header;
    for (;;) {
        if (item < root->element) {
            if (root->left == NULL) break;
            if (item < root->left->element) root = rotate_left_child(root);
            if (root->left == NULL) break;
            right_min->left = root;
            right_min = root;
            root = root->left;
        } else if (item > root->element) {
            if (root->right == NULL) break;
            if (item > root->right->element) root = rotate_right_child(root);
            if (root->right == NULL) break;
            left_max->right = root;
            left_max = root;
            root = root->right;
        } else break;
    }
    left_max->right = root->left;
    right_min->left = root->right;
    root->left = header.right;
    root->right = header.left;
    return root;
}

static SplayNode *insert(int item, SplayNode *root)
{
    if (root == NULL) return new_node(item);
    root = splay(item, root);
    if (item == root->element) return root;
    SplayNode *node = new_node(item);
    if (item < root->element) {
        node->left = root->left;
        node->right = root;
        root->left = NULL;
    } else {
        node->right = root->right;
        node->left = root;
        root->right = NULL;
    }
    return node;
}

static SplayNode *remove_item(int item, SplayNode *root)
{
    if (root == NULL) return NULL;
    root = splay(item, root);
    if (root->element != item) return root;
    SplayNode *old = root;
    SplayNode *left = root->left, *right = root->right;
    if (left == NULL) root = right;
    else {
        root = splay(item, left);
        root->right = right;
    }
    free(old);
    return root;
}

static void destroy(SplayNode *root)
{
    if (root == NULL) return;
    destroy(root->left); destroy(root->right); free(root);
}

int weiss_run_ch12_splay(int number)
{
    SplayNode *root = NULL;
    if (number != 5) {
        int values[] = {5, 2, 8, 1, 3};
        for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i)
            root = insert(values[i], root);
    }
    switch (number) {
    case 5: printf("Initialize: empty = %d\n", root == NULL); break;
    case 6: root = splay(2, root); printf("Splay root = %d\n", root->element); break;
    case 7: root = insert(4, root); printf("Insert root = %d\n", root->element); break;
    case 8: root = remove_item(2, root); printf("After Delete root = %d\n", root->element); break;
    default: destroy(root); return 1;
    }
    destroy(root);
    return 0;
}
