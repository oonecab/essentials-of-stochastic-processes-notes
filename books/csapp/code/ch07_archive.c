/* C11 model of textbook left-to-right archive extraction. */
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>

/* Bits 0..3 denote p, x1, x2, y. All definitions here are unique. */
struct module { const char *name; unsigned defines, uses; };
static const struct module modules[] = {
    {"p", 1U, 2U}, {"x1", 2U, 8U}, {"x2", 4U, 1U}, {"y", 8U, 4U}
};
struct state { unsigned included, defined, unresolved; };

static void include(struct state *s, size_t i) {
    s->included |= 1U << i;
    s->defined |= modules[i].defines;
    s->unresolved = (s->unresolved | modules[i].uses) & ~s->defined;
    printf(" %s", modules[i].name);
}

static void archive(struct state *s, const size_t *members, size_t count) {
    bool changed;
    do {
        changed = false;
        for (size_t k = 0; k < count; ++k) {
            size_t i = members[k];
            if (!(s->included & (1U << i)) &&
                (modules[i].defines & s->unresolved)) {
                include(s, i);
                changed = true;
            }
        }
    } while (changed);
}

static unsigned run(const char *name, const char *order) {
    struct state s = {0, 0, 0};
    const size_t x[] = {2, 1}; /* x2 before x1 forces within-archive iteration */
    const size_t y[] = {3};
    const size_t all[] = {2, 3, 1};
    printf("%s:", name);
    for (; *order; ++order) {
        if (*order == 'p') include(&s, 0);
        else if (*order == 'x') archive(&s, x, 2);
        else if (*order == 'y') archive(&s, y, 1);
        else if (*order == 'a') archive(&s, all, 3);
    }
    printf(" | unresolved=%u\n", s.unresolved);
    return s.unresolved;
}

int main(void) {
    if (run("good", "pxyx") != 0) return 1;
    if (run("one-pass", "pxy") != 4) return 1;
    if (run("early-archive", "xpy") != 2) return 1;
    if (run("combined", "pa") != 0) return 1;
    if (run("empty-input", "") != 0) return 1;
    if (run("unused-libraries", "xy") != 0) return 1;
    return 0;
}
