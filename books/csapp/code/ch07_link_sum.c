/* Contract: n >= 0, n readable ints, and no signed sum overflow. */
int ch07_sum(const int *a, int n) {
    int total = 0;
    for (int i = 0; i < n; ++i) total += a[i];
    return total;
}
