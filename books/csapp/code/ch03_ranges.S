/* One comparison per implementation; x86-64 scalar float argument in xmm0.
   NEG=0, ZERO=1, POS=2, OTHER=3. Apple symbol spelling is selected by CPP. */
#ifdef __APPLE__
#define BRANCH _ch03_range_branch
#define CMOV _ch03_range_cmov
#else
#define BRANCH ch03_range_branch
#define CMOV ch03_range_cmov
#endif
.text
.globl BRANCH
BRANCH:
    xorps %xmm1, %xmm1
    ucomiss %xmm1, %xmm0
    jp .Lother
    jb .Lnegative
    je .Lzero
    movl $2, %eax
    ret
.Lnegative:
    movl $0, %eax
    ret
.Lzero:
    movl $1, %eax
    ret
.Lother:
    movl $3, %eax
    ret

.globl CMOV
CMOV:
    xorps %xmm1, %xmm1
    movl $2, %eax
    movl $0, %ecx
    movl $1, %edx
    movl $3, %r8d
    ucomiss %xmm1, %xmm0
    cmovb %ecx, %eax
    cmove %edx, %eax
    cmovp %r8d, %eax
    ret
#ifndef __APPLE__
.section .note.GNU-stack,"",@progbits
#endif
