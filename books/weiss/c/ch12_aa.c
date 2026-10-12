#include <stdio.h>
#include <stdlib.h>

typedef struct AANode {
    int element, level;
    struct AANode *left, *right;
} AANode;

static int level(const AANode *p) { return p == NULL ? 0 : p->level; }

static AANode *skew(AANode *root)
{
    if (root != NULL && root->left != NULL && root->left->level == root->level) {
        AANode *child = root->left;
        root->left = child->right;
        child->right = root;
        return child;
    }
    return root;
}

static AANode *split(AANode *root)
{
    if (root != NULL && root->right != NULL && root->right->right != NULL &&
        root->right->right->level == root->level) {
        AANode *child = root->right;
        root->right = child->left;
        child->left = root;
        ++child->level;
        return child;
    }
    return root;
}

static AANode *insert(int item, AANode *root)
{
    if (root == NULL) {
        AANode *node = calloc(1, sizeof(*node));
        if (node == NULL) exit(EXIT_FAILURE);
        node->element = item; node->level = 1;
        return node;
    }
    if (item < root->element) root->left = insert(item, root->left);
    else if (item > root->element) root->right = insert(item, root->right);
    return split(skew(root));
}

static AANode *remove_item(int item, AANode *root)
{
    if (root == NULL) return NULL;
    if (item < root->element) root->left = remove_item(item, root->left);
    else if (item > root->element) root->right = remove_item(item, root->right);
    else {
        if (root->left == NULL || root->right == NULL) {
            AANode *child = root->left != NULL ? root->left : root->right;
            free(root);
            return child;
        }
        AANode *successor = root->right;
        while (successor->left != NULL) successor = successor->left;
        root->element = successor->element;
        root->right = remove_item(successor->element, root->right);
    }
    int should_be = (level(root->left) < level(root->right) ?
                     level(root->left) : level(root->right)) + 1;
    if (should_be < root->level) {
        root->level = should_be;
        if (root->right != NULL && root->right->level > should_be)
            root->right->level = should_be;
    }
    root = skew(root);
    root->right = skew(root->right);
    if (root->right != NULL) root->right->right = skew(root->right->right);
    root = split(root);
    root->right = split(root->right);
    return root;
}

static int contains(int item, const AANode *root)
{
    while (root != NULL) {
        if (item < root->element) root = root->left;
        else if (item > root->element) root = root->right;
        else return 1;
    }
    return 0;
}

static void destroy(AANode *root)
{
    if (root == NULL) return;
    destroy(root->left); destroy(root->right); free(root);
}

int weiss_run_ch12_aa(int number)
{
    AANode *root = NULL;
    if (number != 27) {
        int values[] = {5, 2, 8, 1, 3, 7};
        for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i)
            root = insert(values[i], root);
    }
    switch (number) {
    case 27: printf("Initialize: empty = %d\n", root == NULL); break;
    case 29: printf("Skew/Split: root = %d, level = %d\n", root->element, root->level); break;
    case 36: root = insert(4, root); printf("Insert(4) = %d\n", contains(4, root)); break;
    case 38: root = remove_item(2, root); printf("Remove(2): found = %d\n", contains(2, root)); break;
    default: destroy(root); return 1;
    }
    destroy(root);
    return 0;
}
