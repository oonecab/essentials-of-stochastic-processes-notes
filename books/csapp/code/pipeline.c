#include <stdio.h>
int main(void) {
    /* Three logic stages: 300, 200 and 400 ns; each register costs 20 ns.
       Serial uses one output register; the pipeline has one after each stage. */
    const unsigned int counts[] = {1u, 4u, 10u};
    for (size_t i = 0; i < sizeof counts / sizeof counts[0]; ++i) {
        const unsigned int n = counts[i];
        printf("n=%u seq-ns=%u pipe-cycles=%u pipe-ns=%u\n",
               n, n * 920u, n + 2u, (n + 2u) * 420u);
    }
    /* Five-stage model, four useful instructions and one inserted stall cycle. */
    printf("five-stage=4 instructions,1 stall,9 cycles\n");
    return 0;
}
