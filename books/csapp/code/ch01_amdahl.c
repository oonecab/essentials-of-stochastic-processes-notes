#include <stdio.h>

static double speedup(double fraction, double factor) {
    return 1.0 / ((1.0 - fraction) + fraction / factor);
}

int main(void) {
    const double fraction = 0.6;
    const double factors[] = {1.0, 1.5, 3.0, 10.0};
    for (size_t i = 0; i < sizeof factors / sizeof factors[0]; ++i)
        printf("alpha=%.1f k=%.1f speedup=%.6f\n",
               fraction, factors[i], speedup(fraction, factors[i]));
    printf("limit=%.6f\n", 1.0 / (1.0 - fraction));
    const double target = 4.0, improved_fraction = 0.9;
    const double denominator = 1.0 / target - (1.0 - improved_fraction);
    if (denominator <= 0.0) return 1;
    printf("required-k=%.6f\n", improved_fraction / denominator);
    return 0;
}
