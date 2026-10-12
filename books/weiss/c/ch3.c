#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct ListNode {
    int element;
    struct ListNode *next;
} ListNode;

static ListNode *list_new(int value, ListNode *next)
{
    ListNode *p = malloc(sizeof(*p));
    if (p == NULL) {
        fprintf(stderr, "out of memory\n");
        exit(EXIT_FAILURE);
    }
    p->element = value;
    p->next = next;
    return p;
}

static ListNode *list_sample(void)
{
    ListNode *header = list_new(0, NULL);
    header->next = list_new(1, list_new(2, list_new(3, NULL)));
    return header;
}

static int list_is_empty(const ListNode *header) { return header->next == NULL; }
static int list_is_last(const ListNode *p) { return p->next == NULL; }

/* fig3.10: the goto leaves the search at the first matching node. */
static ListNode *list_find_goto(int x, ListNode *header)
{
    ListNode *p = header->next;
    while (p != NULL) {
        if (p->element == x) goto found;
        p = p->next;
    }
found:
    return p;
}

static ListNode *list_find_while(int x, ListNode *header)
{
    ListNode *p = header->next;
    while (p != NULL && p->element != x) p = p->next;
    return p;
}

static ListNode *list_find_flag(int x, ListNode *header)
{
    ListNode *p = header->next;
    int found = 0;
    while (p != NULL && !found) {
        if (p->element == x) found = 1;
        else p = p->next;
    }
    return p;
}

static ListNode *list_find_previous(int x, ListNode *header)
{
    ListNode *p = header;
    while (p->next != NULL && p->next->element != x) p = p->next;
    return p;
}

static void list_insert(int x, ListNode *p)
{
    p->next = list_new(x, p->next);
}

static void list_delete(int x, ListNode *header)
{
    ListNode *p = list_find_previous(x, header);
    if (p->next != NULL) {
        ListNode *old = p->next;
        p->next = old->next;
        free(old);
    }
}

/* fig3.16 is unsafe as printed: save Next before free, as in fig3.17. */
static void list_delete_all(ListNode *header)
{
    ListNode *p = header->next;
    header->next = NULL;
    while (p != NULL) {
        ListNode *next = p->next;
        free(p);
        p = next;
    }
}

static void list_print_recursive(const ListNode *p)
{
    if (p != NULL) {
        printf("%d ", p->element);
        list_print_recursive(p->next);
    }
}

static void list_print_iterative(const ListNode *p)
{
    while (p != NULL) {
        printf("%d ", p->element);
        p = p->next;
    }
}

#define MAX_DEGREE 8
typedef struct {
    int coeff[MAX_DEGREE + 1];
    int high_power;
} Polynomial;

static void poly_zero(Polynomial *p)
{
    for (int i = 0; i <= MAX_DEGREE; ++i) p->coeff[i] = 0;
    p->high_power = 0;
}

static void poly_add(const Polynomial *a, const Polynomial *b, Polynomial *sum)
{
    poly_zero(sum);
    sum->high_power = a->high_power > b->high_power ? a->high_power : b->high_power;
    for (int i = sum->high_power; i >= 0; --i) sum->coeff[i] = a->coeff[i] + b->coeff[i];
}

static int poly_multiply(const Polynomial *a, const Polynomial *b, Polynomial *product)
{
    poly_zero(product);
    if (a->high_power + b->high_power > MAX_DEGREE) return 0;
    product->high_power = a->high_power + b->high_power;
    for (int i = 0; i <= a->high_power; ++i)
        for (int j = 0; j <= b->high_power; ++j)
            product->coeff[i + j] += a->coeff[i] * b->coeff[j];
    return 1;
}

typedef struct PolyNode {
    int coefficient, exponent;
    struct PolyNode *next;
} PolyNode;

#define CURSOR_SIZE 32
typedef struct { int element, next; } CursorNode;
static CursorNode cursor_space[CURSOR_SIZE + 1];

static void cursor_init(void)
{
    for (int i = 0; i < CURSOR_SIZE; ++i) cursor_space[i].next = i + 1;
    cursor_space[CURSOR_SIZE].next = 0;
}

static int cursor_new(void)
{
    int p = cursor_space[0].next;
    if (p != 0) cursor_space[0].next = cursor_space[p].next;
    return p;
}

static void cursor_dispose(int p)
{
    cursor_space[p].next = cursor_space[0].next;
    cursor_space[0].next = p;
}

static int cursor_is_empty(int header) { return cursor_space[header].next == 0; }
static int cursor_is_last(int p) { return cursor_space[p].next == 0; }

