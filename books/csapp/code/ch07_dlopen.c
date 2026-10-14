/* POSIX dlopen/dlsym demonstration, outside ISO C11's library. */
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fputs("usage: ch07_dlopen library-path\n", stderr);
        return 2;
    }
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) {
        fputs("load failed\n", stderr);
        return 1;
    }
    (void)dlerror();
    void *address = dlsym(handle, "ch07_transform");
    const char *error = dlerror();
    if (error) {
        fputs("symbol lookup failed\n", stderr);
        (void)dlclose(handle);
        return 1;
    }
    int (*transform)(int);
    /* POSIX implementation assumption: equal-size compatible pointer representations. */
    _Static_assert(sizeof transform == sizeof address, "POSIX pointer size");
    memcpy(&transform, &address, sizeof transform);
    int a = transform(35), b = transform(-1), c = transform(101);
    printf("transform(35)=%d boundary(-1)=%d boundary(101)=%d\n", a, b, c);
    int status = a == 42 && b == -1 && c == -1 ? 0 : 1;
    if (dlclose(handle) != 0) return 1;
    return status;
}
