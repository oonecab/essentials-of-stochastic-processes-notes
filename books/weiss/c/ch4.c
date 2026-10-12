#include <stdio.h>
#include <stdlib.h>

typedef struct DirEntry {
    const char *name;
    int own_size, directory;
    struct DirEntry *child, *next;
} DirEntry;

static void list_dir(const DirEntry *d, int depth)
{
    if (d == NULL) return;
    for (int i = 0; i < depth; ++i) putchar(' ');
    puts(d->name);
    if (d->directory)
        for (const DirEntry *child = d->child; child != NULL; child = child->next)
            list_dir(child, depth + 2);
}

static int size_directory(const DirEntry *d)
{
    if (d == NULL) return 0;
    int total = d->own_size;
    if (d->directory)
        for (const DirEntry *child = d->child; child != NULL; child = child->next)
            total += size_directory(child);
    return total;
}

typedef struct ChildNode {
    int element;
    struct ChildNode *first_child, *next_sibling;
} ChildNode;

typedef struct TreeNode {
    int element;
    struct TreeNode *left, *right;
} TreeNode;

static TreeNode *tree_new(int x)
{
    TreeNode *t = malloc(sizeof(*t));
    if (t == NULL) exit(EXIT_FAILURE);
    t->element = x;
    t->left = t->right = NULL;
    return t;
}

static void tree_make_empty(TreeNode **t)
{
    if (*t == NULL) return;
    tree_make_empty(&(*t)->left);
    tree_make_empty(&(*t)->right);
    free(*t);
    *t = NULL;
}

static TreeNode *tree_find(int x, TreeNode *t)
{
    if (t == NULL) return NULL;
    if (x < t->element) return tree_find(x, t->left);
    if (x > t->element) return tree_find(x, t->right);
    return t;
}

static TreeNode *tree_find_min(TreeNode *t)
{
    if (t == NULL || t->left == NULL) return t;
    return tree_find_min(t->left);
}

static TreeNode *tree_find_max(TreeNode *t)
{
    while (t != NULL && t->right != NULL) t = t->right;
    return t;
}

static void tree_insert(int x, TreeNode **t)
{
    if (*t == NULL) *t = tree_new(x);
    else if (x < (*t)->element) tree_insert(x, &(*t)->left);
    else if (x > (*t)->element) tree_insert(x, &(*t)->right);
}

static int tree_delete(int x, TreeNode **t)
{
    if (*t == NULL) return 0;
    if (x < (*t)->element) return tree_delete(x, &(*t)->left);
    if (x > (*t)->element) return tree_delete(x, &(*t)->right);
    if ((*t)->left != NULL && (*t)->right != NULL) {
        TreeNode *successor = tree_find_min((*t)->right);
        (*t)->element = successor->element;
        return tree_delete(successor->element, &(*t)->right);
    }
    TreeNode *old = *t;
    *t = old->left != NULL ? old->left : old->right;
    free(old);
    return 1;
}

static void tree_print(const TreeNode *t)
{
    if (t == NULL) return;
    tree_print(t->left);
    printf("%d ", t->element);
    tree_print(t->right);
}

static int tree_height(const TreeNode *t)
{
    if (t == NULL) return -1;
    int left = tree_height(t->left), right = tree_height(t->right);
    return 1 + (left > right ? left : right);
}

typedef struct AvlNode {
    int element, height;
    struct AvlNode *left, *right;
} AvlNode;

static int avl_height(const AvlNode *t) { return t == NULL ? -1 : t->height; }
static void avl_update(AvlNode *t)
{
    int left = avl_height(t->left), right = avl_height(t->right);
    t->height = 1 + (left > right ? left : right);
}

/* fig4.41: single rotation with the left child. */
static void avl_rotate_left(AvlNode **root)
{
    AvlNode *k2 = *root, *k1 = k2->left;
    k2->left = k1->right;
    k1->right = k2;
    avl_update(k2);
    avl_update(k1);
    *root = k1;
}

static void avl_rotate_right(AvlNode **root)
{
    AvlNode *k1 = *root, *k2 = k1->right;
    k1->right = k2->left;
    k2->left = k1;
    avl_update(k1);
    avl_update(k2);
    *root = k2;
}

static void avl_double_rotate_left(AvlNode **root)
{
    avl_rotate_right(&(*root)->left);
    avl_rotate_left(root);
}

static void avl_double_rotate_right(AvlNode **root)
{
    avl_rotate_left(&(*root)->right);
    avl_rotate_right(root);
}

static void avl_insert(int x, AvlNode **root)
{
    if (*root == NULL) {
        *root = calloc(1, sizeof(**root));
        if (*root == NULL) exit(EXIT_FAILURE);
        (*root)->element = x;
        return;
    }
    if (x < (*root)->element) {
        avl_insert(x, &(*root)->left);
        if (avl_height((*root)->left) - avl_height((*root)->right) == 2) {
            if (x < (*root)->left->element) avl_rotate_left(root);
            else avl_double_rotate_left(root);
        }
    } else if (x > (*root)->element) {
        avl_insert(x, &(*root)->right);
        if (avl_height((*root)->right) - avl_height((*root)->left) == 2) {
            if (x > (*root)->right->element) avl_rotate_right(root);
            else avl_double_rotate_right(root);
        }
    }
    avl_update(*root);
}

