#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

#define VERTICES 5
#define INF (INT_MAX / 4)
typedef struct { int weight[VERTICES][VERTICES]; } Graph;
typedef struct { int known, dist, path; } TableEntry;
typedef struct { TableEntry entry[VERTICES]; } Table;

static void graph_clear(Graph *g)
{
    for (int i = 0; i < VERTICES; ++i)
        for (int j = 0; j < VERTICES; ++j) g->weight[i][j] = 0;
}

static void graph_sample(Graph *g)
{
    graph_clear(g);
    g->weight[0][1] = 2; g->weight[0][2] = 5;
    g->weight[1][2] = 1; g->weight[1][3] = 4;
    g->weight[2][3] = 2; g->weight[3][4] = 1;
}

static void table_init(Table *t, int start)
{
    for (int i = 0; i < VERTICES; ++i) {
        t->entry[i].known = 0;
        t->entry[i].dist = INF;
        t->entry[i].path = -1;
    }
    t->entry[start].dist = 0;
}

static void print_distances(const Table *t)
{
    for (int i = 0; i < VERTICES; ++i)
        printf("%d:%d%s", i, t->entry[i].dist,
               i == VERTICES - 1 ? "\n" : " ");
}

static void print_path(const Table *t, int v)
{
    if (t->entry[v].path >= 0) {
        print_path(t, t->entry[v].path);
        printf(" to ");
    }
    printf("%d", v);
}

static int top_sort_scan(const Graph *g, int *order)
{
    int indegree[VERTICES] = {0}, used[VERTICES] = {0};
    for (int v = 0; v < VERTICES; ++v)
        for (int w = 0; w < VERTICES; ++w)
            if (g->weight[v][w] != 0) ++indegree[w];
    for (int counter = 0; counter < VERTICES; ++counter) {
        int v = -1;
        for (int i = 0; i < VERTICES; ++i)
            if (!used[i] && indegree[i] == 0) { v = i; break; }
        if (v < 0) return 0;
        used[v] = 1; order[counter] = v;
        for (int w = 0; w < VERTICES; ++w)
            if (g->weight[v][w] != 0) --indegree[w];
    }
    return 1;
}

static int top_sort_queue(const Graph *g, int *order)
{
    int indegree[VERTICES] = {0}, queue[VERTICES], front = 0, rear = 0, count = 0;
    for (int v = 0; v < VERTICES; ++v)
        for (int w = 0; w < VERTICES; ++w)
            if (g->weight[v][w] != 0) ++indegree[w];
    for (int v = 0; v < VERTICES; ++v)
        if (indegree[v] == 0) queue[rear++] = v;
    while (front < rear) {
        int v = queue[front++]; order[count++] = v;
        for (int w = 0; w < VERTICES; ++w)
            if (g->weight[v][w] != 0 && --indegree[w] == 0) queue[rear++] = w;
    }
    return count == VERTICES;
}

static void unweighted_scan(const Graph *g, Table *t)
{
    for (int current_dist = 0; current_dist < VERTICES; ++current_dist)
        for (int v = 0; v < VERTICES; ++v)
            if (!t->entry[v].known && t->entry[v].dist == current_dist) {
                t->entry[v].known = 1;
                for (int w = 0; w < VERTICES; ++w)
                    if (g->weight[v][w] != 0 && t->entry[w].dist == INF) {
                        t->entry[w].dist = current_dist + 1;
                        t->entry[w].path = v;
                    }
            }
}

static void unweighted_queue(const Graph *g, Table *t, int start)
{
    int queue[VERTICES], front = 0, rear = 0;
    queue[rear++] = start;
    while (front < rear) {
        int v = queue[front++];
        t->entry[v].known = 1;
        for (int w = 0; w < VERTICES; ++w)
            if (g->weight[v][w] != 0 && t->entry[w].dist == INF) {
                t->entry[w].dist = t->entry[v].dist + 1;
                t->entry[w].path = v;
                queue[rear++] = w;
            }
    }
}

static void dijkstra(const Graph *g, Table *t)
{
    for (int i = 0; i < VERTICES; ++i) {
        int v = -1;
        for (int j = 0; j < VERTICES; ++j)
            if (!t->entry[j].known &&
                (v < 0 || t->entry[j].dist < t->entry[v].dist)) v = j;
        if (v < 0 || t->entry[v].dist == INF) break;
        t->entry[v].known = 1;
        for (int w = 0; w < VERTICES; ++w)
            if (g->weight[v][w] != 0 && !t->entry[w].known &&
                t->entry[v].dist + g->weight[v][w] < t->entry[w].dist) {
                t->entry[w].dist = t->entry[v].dist + g->weight[v][w];
                t->entry[w].path = v;
            }
    }
}

static int weighted_negative(const Graph *g, Table *t, int start)
{
    int queue[VERTICES * VERTICES], in_queue[VERTICES] = {0};
    int relax_count[VERTICES] = {0}, front = 0, rear = 0;
    queue[rear++] = start; in_queue[start] = 1;
    while (front < rear) {
        int v = queue[front++]; in_queue[v] = 0;
        for (int w = 0; w < VERTICES; ++w)
            if (g->weight[v][w] != 0 && t->entry[v].dist != INF &&
                t->entry[v].dist + g->weight[v][w] < t->entry[w].dist) {
                t->entry[w].dist = t->entry[v].dist + g->weight[v][w];
                t->entry[w].path = v;
                if (++relax_count[w] >= VERTICES) return 0;
                if (!in_queue[w]) {
                    if (rear >= VERTICES * VERTICES) return 0;
                    queue[rear++] = w; in_queue[w] = 1;
                }
            }
    }
    return 1;
}

