#!/usr/bin/env python3
"""Independent boundary checks for Part III; all artifacts stay in run_dir."""
from __future__ import annotations
import errno
import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def module(path):
    spec = importlib.util.spec_from_file_location('part3_' + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_tfgets_cleanup(base, run, compiler='clang'):
    """Exercise inherited signal state with ready input and an owned timer child."""
    run.mkdir(parents=True, exist_ok=True)
    source = base/'code/ch12_tfgets.c'
    harness_text = r'''
#define main original_demo_main
#include "SOURCE"
#undef main
static volatile sig_atomic_t unexpected_signal;
static void caller_handler(int sig) { unexpected_signal=sig; }
static int same_mask(const sigset_t *left,const sigset_t *right) {
    const int signals[]={SIGHUP,SIGINT,SIGQUIT,SIGILL,SIGABRT,SIGFPE,SIGKILL,
        SIGSEGV,SIGPIPE,SIGALRM,SIGTERM,SIGUSR1,SIGUSR2,SIGCHLD,SIGCONT,
        SIGSTOP,SIGTSTP,SIGTTIN,SIGTTOU};
    for(size_t i=0;i<sizeof(signals)/sizeof(signals[0]);++i)
        if(sigismember(left,signals[i])!=sigismember(right,signals[i]))return 0;
    return 1;
}
static int same_action(const struct sigaction *left,const struct sigaction *right) {
    return left->sa_handler==right->sa_handler && left->sa_flags==right->sa_flags
        && same_mask(&left->sa_mask,&right->sa_mask);
}
int main(int argc,char **argv) {
    if(argc!=2)return 1;
    int blocked=strcmp(argv[1],"blocked")==0;
    if(!blocked && strcmp(argv[1],"ignored"))return 1;
    struct sigaction action,term_before,term_after,usr_before,usr_after;
    memset(&action,0,sizeof(action));sigemptyset(&action.sa_mask);
    sigaddset(&action.sa_mask,SIGUSR2);action.sa_flags=SA_RESTART;
    action.sa_handler=caller_handler;if(sigaction(SIGUSR1,&action,NULL))return 1;
    action.sa_handler=blocked?caller_handler:SIG_IGN;
    if(sigaction(SIGTERM,&action,NULL))return 1;
    sigset_t before,after;sigemptyset(&before);sigaddset(&before,SIGUSR2);
    if(blocked){sigaddset(&before,SIGTERM);sigaddset(&before,SIGUSR1);}
    if(sigprocmask(SIG_SETMASK,&before,NULL) || sigprocmask(SIG_SETMASK,NULL,&before)
        || sigaction(SIGTERM,NULL,&term_before) || sigaction(SIGUSR1,NULL,&usr_before))return 1;
    FILE *input=tmpfile();if(!input)return 1;
    if(setvbuf(input,NULL,_IONBF,0) || fputs("ready\n",input)==EOF
        || fflush(input) || fseek(input,0,SEEK_SET))return 1;
    char output[16];double start=monotonic();
    char *result=tfgets_proc(output,sizeof(output),input);
    double elapsed=monotonic()-start;
    int output_ok=result==output && !strcmp(output,"ready\n");
    if(sigprocmask(SIG_SETMASK,NULL,&after) || sigaction(SIGTERM,NULL,&term_after)
        || sigaction(SIGUSR1,NULL,&usr_after))return 1;
    int mask_ok=same_mask(&before,&after);
    int actions_ok=same_action(&term_before,&term_after) && same_action(&usr_before,&usr_after);
    errno=0;pid_t child=waitpid(-1,NULL,WNOHANG);
    int reaped=child==-1 && errno==ECHILD;
    printf("{\"variant\":\"%s\",\"elapsed_seconds\":%.6f,\"output_ok\":%s,"
           "\"mask_preserved\":%s,\"actions_preserved\":%s,\"no_children\":%s,"
           "\"unexpected_signal\":%d}\n",argv[1],elapsed,output_ok?"true":"false",
           mask_ok?"true":"false",actions_ok?"true":"false",reaped?"true":"false",
           (int)unexpected_signal);
    if(fclose(input))return 1;
    if(!output_ok || !mask_ok || !actions_ok || !reaped || unexpected_signal)return 1;
    return elapsed<2.0?0:2;
}
'''
    def compile_harness(path, name):
        harness=run/(name+'.c');binary=run/name
        harness.write_text(harness_text.replace('SOURCE',str(path)))
        built=subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O1',
            '-pthread','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(harness),'-o',str(binary)],
            capture_output=True,timeout=30)
        if built.returncode:raise ValueError('tfgets cleanup harness compile failed: '+built.stderr.decode())
        return binary
    def cases(binary):
        jobs=[];results=[]
        try:
            for variant in ['ignored','blocked']:
                jobs.append(subprocess.Popen([str(binary),variant],stdout=subprocess.PIPE,stderr=subprocess.PIPE))
            for proc in jobs:
                output,errors=proc.communicate(timeout=8)
                case=json.loads(output);case['returncode']=proc.returncode;case['stderr']=errors.decode()
                results.append(case)
        finally:
            for proc in jobs:
                if proc.poll() is None:proc.kill();proc.wait()
                proc.stdout.close();proc.stderr.close()
        return results
    actual=cases(compile_harness(source,'tfgets_cleanup'))
    report={'status':'failed','ready_input_cases':actual,'sigterm_mutant_rejected':False}
    report_path=run/'tfgets_cleanup_report.json'
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if any(item['returncode'] or item['stderr'] for item in actual):
        raise ValueError('tfgets inherited SIGTERM cleanup regression; see '+str(report_path))
    old='if(kill(timer,SIGKILL)<0'
    text=source.read_text()
    if text.count(old)!=1:raise ValueError('tfgets cancellation mutation target missing')
    mutant=run/'tfgets_sigterm_mutant.c';mutant.write_text(text.replace(old,'if(kill(timer,SIGTERM)<0',1))
    mutations=cases(compile_harness(mutant,'tfgets_cleanup_mutation'))
    report['sigterm_mutant_cases']=mutations
    # Exit 2 means the correct line and signal state survived, but cancellation
    # waited for the five-second timer. Other failures do not prove this bug.
    rejected=all(item['returncode']==2 and not item['stderr'] and 4.5<=item['elapsed_seconds']<8
                 for item in mutations)
    report.update(status='passed' if rejected else 'failed',sigterm_mutant_rejected=rejected)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if not rejected:raise ValueError('tfgets SIGTERM cleanup mutation was not detected')
    return report