static int cursor_find(int x, int header)
{
    int p = cursor_space[header].next;
    while (p != 0 && cursor_space[p].element != x) p = cursor_space[p].next;
    return p;
}

static int cursor_find_previous(int x, int header)
{
    int p = header;
    while (cursor_space[p].next != 0 && cursor_space[cursor_space[p].next].element != x)
        p = cursor_space[p].next;
    return p;
}

static int cursor_insert(int x, int p)
{
    int new_node = cursor_new();
    if (new_node == 0) return 0;
    cursor_space[new_node].element = x;
    cursor_space[new_node].next = cursor_space[p].next;
    cursor_space[p].next = new_node;
    return new_node;
}

static void cursor_delete(int x, int header)
{
    int p = cursor_find_previous(x, header);
    if (cursor_space[p].next != 0) {
        int old = cursor_space[p].next;
        cursor_space[p].next = cursor_space[old].next;
        cursor_dispose(old);
    }
}

typedef struct StackNode {
    int element;
    struct StackNode *next;
} StackNode;

static int linked_stack_is_empty(const StackNode *s) { return s == NULL; }
static void linked_stack_make_empty(StackNode **s) { *s = NULL; }

static void linked_stack_push(int x, StackNode **s)
{
    StackNode *node = malloc(sizeof(*node));
    if (node == NULL) exit(EXIT_FAILURE);
    node->element = x;
    node->next = *s;
    *s = node;
}

static int linked_stack_top(const StackNode *s) { return s->element; }

static void linked_stack_pop(StackNode **s)
{
    StackNode *old = *s;
    *s = old->next;
    free(old);
}

#define STACK_SIZE 16
typedef struct { int top; int values[STACK_SIZE + 1]; } ArrayStack;
static int array_stack_is_empty(const ArrayStack *s) { return s->top == 0; }
static void array_stack_make_empty(ArrayStack *s) { s->top = 0; }
static int array_stack_is_full(const ArrayStack *s) { return s->top == STACK_SIZE; }
static int array_stack_push(int x, ArrayStack *s)
{
    if (array_stack_is_full(s)) return 0;
    s->values[++s->top] = x;
    return 1;
}
static int array_stack_top(const ArrayStack *s) { return s->values[s->top]; }
static void array_stack_pop(ArrayStack *s) { --s->top; }
static int array_stack_pop_value(ArrayStack *s) { return s->values[s->top--]; }

#define QUEUE_SIZE 16
typedef struct {
    int front, rear, size;
    int values[QUEUE_SIZE + 1];
} Queue;
static int queue_is_empty(const Queue *q) { return q->size == 0; }
static void queue_make_empty(Queue *q)
{
    q->size = 0;
    q->front = 1;
    q->rear = QUEUE_SIZE;
}
static void queue_increment(int *index)
{
    *index = *index == QUEUE_SIZE ? 1 : *index + 1;
}
static int queue_enqueue(int x, Queue *q)
{
    if (q->size == QUEUE_SIZE) return 0;
    ++q->size;
    queue_increment(&q->rear);
    q->values[q->rear] = x;
    return 1;
}

