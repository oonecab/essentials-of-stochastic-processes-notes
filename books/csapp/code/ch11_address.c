#define _POSIX_C_SOURCE 200809L
/* C11 + POSIX sockets; defaults perform numeric loopback conversion only. */
#include <arpa/inet.h>
#include <errno.h>
#include <inttypes.h>
#include <netdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int number(const char *s, int base, uint32_t limit, uint32_t *out) {
    const char *digits = s;
    if (base == 16 && s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) digits += 2;
    if (!*digits) return 0;
    for (const char *p = digits; *p; ++p) {
        int valid = (*p >= '0' && *p <= '9') ||
            (base == 16 && ((*p >= 'a' && *p <= 'f') || (*p >= 'A' && *p <= 'F')));
        if (!valid) return 0;
    }
    char *end; errno = 0;
    uintmax_t n = strtoumax(s, &end, base);
    if (errno || *end || n > limit) return 0;
    *out = (uint32_t)n; return 1;
}
static int hostinfo(const char *host) {
    struct addrinfo hints = {0}, *list = NULL;
    hints.ai_family = AF_INET; hints.ai_socktype = SOCK_STREAM;
    int rc = getaddrinfo(host, NULL, &hints, &list);
    if (rc) { fprintf(stderr, "%s\n", gai_strerror(rc)); return 2; }
    for (struct addrinfo *p = list; p; p = p->ai_next) {
        const struct sockaddr_in *a = (const struct sockaddr_in *)p->ai_addr;
        char text[INET_ADDRSTRLEN];
        if (!inet_ntop(AF_INET, &a->sin_addr, text, sizeof(text))) {
            freeaddrinfo(list); return 2;
        }
        puts(text);
    }
    freeaddrinfo(list); return 0;
}
int main(int argc, char **argv) {
    uint32_t n;
    if (argc == 3) {
        if (!strcmp(argv[1], "hostinfo")) return hostinfo(argv[2]);
        if (!strcmp(argv[1], "hex2dd") && number(argv[2], 16, UINT16_MAX, &n)) {
            uint16_t wire = htons((uint16_t)n);
            printf("%u\n", (unsigned)ntohs(wire)); return 0;
        }
        if (!strcmp(argv[1], "dd2hex") && number(argv[2], 10, UINT16_MAX, &n)) {
            uint16_t wire = htons((uint16_t)n);
            printf("0x%x\n", (unsigned)ntohs(wire)); return 0;
        }
        if (!strcmp(argv[1], "ipv4hex")) {
            struct in_addr a;
            if (inet_pton(AF_INET, argv[2], &a) == 1) {
                printf("0x%08" PRIX32 "\n", ntohl(a.s_addr)); return 0;
            }
        }
        if (!strcmp(argv[1], "hexipv4") && number(argv[2], 16, UINT32_MAX, &n)) {
            struct in_addr a = {.s_addr = htonl(n)};
            char buf[INET_ADDRSTRLEN];
            if (inet_ntop(AF_INET, &a, buf, sizeof(buf))) { puts(buf); return 0; }
        }
        fputs("invalid input\n", stderr); return 2;
    }
    if (argc != 1) { fputs("usage: ch11_address MODE VALUE\n", stderr); return 2; }
    const char *samples[] = {"107.212.122.205", "64.12.149.13", "107.212.96.29",
                            "0.0.0.128", "255.255.255.0", "10.1.1.64"};
    for (size_t i = 0; i < sizeof(samples) / sizeof(*samples); ++i) {
        struct in_addr a;
        if (inet_pton(AF_INET, samples[i], &a) != 1) return 1;
        printf("%s = 0x%08" PRIX32 "\n", samples[i], ntohl(a.s_addr));
    }
    uint16_t wire = htons(1024);
    unsigned char bytes[2]; memcpy(bytes, &wire, sizeof(bytes));
    printf("port=1024 wire=%02x %02x\n", bytes[0], bytes[1]);
    return hostinfo("127.0.0.1");
}
