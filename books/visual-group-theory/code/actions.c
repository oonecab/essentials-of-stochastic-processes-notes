/* Three distinct pictures; words execute from left to right. */
#include <stdio.h>
#include <string.h>

enum { POSITIONS = 3, MAX_STATES = 6, WORD_CAPACITY = 7 };
typedef struct {
    int at[POSITIONS];
    char word[WORD_CAPACITY];
} State;

static void step(State *state, char action)
{
    int left = action == 'a' ? 0 : 1;
    int saved = state->at[left];
    state->at[left] = state->at[left + 1];
    state->at[left + 1] = saved;
}

static int same(const State *left, const State *right)
{
    for (int i = 0; i < POSITIONS; ++i)
        if (left->at[i] != right->at[i])
            return 0;
    return 1;
}

static void print_state(const State *state)
{
    for (int i = 0; i < POSITIONS; ++i)
        putchar("ABC"[state->at[i]]);
    putchar('\n');
}

int main(int argc, char **argv)
{
    State states[MAX_STATES] = {{{0, 1, 2}, ""}};
    if (argc > 2) {
        fputs("usage: actions [word of a and b]\n", stderr);
        return 2;
    }
    if (argc == 2) {
        for (const char *p = argv[1]; *p; ++p) {
            if (*p != 'a' && *p != 'b') {
                fputs("word must contain only a and b\n", stderr);
                return 2;
            }
        }
        for (const char *p = argv[1]; *p; ++p)
            step(&states[0], *p);
        print_state(&states[0]);
        return 0;
    }
    int count = 1;
    for (int head = 0; head < count; ++head) {
        const char actions[] = {'a', 'b'};
        for (int k = 0; k < 2; ++k) {
            State target = states[head];
            step(&target, actions[k]);
            int seen = 0;
            for (int i = 0; i < count; ++i)
                if (same(&states[i], &target))
                    seen = 1;
            if (!seen) {
                size_t length = strlen(states[head].word);
                if (count >= MAX_STATES || length + 1 >= WORD_CAPACITY) {
                    fputs("enumeration capacity exceeded\n", stderr);
                    return 1;
                }
                target.word[length] = actions[k];
                target.word[length + 1] = '\0';
                states[count++] = target;
            }
        }
    }
    for (int i = 0; i < count; ++i) {
        printf("%s ", states[i].word[0] ? states[i].word : "e");
        print_state(&states[i]);
    }
    return 0;
}