def check_part_three(base, run, compiler='clang'):
    run.mkdir(parents=True, exist_ok=True)
    def execute(args, *, input=None, expected=None, code=0, timeout=20):
        result = subprocess.run([str(x) for x in args], input=input, capture_output=True, timeout=timeout)
        if result.returncode != code or (expected is not None and result.stdout != expected):
            raise ValueError(f'Part III command failed: {args[0]} code={result.returncode}\n{result.stderr[:1500]!r}')
        return result
    def compile_c(path, name):
        binary = run / name
        execute([compiler,'-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O1',
                 '-pthread','-fsanitize=address,undefined','-fno-omit-frame-pointer',path,'-o',binary])
        return binary
    rio = module(base/'code/ch10_rio.py')
    cases = 0
    for length, request, first in itertools.product(range(10), range(13), range(1,5)):
        data = bytes((i*71) % 256 for i in range(length))
        reader = rio.Script(data, (-errno.EINTR,first,-errno.EINTR,2,1))
        if rio.readn(reader.read, request) != data[:request]:
            raise ValueError('Byte-prefix reference differs')
        writer = rio.Script(steps=(-errno.EINTR,first,-errno.EINTR,2,1))
        if rio.writen(writer.write,data) != length or writer.output != data:
            raise ValueError('Byte-write reference differs')
        cases += 1
    c_harness = r'''
#define main original_demo_main
#include "SOURCE"
#undef main
int main(void) {
    unsigned char data[10], got[20];
    for (size_t i=0;i<sizeof(data);++i)data[i]=(unsigned char)(i*71u);
    for(size_t len=0;len<10;++len)for(size_t want=0;want<13;++want)for(int first=1;first<=4;++first){
        int steps[]={-EINTR,first,-EINTR,2,1};
        Script input={data,len,0,steps,5,0,0,{0}};
        size_t expected=len<want?len:want;
        if(readn(scripted,&input,got,want)!=(ssize_t)expected || memcmp(got,data,expected))return 1;
        Script output={NULL,0,0,steps,5,0,0,{0}};
        if(writen(scripted_write,&output,data,len)!=(ssize_t)len || memcmp(output.output,data,len))return 2;
    }
    return 0;
}
'''
    harness = run/'rio_boundary.c'
    harness.write_text(c_harness.replace('SOURCE', str(base/'code/ch10_rio.c')))
    execute([compile_c(harness,'rio_boundary')])
    mutant = run/'rio_bad_eintr.c'
    src=(base/'code/ch10_rio.c').read_text()
    old='if (errno == EINTR) continue;'
    if old not in src: raise ValueError('EINTR mutation target missing')
    mutant.write_text(src.replace(old,'if (errno == EINTR) return -1;',1))
    harness.write_text(c_harness.replace('SOURCE',str(mutant)))
    execute([compile_c(harness,'rio_mutation')],code=1)
    harness.write_text(c_harness.replace('SOURCE',str(base/'code/ch10_rio.c')))
    copy_binary=compile_c(base/'code/ch10_cpfile.c','cpfile')
    rio_binary=compile_c(base/'code/ch10_rio.c','rio')
    copies=0
    sample=run/'binary-input.dat'
    for size in [0,1,7,8,9,8191,8192,8193,32771]:
        content=bytes((i*71)%256 for i in range(size));sample.write_bytes(content)
        for args in ([copy_binary],[rio_binary,'--copy'],[rio_binary,'--lines']):
            execute(args,input=content,expected=content)
            execute([*args,sample],expected=content)
            copies+=2
    # Closing stdin before exec forces open(infile) to reuse descriptor zero.
    proc=subprocess.run([str(copy_binary),str(sample)],stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                        preexec_fn=lambda:os.close(0),timeout=10)
    if proc.returncode or proc.stdout!=sample.read_bytes():raise ValueError('fd-zero copy regression')
    fstat=compile_c(base/'code/ch10_fstatcheck.c','fstatcheck')
    with sample.open('rb') as stream:
        proc=subprocess.run([str(fstat),str(stream.fileno())],pass_fds=(stream.fileno(),),
                            capture_output=True,timeout=10)
    if proc.returncode or proc.stdout!=b'type: regular, read: yes\n':raise ValueError('Inherited fstat descriptor differs')
    for text in ['','-1','+1','x','99999999999999999999999','1x']:
        execute([fstat,text],code=2)
    address = compile_c(base/'code/ch11_address.c','address')
    address_cases = [
        ('hex2dd','0x400',b'1024\n',0),('dd2hex','1024',b'0x400\n',0),
        ('hex2dd','ffff',b'65535\n',0),('dd2hex','0',b'0x0\n',0),
        ('hexipv4','7f000001',b'127.0.0.1\n',0),('ipv4hex','10.1.1.64',b'0x0A010140\n',0),
    ]
    address_cases += [('dd2hex',s,None,2) for s in ['','-1','65536','+1',' 1','\t1024','\n1024','1x']]
    address_cases += [('hex2dd',s,None,2) for s in ['0x','10000','0x10000','-1','gg']]
    address_cases += [('ipv4hex',s,None,2) for s in ['256.0.0.1','127.1','127.0.0.1junk']]
    for mode,value,output,rc in address_cases:
        for cmd in ([address],[sys.executable,base/'code/ch11_address.py']):
            execute([*cmd,mode,value],expected=output,code=rc)
    http_harness = run/'http_boundary.c'
    http_harness.write_text(r'''
#define main original_demo_main
#include "SOURCE"
#undef main
static int response_check(const char *request,int code,const char *payload,size_t length) {
    char *raw;size_t n;if(build_response(request,strlen(request),".",&raw,&n))return 1;
    char *text=malloc(n+1);if(!text){free(raw);return 1;}
    memcpy(text,raw,n);text[n]=0;free(raw);
    int status=0;char *body=strstr(text,"\r\n\r\n");
    int ok=sscanf(text,"HTTP/1.0 %d",&status)==1 && status==code && body;
    if(ok){body+=4;ok=n-(size_t)(body-text)==length && !memcmp(body,payload,length);}
    free(text);return !ok;
}
int main(void){
    const char *get="GET /cgi-bin/adder?2&3 HTTP/1.0\r\n\r\n";
    size_t expected=0;
    for(size_t i=0;i<strlen(get);++i)if(request_size(get,i,&expected)!=0)return 1;
    if(request_size(get,strlen(get),&expected)!=1 || expected!=strlen(get))return 2;
    if(response_check(get,200,"<p>2 + 3 = 5</p>\n",17))return 3;
    if(response_check("HEAD /cgi-bin/adder?2&3 HTTP/1.0\r\n\r\n",200,"",0))return 4;
    if(response_check("GET /../secret HTTP/1.0\r\n\r\n",403,"Forbidden",9))return 5;
    const char *duplicate="POST /cgi-bin/adder HTTP/1.0\r\nContent-Length: 0\r\nContent-Length: 0\r\n\r\n";
    if(request_size(duplicate,strlen(duplicate),&expected)!=-1)return 6;
    const char *post="POST /cgi-bin/adder HTTP/1.0\r\nContent-Length: 7\r\nContent-Type: application/x-www-form-urlencoded\r\n\r\na=2&b=3";
    for(size_t i=0;i<strlen(post);++i)if(request_size(post,i,&expected)!=0)return 7;
    if(response_check(post,200,"<p>2 + 3 = 5</p>\n",17))return 8;
    int fds[2];if(socketpair(AF_UNIX,SOCK_STREAM,0,fds))return 9;
    int size=1024;if(setsockopt(fds[0],SOL_SOCKET,SO_SNDBUF,&size,sizeof(size)))return 10;
    char *large=calloc(1024*1024,1);if(!large)return 11;
    int flags=fcntl(fds[0],F_GETFL);long long start=now_ms();
    int result=write_all(fds[0],large,1024*1024);long long elapsed=now_ms()-start;
    free(large);
    /* macOS exposes an extra F_GETFL bit after a socket buffer fills, even
     * after F_SETFL(old_flags); a plain socketpair reproduces this.
     * Compare public access/status bits affected by this socket operation. */
    int mask=O_ACCMODE|O_NONBLOCK|O_APPEND|O_ASYNC;
    if(result!=-1 || elapsed<1800 || elapsed>4000 || (fcntl(fds[0],F_GETFL)&mask)!=(flags&mask))return 12;
    close(fds[0]);close(fds[1]);return 0;
}
'''.replace('SOURCE',str(base/'code/ch11_http.c')))
    execute([compile_c(http_harness,'http_boundary')],timeout=8)
    # Enumerate all order-preserving schedules independently using combinations.
    outcomes={1:0,2:0}
    for positions in itertools.combinations(range(6),3):
        pcs=[0,0]; registers=[0,0]; value=0
        for i in range(6):
            tid=0 if i in positions else 1
            if pcs[tid]==0:registers[tid]=value
            elif pcs[tid]==1:registers[tid]+=1
            else:value=registers[tid]
            pcs[tid]+=1
        outcomes[value]+=1
    models=module(base/'code/ch12_models.py')
    if models.count_updates() != [0,outcomes[1],outcomes[2]] or outcomes != {1:18,2:2}:
        raise ValueError('Independent counter schedules differ')
    # Cartesian program counters + per-lock owner are independent of token bitsets.
    def terminal_states(programs):
        start=((0,)*len(programs),(-1,)*3); todo=[start]; seen={start}; dead=set();done=set()
        while todo:
            pc,owners=todo.pop(); successors=[]
            if all(pc[i]==len(p) for i,p in enumerate(programs)):
                done.add(pc);continue
            for i,p in enumerate(programs):
                if pc[i]==len(p):continue
                op=p[pc[i]];lock=ord(op.lower())-ord('a');new_owners=list(owners)
                if op.islower():
                    if owners[lock]!=-1:continue
                    new_owners[lock]=i
                else:
                    if owners[lock]!=i:raise ValueError('Invalid lock ownership in reference')
                    new_owners[lock]=-1
                new_pc=list(pc);new_pc[i]+=1;successors.append((tuple(new_pc),tuple(new_owners)))
            if not successors:dead.add(pc)
            for nxt in successors:
                if nxt not in seen:seen.add(nxt);todo.append(nxt)
        return dead,done,len(seen)
    locks=[]
    for programs in [('abAB','abAB'),('abAB','abBA'),('abBA','abAB'),('abBA','abBA'),
                     ('abBcCA','cbBC'),('abBcCA','cbBCaA','cCbaAB')]:
        dead,done,states=terminal_states(programs)
        actual_dead,actual_done=models.lock_states(programs,7)
        if dead!={x[0] for x in actual_dead} or done!={x[0] for x in actual_done}:
            raise ValueError('Owner-state deadlock reference differs')
        locks.append({'programs':programs,'reachable_states':states,'deadlock_pc':sorted(dead)})
    # Test real descriptors and a single absolute timeout, including a partial line.
    tfgets=compile_c(base/'code/ch12_tfgets.c','tfgets')
    for mode in ['proc','select','thread']:
        for sample,expected in [(b'abc\nrest',b'abc\n'),(b'last',b'last'),(b'',b'BOOM!\n')]:
            execute([tfgets,mode],input=sample,expected=expected)
    timed = []
    try:
        for mode in ['proc','select','thread']:
            started = time.monotonic()
            proc = subprocess.Popen([str(tfgets),mode],stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            timed.append((mode,proc,started))
            proc.stdin.write(b'partial'); proc.stdin.flush()
        for mode,proc,started in timed:
            proc.wait(timeout=8)
            elapsed = time.monotonic() - started
            output, errors = proc.stdout.read(), proc.stderr.read()
            if proc.returncode or output != b'BOOM!\n' or errors or not 4.5 <= elapsed <= 8:
                raise ValueError('Partial-line deadline failed: ' + mode)
    finally:
        for _,proc,_ in timed:
            if proc.poll() is None:
                proc.kill(); proc.wait()
            proc.stdin.close(); proc.stdout.close(); proc.stderr.close()
    mask_harness = run/'tfgets_mask.c'
    mask_harness.write_text(r'''
#define main original_demo_main
#include "SOURCE"
#undef main
int main(void) {
    sigset_t before,after; sigemptyset(&before);sigaddset(&before,SIGUSR1);
    if(sigprocmask(SIG_BLOCK,&before,NULL))return 1;
    if(sigprocmask(SIG_SETMASK,NULL,&before))return 1;
    FILE *input=tmpfile();if(!input)return 1;
    if(setvbuf(input,NULL,_IONBF,0))return 1;
    if(fputs("line\n",input)==EOF || fflush(input) || fseek(input,0,SEEK_SET))return 1;
    char output[16];if(!tfgets_proc(output,sizeof(output),input) || strcmp(output,"line\n"))return 2;
    if(sigprocmask(SIG_SETMASK,NULL,&after))return 1;
    if(sigismember(&before,SIGUSR1)!=sigismember(&after,SIGUSR1))return 3;
    fclose(input);return 0;
}
'''.replace('SOURCE',str(base/'code/ch12_tfgets.c')))
    execute([compile_c(mask_harness,'tfgets_mask')])
    tfgets_cleanup=check_tfgets_cleanup(base,run/'tfgets-cleanup',compiler)
    report={'status':'passed','rio_prefix_and_write_cases_per_language':cases,
            'binary_copy_cases':copies+1,'fstat_inherited_and_invalid_cases':7,
            'eintr_mutant_rejected':True,'address_cases_per_language':len(address_cases),
            'http_core':'GET/HEAD/POST, every partial prefix, duplicate length, path rejection, slow-reader deadline and descriptor flag restoration',
            'counter_schedules':20,'counter_outcomes':outcomes,'lock_references':locks,
            'tfgets_immediate_cases':9,'tfgets_partial_deadlines':3,'tfgets_signal_mask_restoration':True,
            'tfgets_cleanup':tfgets_cleanup,
            'boundaries':['Injected EINTR is loop behavior, not host signal-delivery proof.',
            'Finite sequential interleavings model instructions; they do not make C data races defined.']}
    (run/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
