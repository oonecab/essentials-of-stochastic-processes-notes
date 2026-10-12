#include "../testkit/testkit.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void expect_output(const struct tk_result *result, const char *text)
{
    tk_assert(strstr(result->output, text) != NULL,
              "Expected output to contain: %s", text);
}

SystemTest(fibonacci_zero, 0, "./bin/fig1.2", "0")
{
    expect_output(result, "F(0) = 0");
}

SystemTest(fibonacci_rejects_negative, 1, "./bin/fig1.2", "-1")
{
    expect_output(result, "N 必须是 0 到 60 之间的整数");
}

SystemTest(binary_search_found, 0, "./bin/fig2.9", "3", "1", "3", "5")
{
    expect_output(result, "位置 2");
}

SystemTest(binary_search_missing, 0, "./bin/fig2.9", "4", "1", "3", "5")
{
    expect_output(result, "未找到（返回 0）");
}

SystemTest(binary_search_rejects_unsorted, 1,
           "./bin/fig2.9", "3", "5", "1", "3")
{
    expect_output(result, "数组必须按非降序排列");
}

SystemTest(gcd_with_zero, 0, "./bin/fig2.10", "0", "18")
{
    expect_output(result, "Gcd = 18");
}

SystemTest(gcd_rejects_negative, 1, "./bin/fig2.10", "-1", "18")
{
    expect_output(result, "用法：");
}

SystemTest(power_zero_exponent, 0, "./bin/fig2.11", "-2", "0")
{
    expect_output(result, "Pow = 1");
}

SystemTest(power_negative_base, 0, "./bin/fig2.11", "-2", "3")
{
    expect_output(result, "Pow = -8");
}

SystemTest(power_rejects_overflow, 1, "./bin/fig2.11", "2", "63")
{
    expect_output(result, "超出有符号 64 位整数范围");
}

/* A simple exhaustive oracle checks all four algorithms on varied inputs. */
static int64_t reference_max_sum(const int values[], size_t count)
{
    int64_t best = 0;

    for (size_t start = 0; start < count; ++start) {
        int64_t sum = 0;
        for (size_t end = start; end < count; ++end) {
            sum += values[end];
            if (sum > best) {
                best = sum;
            }
        }
    }
    return best;
}

UnitTest(max_subsequence_variants)
{
    static const struct {
        int values[6];
        size_t count;
    } cases[] = {
        {{-4, -2, -7}, 3},
        {{4, -1, 2, -7, 5}, 5},
        {{0, 0, 0}, 3},
        {{2, -2, 2, -2, 2}, 5},
        {{-1, 5, -2, 5, -10, 3}, 6},
        {{1, 2, 3, 4, 5, 6}, 6},
        {{-3, 4, -1, 2, -4, 6}, 6},
        {{0, -1, 0, 1, -1, 0}, 6},
    };
    static const char *const programs[] = {
        "./bin/fig2.5", "./bin/fig2.6", "./bin/fig2.7", "./bin/fig2.8"
    };

    for (size_t sample = 0; sample < sizeof(cases) / sizeof(cases[0]);
         ++sample) {
        int64_t expected = reference_max_sum(cases[sample].values,
                                             cases[sample].count);
        char numbers[6][24];
        const char *argv[8];

        for (size_t i = 0; i < cases[sample].count; ++i) {
            snprintf(numbers[i], sizeof(numbers[i]), "%d",
                     cases[sample].values[i]);
            argv[i + 1] = numbers[i];
        }
        argv[cases[sample].count + 1] = NULL;

        for (size_t program = 0;
             program < sizeof(programs) / sizeof(programs[0]); ++program) {
            int64_t actual = -1;
            struct tk_result result;

            argv[0] = programs[program];
            result = tk_run_command(argv);
            tk_assert(result.signal_number == 0 && result.exit_status == 0,
                      "%s failed on sample %zu: %s", argv[0], sample,
                      result.output);
            tk_assert(sscanf(result.output, "最大子序列和 = %" SCNd64,
                             &actual) == 1,
                      "%s gave unexpected output: %s", argv[0],
                      result.output);
            tk_assert(actual == expected,
                      "%s sample %zu: expected %" PRId64 ", got %" PRId64,
                      argv[0], sample, expected, actual);
            tk_free_result(&result);
        }
    }
}

int main(int argc, char *argv[])
{
    if (argc == 1) {
        return tk_run_all();
    }
    if (argc == 3 && strcmp(argv[1], "--case") == 0) {
        return tk_run_named(argv[2], 0);
    }
    if (argc == 3 && strcmp(argv[1], "--debug-case") == 0) {
        return tk_run_named(argv[2], 1);
    }
    fprintf(stderr, "用法：%s [--case|--debug-case 用例名]\n", argv[0]);
    return 2;
}
