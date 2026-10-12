#include <stdio.h>

static long long sum_cubes(int n)
{
    long long sum = 0;
    for (int i = 1; i <= n; ++i) sum += (long long)i * i * i;
    return sum;
}

static long long factorial(int n)
{
    return n <= 1 ? 1 : n * factorial(n - 1);
}

static long long fib(int n)
{
    return n <= 1 ? 1 : fib(n - 1) + fib(n - 2);
}

int weiss_run_pg(int number)
{
    switch (number) {
    case 21: printf("Sum(5) = %lld\n", sum_cubes(5)); return 0;
    case 231: printf("Factorial(5) = %lld\n", factorial(5)); return 0;
    case 232: printf("Fib(8) = %lld\n", fib(8)); return 0;
    default: fprintf(stderr, "unknown preface figure: %d\n", number); return 1;
    }
}