int weiss_run_ch3(int number)
{
    if (number == 6 || (number >= 8 && number <= 17) || number == 54 || number == 55) {
        ListNode *header = list_sample();
        ListNode *p = header->next;
        switch (number) {
        case 6: printf("List node size = %zu\n", sizeof(*p)); break;
        case 8: printf("IsEmpty = %d\n", list_is_empty(header)); break;
        case 9: printf("IsLast = %d\n", list_is_last(p->next->next)); break;
        case 10: printf("Find = %d\n", list_find_goto(2, header)->element); break;
        case 11: printf("Find = %d\n", list_find_while(2, header)->element); break;
        case 12: printf("Find = %d\n", list_find_flag(2, header)->element); break;
        case 13: list_delete(2, header); printf("After Delete: "); list_print_iterative(header->next); puts(""); break;
        case 14: printf("FindPrevious = %d\n", list_find_previous(2, header)->element); break;
        case 15: list_insert(4, p); printf("After Insert: "); list_print_iterative(header->next); puts(""); break;
        case 16: case 17: list_delete_all(header); printf("IsEmpty = %d\n", list_is_empty(header)); break;
        case 54: list_print_recursive(header->next); puts(""); break;
        case 55: list_print_iterative(header->next); puts(""); break;
        default: break;
        }
        list_delete_all(header);
        free(header);
        return 0;
    }
    if (number >= 20 && number <= 25) {
        Polynomial a, b, result;
        poly_zero(&a); poly_zero(&b);
        a.coeff[0] = 1; a.coeff[1] = 2; a.high_power = 1;
        b.coeff[0] = 3; b.coeff[1] = 1; b.high_power = 1;
        switch (number) {
        case 20: printf("Polynomial degree = %d\n", a.high_power); break;
        case 21: poly_zero(&a); printf("ZeroPolynomial = %d\n", a.coeff[1]); break;
        case 22: poly_add(&a, &b, &result); printf("AddPolynomial = %d + %dx\n", result.coeff[0], result.coeff[1]); break;
        case 23: poly_multiply(&a, &b, &result); printf("MultPolynomial = %d + %dx + %dx^2\n", result.coeff[0], result.coeff[1], result.coeff[2]); break;
        case 25: { PolyNode node = {2, 1, NULL}; printf("Linked polynomial term = %dx^%d\n", node.coefficient, node.exponent); break; }
        default: return 1;
        }
        return 0;
    }
    if (number == 30 || number == 32 || (number >= 34 && number <= 38)) {
        cursor_init();
        int header = cursor_new();
        cursor_space[header].next = 0;
        int first = cursor_insert(1, header);
        cursor_insert(2, first);
        switch (number) {
        case 30: printf("Cursor list header = %d\n", header); break;
        case 32: { int temp = cursor_new(); cursor_dispose(temp); printf("CursorNew/Dispose = %d\n", temp); break; }
        case 34: printf("IsEmpty = %d\n", cursor_is_empty(header)); break;
        case 35: printf("IsLast = %d\n", cursor_is_last(cursor_find(2, header))); break;
        case 36: printf("Find = %d\n", cursor_find(2, header)); break;
        case 37: cursor_delete(2, header); printf("After Delete, Find = %d\n", cursor_find(2, header)); break;
        case 38: printf("Insert = %d\n", cursor_insert(3, first)); break;
        default: return 1;
        }
        return 0;
    }
    if (number >= 41 && number <= 46) {
        StackNode *s = NULL;
        linked_stack_push(1, &s); linked_stack_push(2, &s);
        switch (number) {
        case 41: printf("Linked stack node size = %zu\n", sizeof(*s)); break;
        case 42: printf("IsEmpty = %d\n", linked_stack_is_empty(s)); break;
        case 43: linked_stack_pop(&s); linked_stack_pop(&s); linked_stack_make_empty(&s); printf("IsEmpty = %d\n", linked_stack_is_empty(s)); break;
        case 44: printf("After Push, Top = %d\n", linked_stack_top(s)); break;
        case 45: printf("Top = %d\n", linked_stack_top(s)); break;
        case 46: linked_stack_pop(&s); printf("After Pop, Top = %d\n", linked_stack_top(s)); break;
        default: return 1;
        }
        while (s != NULL) linked_stack_pop(&s);
        return 0;
    }
    if (number >= 47 && number <= 53) {
        ArrayStack s;
        array_stack_make_empty(&s);
        array_stack_push(1, &s); array_stack_push(2, &s);
        switch (number) {
        case 47: printf("Array stack capacity = %d\n", STACK_SIZE); break;
        case 48: printf("IsEmpty = %d\n", array_stack_is_empty(&s)); break;
        case 49: array_stack_make_empty(&s); printf("IsEmpty = %d\n", array_stack_is_empty(&s)); break;
        case 50: printf("After Push, Top = %d\n", array_stack_top(&s)); break;
        case 51: printf("Top = %d\n", array_stack_top(&s)); break;
        case 52: array_stack_pop(&s); printf("After Pop, Top = %d\n", array_stack_top(&s)); break;
        case 53: printf("Pop with value = %d\n", array_stack_pop_value(&s)); break;
        default: return 1;
        }
        return 0;
    }
    if (number >= 57 && number <= 60) {
        Queue q;
        queue_make_empty(&q);
        switch (number) {
        case 57: printf("Queue capacity = %d\n", QUEUE_SIZE); break;
        case 58: printf("IsEmpty = %d\n", queue_is_empty(&q)); break;
        case 59: queue_enqueue(1, &q); queue_make_empty(&q); printf("IsEmpty = %d\n", queue_is_empty(&q)); break;
        case 60: queue_enqueue(1, &q); queue_enqueue(2, &q); printf("Enqueue: front=%d rear=%d size=%d\n", q.values[q.front], q.values[q.rear], q.size); break;
        default: return 1;
        }
        return 0;
    }
    fprintf(stderr, "unknown chapter 3 figure: %d\n", number);
    return 1;
}
