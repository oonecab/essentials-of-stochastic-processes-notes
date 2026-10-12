#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static void matrix_multiply(const double a[2][2], const double b[2][2], double c[2][2])
{
    for (int i = 0; i < 2; ++i)
        for (int j = 0; j < 2; ++j) {
            c[i][j] = 0.0;
            for (int k = 0; k < 2; ++k) c[i][j] += a[i][k] * b[k][j];
        }
}

static int fib_recursive(int n)
{
    return n <= 1 ? 1 : fib_recursive(n - 1) + fib_recursive(n - 2);
}

static int fib_iterative(int n)
{
    if (n <= 1) return 1;
    int last = 1, next_to_last = 1, answer = 1;
    for (int i = 2; i <= n; ++i) {
        answer = last + next_to_last;
        next_to_last = last;
        last = answer;
    }
    return answer;
}

static double eval_recursive(int n)
{
    if (n == 0) return 1.0;
    double sum = 0.0;
    for (int i = 0; i < n; ++i) sum += eval_recursive(i);
    return 2.0 * sum / n + n;
}

static double eval_dynamic(int n)
{
    double c[16] = {1.0};
    for (int i = 1; i <= n; ++i) {
        double sum = 0.0;
        for (int j = 0; j < i; ++j) sum += c[j];
        c[i] = 2.0 * sum / i + i;
    }
    return c[n];
}

static int optimal_matrix_order(const int *columns, int n, int *first_split)
{
    int cost[5][5] = {{0}}, split[5][5] = {{0}};
    for (int length = 1; length < n; ++length)
        for (int left = 1; left + length <= n; ++left) {
            int right = left + length;
            cost[left][right] = 1000000000;
            for (int k = left; k < right; ++k) {
                int candidate = cost[left][k] + cost[k + 1][right] +
                    columns[left - 1] * columns[k] * columns[right];
                if (candidate < cost[left][right]) {
                    cost[left][right] = candidate;
                    split[left][right] = k;
                }
            }
        }
    *first_split = split[1][n];
    return cost[1][n];
}

#define FLOYD_N 4
#define FLOYD_INF 1000000
static void all_pairs(const int a[FLOYD_N][FLOYD_N], int d[FLOYD_N][FLOYD_N],
                      int path[FLOYD_N][FLOYD_N])
{
    for (int i = 0; i < FLOYD_N; ++i)
        for (int j = 0; j < FLOYD_N; ++j) {
            d[i][j] = a[i][j]; path[i][j] = -1;
        }
    for (int k = 0; k < FLOYD_N; ++k)
        for (int i = 0; i < FLOYD_N; ++i)
            for (int j = 0; j < FLOYD_N; ++j)
                if (d[i][k] != FLOYD_INF && d[k][j] != FLOYD_INF &&
                    d[i][k] + d[k][j] < d[i][j]) {
                    d[i][j] = d[i][k] + d[k][j];
                    path[i][j] = k;
                }
}

#define LCG_A INT64_C(48271)
#define LCG_M INT64_C(2147483647)
static double lcg_direct(int64_t *seed)
{
    *seed = LCG_A * *seed % LCG_M; /* int64 avoids the source's 32-bit overflow. */
    return (double)*seed / (double)LCG_M;
}

static double lcg_schrage(int64_t *seed)
{
    const int64_t q = 44488, r = 3399;
    int64_t tmp = LCG_A * (*seed % q) - r * (*seed / q);
    *seed = tmp >= 0 ? tmp : tmp + LCG_M;
    return (double)*seed / (double)LCG_M;
}

static uint32_t lcg_next_integer(int64_t *seed)
{
    (void)lcg_schrage(seed);
    return (uint32_t)*seed;
}

static uint64_t mod_add(uint64_t a, uint64_t b, uint64_t n)
{
    return a >= n - b ? a - (n - b) : a + b;
}

static uint64_t mod_multiply(uint64_t a, uint64_t b, uint64_t n)
{
    uint64_t result = 0;
    a %= n;
    while (b != 0) {
        if (b & 1U) result = mod_add(result, a, n);
        b >>= 1;
        if (b != 0) a = mod_add(a, a, n);
    }
    return result;
}

static uint64_t modular_power(uint64_t a, uint64_t p, uint64_t n, int *composite)
{
    if (p == 0) return 1;
    uint64_t x = modular_power(a, p / 2, n, composite);
    uint64_t result = mod_multiply(x, x, n);
    if (result == 1 && x != 1 && x != n - 1) *composite = 1;
    if (p & 1U) result = mod_multiply(result, a, n);
    return result;
}

static int probably_prime_one_base(uint64_t n, uint64_t a)
{
    int composite = 0;
    return modular_power(a, n - 1, n, &composite) == 1 && !composite;
}

static int board_full(const char *board)
{
    for (int i = 0; i < 9; ++i) if (board[i] == '.') return 0;
    return 1;
}

static int board_winner(const char *board, char side)
{
    const int lines[8][3] = {
        {0,1,2},{3,4,5},{6,7,8},{0,3,6},
        {1,4,7},{2,5,8},{0,4,8},{2,4,6}
    };
    for (int i = 0; i < 8; ++i)
        if (board[lines[i][0]] == side && board[lines[i][1]] == side &&
            board[lines[i][2]] == side) return 1;
    return 0;
}