static void dfs(const Graph *g, int v, int *visited)
{
    visited[v] = 1;
    for (int w = 0; w < VERTICES; ++w)
        if (g->weight[v][w] != 0 && !visited[w]) dfs(g, w, visited);
}

static void assign_num(const Graph *g, int v, int *visited,
                       int *number, int *parent, int *counter)
{
    visited[v] = 1;
    number[v] = (*counter)++;
    for (int w = 0; w < VERTICES; ++w)
        if (g->weight[v][w] != 0 && !visited[w]) {
            parent[w] = v;
            assign_num(g, w, visited, number, parent, counter);
        }
}

static void articulation_dfs(const Graph *g, int v, int *visited, int *number,
                             int *low, int *parent, int *cut, int *counter)
{
    int children = 0;
    visited[v] = 1;
    number[v] = low[v] = (*counter)++;
    for (int w = 0; w < VERTICES; ++w) {
        if (g->weight[v][w] == 0) continue;
        if (!visited[w]) {
            parent[w] = v; ++children;
            articulation_dfs(g, w, visited, number, low, parent, cut, counter);
            if (low[w] < low[v]) low[v] = low[w];
            if (parent[v] < 0 && children > 1) cut[v] = 1;
            if (parent[v] >= 0 && low[w] >= number[v]) cut[v] = 1;
        } else if (w != parent[v] && number[w] < low[v]) low[v] = number[w];
    }
}

typedef struct { int u, v, weight; } Edge;
static int edge_compare(const void *a, const void *b)
{
    const Edge *x = a, *y = b;
    return (x->weight > y->weight) - (x->weight < y->weight);
}
static int set_find(int x, int *parent)
{
    if (parent[x] == x) return x;
    parent[x] = set_find(parent[x], parent);
    return parent[x];
}

static int kruskal(const Graph *g)
{
    Edge edges[VERTICES * (VERTICES - 1) / 2];
    int count = 0, parent[VERTICES], accepted = 0, total = 0;
    for (int u = 0; u < VERTICES; ++u) {
        parent[u] = u;
        for (int v = u + 1; v < VERTICES; ++v)
            if (g->weight[u][v] != 0)
                edges[count++] = (Edge){u, v, g->weight[u][v]};
    }
    qsort(edges, (size_t)count, sizeof(edges[0]), edge_compare);
    for (int i = 0; i < count && accepted < VERTICES - 1; ++i) {
        int u = set_find(edges[i].u, parent), v = set_find(edges[i].v, parent);
        if (u != v) { parent[v] = u; total += edges[i].weight; ++accepted; }
    }
    return accepted == VERTICES - 1 ? total : -1;
}

int weiss_run_ch9(int number)
{
    Graph g; Table t;
    graph_sample(&g);
    table_init(&t, 0);
    if (number == 5 || number == 7) {
        int order[VERTICES], ok = number == 5 ? top_sort_scan(&g, order) : top_sort_queue(&g, order);
        if (!ok) { puts("graph has a cycle"); return 1; }
        printf("Topological order:");
        for (int i = 0; i < VERTICES; ++i) printf(" %d", order[i]);
        puts(""); return 0;
    }
    if (number == 16 || number == 18) {
        if (number == 16) unweighted_scan(&g, &t);
        else unweighted_queue(&g, &t, 0);
        print_distances(&t); return 0;
    }
    if (number == 29) { printf("Table entries = %d\n", VERTICES); return 0; }
    if (number == 30) { printf("Start distance = %d\n", t.entry[0].dist); return 0; }
    if (number == 31 || number == 32) {
        dijkstra(&g, &t);
        if (number == 31) { print_path(&t, 4); puts(""); }
        else print_distances(&t);
        return 0;
    }
    if (number == 33) {
        g.weight[1][3] = -1;
        if (!weighted_negative(&g, &t, 0)) return 1;
        print_distances(&t); return 0;
    }
    if (number == 58) { printf("Kruskal total weight = %d\n", kruskal(&g)); return 0; }
    if (number == 59) {
        int visited[VERTICES] = {0};
        dfs(&g, 0, visited);
        printf("DFS visited = %d\n", visited[4]); return 0;
    }
    if (number == 65) {
        int visited[VERTICES] = {0}, num[VERTICES] = {0};
        int parent[VERTICES] = {-1, -1, -1, -1, -1}, counter = 0;
        assign_num(&g, 0, visited, num, parent, &counter);
        printf("Num[4] = %d, Parent[4] = %d\n", num[4], parent[4]); return 0;
    }
    if (number == 66 || number == 67) {
        int visited[VERTICES] = {0}, num[VERTICES] = {0}, low[VERTICES] = {0};
        int parent[VERTICES] = {-1, -1, -1, -1, -1}, cut[VERTICES] = {0}, counter = 0;
        graph_clear(&g);
        g.weight[0][1] = g.weight[1][0] = 1;
        g.weight[1][2] = g.weight[2][1] = 1;
        g.weight[1][3] = g.weight[3][1] = 1;
        g.weight[3][4] = g.weight[4][3] = 1;
        articulation_dfs(&g, 0, visited, num, low, parent, cut, &counter);
        printf("Articulation vertices:");
        for (int i = 0; i < VERTICES; ++i) if (cut[i]) printf(" %d", i);
        puts(""); return 0;
    }
    fprintf(stderr, "unknown chapter 9 figure: %d\n", number);
    return 1;
}
