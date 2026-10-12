#include <stdio.h>
#include <stdlib.h>

typedef enum { BLACK, RED } Color;
typedef struct RedBlackNode {
    int element;
    Color color;
    struct RedBlackNode *left, *right;
} RedBlackNode;

static int is_red(const RedBlackNode *p) { return p != NULL && p->color == RED; }

static RedBlackNode *rotate_left(RedBlackNode *root)
{
    RedBlackNode *child = root->right;
    root->right = child->left;
    child->left = root;
    child->color = root->color;
    root->color = RED;
    return child;
}

static RedBlackNode *rotate_right(RedBlackNode *root)
{
    RedBlackNode *child = root->left;
    root->left = child->right;
    child->right = root;
    child->color = root->color;
    root->color = RED;
    return child;
}

static void flip_colors(RedBlackNode *root)
{
    root->color = root->color == RED ? BLACK : RED;
    root->left->color = root->left->color == RED ? BLACK : RED;
    root->right->color = root->right->color == RED ? BLACK : RED;
}

/* Left-leaning red-black insertion expresses the rotations/color flips in fig12.16. */
static RedBlackNode *insert_rec(int item, RedBlackNode *root)
{
    if (root == NULL) {
        RedBlackNode *node = calloc(1, sizeof(*node));
        if (node == NULL) exit(EXIT_FAILURE);
        node->element = item;
        node->color = RED;
        return node;
    }
    if (item < root->element) root->left = insert_rec(item, root->left);
    else if (item > root->element) root->right = insert_rec(item, root->right);
    if (is_red(root->right) && !is_red(root->left)) root = rotate_left(root);
    if (is_red(root->left) && is_red(root->left->left)) root = rotate_right(root);
    if (is_red(root->left) && is_red(root->right)) flip_colors(root);
    return root;
}

static void insert(int item, RedBlackNode **root)
{
    *root = insert_rec(item, *root);
    (*root)->color = BLACK;
}

static void print_tree(const RedBlackNode *root)
{
    if (root == NULL) return;
    print_tree(root->left);
    printf("%d ", root->element);
    print_tree(root->right);
}

static void destroy(RedBlackNode *root)
{
    if (root == NULL) return;
    destroy(root->left); destroy(root->right); free(root);
}

int weiss_run_ch12_redblack(int number)
{
    RedBlackNode *root = NULL;
    if (number != 14) {
        int values[] = {5, 2, 8, 1, 3, 7};
        for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i)
            insert(values[i], &root);
    }
    switch (number) {
    case 13: printf("Red-black inorder: "); print_tree(root); puts(""); break;
    case 14: printf("Initialize: empty = %d\n", root == NULL); break;
    case 15: root = rotate_right(root); printf("Rotate with left child: root = %d\n", root->element); break;
    case 16: insert(4, &root); printf("Insert: root = %d, color = %s\n",
                            root->element, root->color == BLACK ? "black" : "red"); break;
    default: destroy(root); return 1;
    }
    destroy(root);
    return 0;
}