static int immediate_win(char *board, char side, int *move)
{
    for (int i = 0; i < 9; ++i)
        if (board[i] == '.') {
            board[i] = side;
            int won = board_winner(board, side);
            board[i] = '.';
            if (won) { *move = i; return 1; }
        }
    return 0;
}

static int human_move(char *board, int *best);

static int comp_move(char *board, int *best)
{
    if (board_full(board)) return 0;
    if (immediate_win(board, 'X', best)) return 1;
    int value = -1;
    *best = -1;
    for (int i = 0; i < 9; ++i)
        if (board[i] == '.') {
            board[i] = 'X';
            int other_best, response = human_move(board, &other_best);
            board[i] = '.';
            if (*best < 0 || response > value) { value = response; *best = i; }
        }
    return value;
}

static int human_move(char *board, int *best)
{
    if (board_full(board)) return 0;
    if (immediate_win(board, 'O', best)) return -1;
    int value = 1;
    *best = -1;
    for (int i = 0; i < 9; ++i)
        if (board[i] == '.') {
            board[i] = 'O';
            int other_best, response = comp_move(board, &other_best);
            board[i] = '.';
            if (*best < 0 || response < value) { value = response; *best = i; }
        }
    return value;
}

static int human_alpha_beta(char *board, int *best, int alpha, int beta);

static int comp_alpha_beta(char *board, int *best, int alpha, int beta)
{
    if (board_full(board)) return 0;
    if (immediate_win(board, 'X', best)) return 1;
    int value = alpha;
    *best = -1;
    for (int i = 0; i < 9 && value < beta; ++i)
        if (board[i] == '.') {
            board[i] = 'X';
            int other_best, response = human_alpha_beta(board, &other_best, value, beta);
            board[i] = '.';
            if (*best < 0 || response > value) { value = response; *best = i; }
        }
    return value;
}

static int human_alpha_beta(char *board, int *best, int alpha, int beta)
{
    if (board_full(board)) return 0;
    if (immediate_win(board, 'O', best)) return -1;
    int value = beta;
    *best = -1;
    for (int i = 0; i < 9 && value > alpha; ++i)
        if (board[i] == '.') {
            board[i] = 'O';
            int other_best, response = comp_alpha_beta(board, &other_best, alpha, value);
            board[i] = '.';
            if (*best < 0 || response < value) { value = response; *best = i; }
        }
    return value;
}

int weiss_run_ch10(int number)
{
    switch (number) {
    case 38: {
        const double a[2][2] = {{1,2},{3,4}}, b[2][2] = {{5,6},{7,8}};
        double c[2][2]; matrix_multiply(a, b, c);
        printf("Matrix product = %.0f %.0f / %.0f %.0f\n", c[0][0], c[0][1], c[1][0], c[1][1]); break;
    }
    case 40: printf("Fib(8) = %d\n", fib_recursive(8)); break;
    case 41: printf("Fibonacci(8) = %d\n", fib_iterative(8)); break;
    case 43: printf("Eval(5) = %.6f\n", eval_recursive(5)); break;
    case 45: printf("Eval(5) = %.6f\n", eval_dynamic(5)); break;
    case 46: {
        int columns[] = {10,20,30,40}, split;
        int cost = optimal_matrix_order(columns, 3, &split);
        printf("Matrix chain cost = %d, first split = %d\n", cost, split); break;
    }
    case 53: {
        const int a[FLOYD_N][FLOYD_N] = {
            {0,3,FLOYD_INF,10},{FLOYD_INF,0,2,FLOYD_INF},
            {FLOYD_INF,FLOYD_INF,0,1},{FLOYD_INF,FLOYD_INF,FLOYD_INF,0}
        };
        int d[FLOYD_N][FLOYD_N], path[FLOYD_N][FLOYD_N];
        all_pairs(a, d, path);
        printf("Shortest 0->3 = %d, via = %d\n", d[0][3], path[0][3]); break;
    }
    case 54: { int64_t seed = 1; printf("Random = %.9f\n", lcg_direct(&seed)); break; }
    case 55: { int64_t seed = 1; printf("Random = %.9f\n", lcg_schrage(&seed)); break; }
    case 62: printf("17 probable prime = %d; 21 composite = %d\n",
                    probably_prime_one_base(17, 2), !probably_prime_one_base(21, 2)); break;
    case 66: case 67: case 73: {
        char board[10] = "XO..X.O..";
        int best = -1;
        int value = number == 67 ? human_move(board, &best) :
                    number == 73 ? comp_alpha_beta(board, &best, -1, 1) :
                                   comp_move(board, &best);
        printf("Best move = %d, value = %d\n", best + 1, value); break;
    }
    case 74: { int64_t seed = 1; uint32_t value = lcg_next_integer(&seed);
               printf("Flip = %s\n", value % 2U == 0 ? "Heads" : "Tails"); break; }
    default: fprintf(stderr, "unknown chapter 10 figure: %d\n", number); return 1;
    }
    return 0;
}
