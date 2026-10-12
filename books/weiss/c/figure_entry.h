#ifndef WEISS_FIGURE_ENTRY_H
#define WEISS_FIGURE_ENTRY_H

#ifndef WEISS_CHAPTER
#error "WEISS_CHAPTER must be defined"
#endif
#ifndef WEISS_NUMBER
#error "WEISS_NUMBER must be defined"
#endif

#if WEISS_CHAPTER == 3
int weiss_run_ch3(int number);
#define WEISS_RUN weiss_run_ch3
#elif WEISS_CHAPTER == 4
int weiss_run_ch4(int number);
#define WEISS_RUN weiss_run_ch4
#elif WEISS_CHAPTER == 5
int weiss_run_ch5(int number);
#define WEISS_RUN weiss_run_ch5
#elif WEISS_CHAPTER == 6
int weiss_run_ch6(int number);
#define WEISS_RUN weiss_run_ch6
#elif WEISS_CHAPTER == 7
int weiss_run_ch7(int number);
#define WEISS_RUN weiss_run_ch7
#elif WEISS_CHAPTER == 8
int weiss_run_ch8(int number);
#define WEISS_RUN weiss_run_ch8
#elif WEISS_CHAPTER == 9
int weiss_run_ch9(int number);
#define WEISS_RUN weiss_run_ch9
#elif WEISS_CHAPTER == 10
int weiss_run_ch10(int number);
#define WEISS_RUN weiss_run_ch10
#elif WEISS_CHAPTER == 12
int weiss_run_ch12(int number);
#define WEISS_RUN weiss_run_ch12
#elif WEISS_CHAPTER == 0
int weiss_run_pg(int number);
#define WEISS_RUN weiss_run_pg
#else
#error "unsupported chapter"
#endif

int main(void)
{
    return WEISS_RUN(WEISS_NUMBER);
}

#endif
