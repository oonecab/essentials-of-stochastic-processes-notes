/* Freestanding-friendly source for native and ELF cross-target inspection. */
int ch07_sum(const int *a, int n);
int ch07_array[2] = {1, 2};
int main(void) {
    return ch07_sum(ch07_array, 2) == 3 ? 0 : 1;
}
