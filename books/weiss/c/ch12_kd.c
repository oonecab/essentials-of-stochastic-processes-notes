#include <stdio.h>
#include <stdlib.h>

typedef struct { int coord[2]; } Point;
typedef struct KdNode {
    Point point;
    struct KdNode *left, *right;
} KdNode;

static KdNode *kd_insert(Point point, KdNode *root, int axis)
{
    if (root == NULL) {
        KdNode *node = calloc(1, sizeof(*node));
        if (node == NULL) exit(EXIT_FAILURE);
        node->point = point;
        return node;
    }
    if (point.coord[axis] < root->point.coord[axis])
        root->left = kd_insert(point, root->left, 1 - axis);
    else root->right = kd_insert(point, root->right, 1 - axis);
    return root;
}

static int kd_print_range(const Point *low, const Point *high,
                          const KdNode *root, int axis)
{
    if (root == NULL) return 0;
    int count = 0;
    if (low->coord[0] <= root->point.coord[0] &&
        low->coord[1] <= root->point.coord[1] &&
        high->coord[0] >= root->point.coord[0] &&
        high->coord[1] >= root->point.coord[1]) {
        printf("(%d,%d) ", root->point.coord[0], root->point.coord[1]);
        ++count;
    }
    if (low->coord[axis] <= root->point.coord[axis])
        count += kd_print_range(low, high, root->left, 1 - axis);
    if (high->coord[axis] >= root->point.coord[axis])
        count += kd_print_range(low, high, root->right, 1 - axis);
    return count;
}

static void kd_destroy(KdNode *root)
{
    if (root == NULL) return;
    kd_destroy(root->left); kd_destroy(root->right); free(root);
}

#define KD_HEAP_CAPACITY 32
typedef struct { Point element[KD_HEAP_CAPACITY + 1]; int size; } KdHeap;

static int branching_axis(int index)
{
    int depth = 0;
    while (index > 1) { index /= 2; ++depth; }
    return depth % 2;
}

static void point_swap(Point *a, Point *b) { Point tmp = *a; *a = *b; *b = tmp; }

static int kd_heap_insert(Point item, KdHeap *heap)
{
    if (heap->size == KD_HEAP_CAPACITY) return 0;
    int current = ++heap->size;
    heap->element[current] = item;
    while (current > 1) {
        int parent = current / 2, axis = branching_axis(parent);
        if (heap->element[parent].coord[axis] <= heap->element[current].coord[axis]) break;
        point_swap(&heap->element[parent], &heap->element[current]);
        current = parent;
    }
    return 1;
}

static void sift_down(KdHeap *heap, int current)
{
    while (2 * current <= heap->size) {
        int child = 2 * current, axis = branching_axis(current);
        if (child + 1 <= heap->size &&
            heap->element[child + 1].coord[axis] < heap->element[child].coord[axis])
            ++child;
        if (heap->element[current].coord[axis] <= heap->element[child].coord[axis]) break;
        point_swap(&heap->element[current], &heap->element[child]);
        current = child;
    }
}

/* The source leaves FindMin/GetBranching undefined; this bounded demo scans
   for the chosen coordinate, then rebuilds the alternating-key heap. */
static int kd_heap_delete_min(KdHeap *heap, int axis, Point *minimum)
{
    if (heap->size == 0 || axis < 0 || axis > 1) return 0;
    int pos = 1;
    for (int i = 2; i <= heap->size; ++i)
        if (heap->element[i].coord[axis] < heap->element[pos].coord[axis]) pos = i;
    *minimum = heap->element[pos];
    heap->element[pos] = heap->element[heap->size--];
    for (int i = heap->size / 2; i >= 1; --i) sift_down(heap, i);
    return 1;
}

int weiss_run_ch12_kd(int number)
{
    Point points[] = {{{5,9}},{{2,4}},{{8,1}},{{1,7}}};
    if (number == 43 || number == 44) {
        KdNode *root = NULL;
        for (size_t i = 0; i < sizeof(points) / sizeof(points[0]); ++i)
            root = kd_insert(points[i], root, 0);
        if (number == 43) printf("KdTree root = (%d,%d)\n",
                                 root->point.coord[0], root->point.coord[1]);
        else {
            Point low = {{1,1}}, high = {{5,8}};
            printf("Range points: ");
            int count = kd_print_range(&low, &high, root, 0);
            printf("(count=%d)\n", count);
        }
        kd_destroy(root);
        return 0;
    }
    if (number == 47 || number == 49) {
        KdHeap heap = {0};
        for (size_t i = 0; i < sizeof(points) / sizeof(points[0]); ++i)
            kd_heap_insert(points[i], &heap);
        if (number == 47) printf("KdHeap size = %d\n", heap.size);
        else {
            Point minimum;
            kd_heap_delete_min(&heap, 0, &minimum);
            printf("DeleteMin x = (%d,%d)\n", minimum.coord[0], minimum.coord[1]);
        }
        return 0;
    }
    fprintf(stderr, "unknown Kd figure: %d\n", number);
    return 1;
}
