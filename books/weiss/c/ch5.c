#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TABLE_SIZE 11

static size_t hash_sum(const char *key)
{
    size_t sum = 0;
    for (const unsigned char *p = (const unsigned char *)key; *p != 0; ++p)
        sum += *p;
    return sum % TABLE_SIZE;
}

static size_t hash_three(const char *key)
{
    if (strlen(key) < 3) return 0;
    return ((unsigned char)key[0] + 27U * (unsigned char)key[1] +
            729U * (unsigned char)key[2]) % TABLE_SIZE;
}

static size_t hash_shift(const char *key)
{
    size_t value = (unsigned char)key[0];
    for (size_t i = 1; key[i] != '\0'; ++i)
        value = (value * 32U + (unsigned char)key[i]) % TABLE_SIZE;
    return value;
}

typedef struct ChainNode {
    int element;
    struct ChainNode *next;
} ChainNode;
typedef struct { ChainNode *header[TABLE_SIZE]; } ChainTable;

static size_t hash_int(int key)
{
    int remainder = key % TABLE_SIZE;
    return (size_t)(remainder < 0 ? remainder + TABLE_SIZE : remainder);
}

static void chain_initialize(ChainTable *table)
{
    for (int i = 0; i < TABLE_SIZE; ++i) {
        table->header[i] = calloc(1, sizeof(ChainNode));
        if (table->header[i] == NULL) exit(EXIT_FAILURE);
    }
}

static ChainNode *chain_find(int key, const ChainTable *table)
{
    ChainNode *p = table->header[hash_int(key)]->next;
    while (p != NULL && p->element != key) p = p->next;
    return p;
}

static void chain_insert(int key, ChainTable *table)
{
    if (chain_find(key, table) != NULL) return;
    ChainNode *header = table->header[hash_int(key)];
    ChainNode *new_node = malloc(sizeof(*new_node));
    if (new_node == NULL) exit(EXIT_FAILURE);
    new_node->element = key;
    new_node->next = header->next;
    header->next = new_node;
}

static void chain_destroy(ChainTable *table)
{
    for (int i = 0; i < TABLE_SIZE; ++i) {
        ChainNode *p = table->header[i];
        while (p != NULL) {
            ChainNode *next = p->next;
            free(p);
            p = next;
        }
    }
}

typedef enum { EMPTY, LEGITIMATE, DELETED } EntryKind;
typedef struct { int element; EntryKind info; } HashEntry;
typedef struct { HashEntry entries[TABLE_SIZE]; } OpenTable;

static void open_initialize(OpenTable *table)
{
    for (int i = 0; i < TABLE_SIZE; ++i) table->entries[i].info = EMPTY;
}

/* Quadratic probing: positions h, h+1, h+4, ... modulo TABLE_SIZE. */
static int open_find(int key, const OpenTable *table)
{
    size_t base = hash_int(key);
    for (size_t collision = 0; collision < TABLE_SIZE; ++collision) {
        size_t pos = (base + collision * collision) % TABLE_SIZE;
        if (table->entries[pos].info == EMPTY) return (int)pos;
        if (table->entries[pos].info == LEGITIMATE &&
            table->entries[pos].element == key) return (int)pos;
    }
    return -1;
}

static int open_insert(int key, OpenTable *table)
{
    int pos = open_find(key, table);
    if (pos < 0) return 0;
    if (table->entries[pos].info != LEGITIMATE) {
        table->entries[pos].info = LEGITIMATE;
        table->entries[pos].element = key;
    }
    return 1;
}

int weiss_run_ch5(int number)
{
    if (number == 2) { printf("Index range = 0..%d\n", TABLE_SIZE - 1); return 0; }
    if (number == 3) { printf("Hash sum abc = %zu\n", hash_sum("abc")); return 0; }
    if (number == 4) { printf("Hash 3-char abc = %zu\n", hash_three("abc")); return 0; }
    if (number == 5) { printf("Hash shift abc = %zu\n", hash_shift("abc")); return 0; }
    if (number == 7 || number == 8 || number == 9 || number == 10) {
        ChainTable table;
        chain_initialize(&table);
        chain_insert(12, &table);
        chain_insert(23, &table);
        switch (number) {
        case 7: printf("Chain node size = %zu\n", sizeof(ChainNode)); break;
        case 8: printf("Initialized buckets = %d\n", TABLE_SIZE); break;
        case 9: printf("Find 23 = %d\n", chain_find(23, &table)->element); break;
        case 10: chain_insert(34, &table); printf("Insert 34 = %d\n", chain_find(34, &table)->element); break;
        default: break;
        }
        chain_destroy(&table);
        return 0;
    }
    if (number >= 14 && number <= 17) {
        OpenTable table;
        open_initialize(&table);
        open_insert(12, &table); open_insert(23, &table);
        switch (number) {
        case 14: printf("HashEntry size = %zu\n", sizeof(HashEntry)); break;
        case 15: printf("Empty slot = %d\n", table.entries[0].info == EMPTY); break;
        case 16: printf("Find 23 = %d\n", open_find(23, &table)); break;
        case 17: open_insert(34, &table); printf("Insert 34 = %d\n", open_find(34, &table)); break;
        default: break;
        }
        return 0;
    }
    fprintf(stderr, "unknown chapter 5 figure: %d\n", number);
    return 1;
}
