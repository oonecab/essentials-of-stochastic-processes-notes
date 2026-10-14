/* Text-line interface: embedded NUL is outside the input contract. */
#include <stdio.h>
#include <string.h>

static int good_echo(void)
{
    char buf[256];
    while (fgets(buf,sizeof buf,stdin)!=NULL) {
        if (fputs(buf,stdout)==EOF) return 3;
        if (strchr(buf,'\n')!=NULL) return fflush(stdout)==EOF?3:0;
    }
    if (ferror(stdin)) return 3;
    return fflush(stdout)==EOF?3:0;
}

int main(void)
{
    return good_echo();
}