static void avl_destroy(AvlNode *t)
{
    if (t == NULL) return;
    avl_destroy(t->left); avl_destroy(t->right); free(t);
}

typedef struct SplayNode {
    int element;
    struct SplayNode *left, *right, *parent;
} SplayNode;

static SplayNode *splay_new(int x)
{
    SplayNode *p = calloc(1, sizeof(*p));
    if (p == NULL) exit(EXIT_FAILURE);
    p->element = x;
    return p;
}

static void rotate_up(SplayNode *x)
{
    SplayNode *p = x->parent, *g = p->parent;
    if (p->left == x) {
        p->left = x->right;
        if (x->right != NULL) x->right->parent = p;
        x->right = p;
    } else {
        p->right = x->left;
        if (x->left != NULL) x->left->parent = p;
        x->left = p;
    }
    x->parent = g;
    p->parent = x;
    if (g != NULL) {
        if (g->left == p) g->left = x;
        else g->right = x;
    }
}

static void splay(SplayNode *x)
{
    while (x->parent != NULL) {
        SplayNode *p = x->parent, *g = p->parent;
        if (g == NULL) rotate_up(x);
        else if ((g->left == p) == (p->left == x)) {
            rotate_up(p); rotate_up(x);
        } else {
            rotate_up(x); rotate_up(x);
        }
    }
}

static void splay_destroy(SplayNode *t)
{
    if (t == NULL) return;
    splay_destroy(t->left); splay_destroy(t->right); free(t);
}

int weiss_run_ch4(int number)
{
    if (number == 3) {
        ChildNode child = {2, NULL, NULL}, root = {1, &child, NULL};
        printf("FirstChild = %d\n", root.first_child->element);
        return 0;
    }
    if (number == 6 || number == 9) {
        DirEntry file2 = {"b.txt", 3, 0, NULL, NULL};
        DirEntry file1 = {"a.txt", 5, 0, NULL, &file2};
        DirEntry root = {"root", 0, 1, &file1, NULL};
        if (number == 6) list_dir(&root, 0);
        else printf("SizeDirectory = %d\n", size_directory(&root));
        return 0;
    }
    if (number == 13 || number == 16 || number == 17 || number == 18 ||
        number == 19 || number == 20 || number == 22 || number == 25 ||
        number == 62 || number == 63) {
        TreeNode *t = NULL;
        tree_insert(4, &t); tree_insert(2, &t); tree_insert(6, &t);
        tree_insert(1, &t); tree_insert(3, &t);
        switch (number) {
        case 13: case 16: printf("Root = %d\n", t->element); break;
        case 17: tree_make_empty(&t); printf("MakeEmpty = %d\n", t == NULL); break;
        case 18: printf("Find = %d\n", tree_find(3, t)->element); break;
        case 19: printf("FindMin = %d\n", tree_find_min(t)->element); break;
        case 20: printf("FindMax = %d\n", tree_find_max(t)->element); break;
        case 22: tree_insert(5, &t); printf("Insert = %d\n", tree_find(5, t)->element); break;
        case 25: tree_delete(2, &t); printf("After Delete: "); tree_print(t); puts(""); break;
        case 62: tree_print(t); puts(""); break;
        case 63: printf("Height = %d\n", tree_height(t)); break;
        default: break;
        }
        tree_make_empty(&t);
        return 0;
    }
    if (number == 37 || number == 38 || number == 39 || number == 41 || number == 43) {
        AvlNode *t = NULL;
        int values[] = {3, 1, 2};
        for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i)
            avl_insert(values[i], &t);
        switch (number) {
        case 37: printf("AVL root = %d\n", t->element); break;
        case 38: printf("Height = %d\n", avl_height(t)); break;
        case 39: printf("AVL Insert root = %d\n", t->element); break;
        case 41: { AvlNode *u = NULL; avl_insert(3, &u); avl_insert(2, &u); avl_insert(1, &u); printf("Single rotation root = %d\n", u->element); avl_destroy(u); break; }
        case 43: printf("Double rotation root = %d\n", t->element); break;
        default: break;
        }
        avl_destroy(t);
        return 0;
    }
    if (number == 56 || number == 57 || number == 58 || number == 59 || number == 61) {
        SplayNode *g = splay_new(3), *p = splay_new(2), *x = splay_new(1);
        g->left = p; p->parent = g; p->left = x; x->parent = p;
        if (number == 56) printf("Splay root = %d\n", g->element);
        else if (number == 58 || number == 59) {
            rotate_up(p);
            printf("Single/ZigLeft root = %d\n", p->element);
        } else {
            splay(x);
            printf("Splay/ZigZigLeft root = %d\n", x->element);
        }
        while (g->parent != NULL) g = g->parent;
        splay_destroy(g);
        return 0;
    }
    fprintf(stderr, "unknown chapter 4 figure: %d\n", number);
    return 1;
}
