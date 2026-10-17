/* Exact (x,y) -> (sx*x+dx, sy*y). At most 10000 actions avoids overflow. */
#include <stdio.h>
#include <string.h>

static int valid(const char *word) {
    if (strlen(word) > 10000) return 0;
    for (const char *p = word; *p; ++p) if (*p != 'h' && *p != 'g' && *p != 'G') return 0;
    return 1;
}

static void show(const char *word) {
    int sx = 1, sy = 1, dx = 0;
    for (const char *p = word; *p; ++p) {
        if (*p == 'h') { sx = -sx; dx = -dx; }
        else { sy = -sy; dx += *p == 'g' ? 1 : -1; }
    }
    printf("%s %d %d %d\n", *word ? word : "e", sx, sy, dx);
}

int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && !valid(argv[1]))) {
        fputs("usage: frieze [word of at most 10000 letters from h,g,G]\n", stderr);
        return 2;
    }
    puts("word sx sy dx");
    if (argc == 2) show(argv[1]);
    else {
        const char *words[] = {"", "h", "g", "G", "gg", "hgh", "hghg", "ghgh"};
        for (size_t i = 0; i < sizeof words / sizeof words[0]; ++i) show(words[i]);
    }
    return 0;
}
