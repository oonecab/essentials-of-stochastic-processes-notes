#include <stdio.h>

int weiss_run_ch12_splay(int number);
int weiss_run_ch12_redblack(int number);
int weiss_run_ch12_skip(int number);
int weiss_run_ch12_aa(int number);
int weiss_run_ch12_treap(int number);
int weiss_run_ch12_kd(int number);
int weiss_run_ch12_pair(int number);

int weiss_run_ch12(int number)
{
    if (number >= 5 && number <= 8) return weiss_run_ch12_splay(number);
    if (number >= 13 && number <= 16) return weiss_run_ch12_redblack(number);
    if (number >= 23 && number <= 25) return weiss_run_ch12_skip(number);
    if (number == 27 || number == 29 || number == 36 || number == 38)
        return weiss_run_ch12_aa(number);
    if (number >= 39 && number <= 41) return weiss_run_ch12_treap(number);
    if (number == 43 || number == 44 || number == 47 || number == 49)
        return weiss_run_ch12_kd(number);
    if (number >= 53 && number <= 56) return weiss_run_ch12_pair(number);
    fprintf(stderr, "unknown chapter 12 figure: %d\n", number);
    return 1;
}
