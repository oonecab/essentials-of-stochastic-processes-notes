"""Bounded POSIX cleanup and HTML-extracted signal-mask regressions.

The shell tests create their own session, use only its known direct children,
and rescue a deliberately hung mutant before waiting for that shell to reap.
No test sends a signal to the caller's process group or creates grandchildren.
"""
from __future__ import annotations

import errno
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import subprocess
import time


GUARD = 1.0
FLAGS = ['-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic', '-O1',
         '-fsanitize=address,undefined', '-fno-omit-frame-pointer']


class _Snippet(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.count = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code' and dict(attrs).get('id') == 'sigsuspend-wait-template':
            self.active = True
            self.count += 1

    def handle_endtag(self, tag):
        if tag == 'code':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


def _exists(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _kill_owned(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _kill_session_child(pid, session_id):
    """Check the private test session as well as the helper's announced PID."""
    try:
        if os.getsid(pid) != session_id:
            raise ValueError('refusing to signal a PID outside the owned test session')
        _kill_owned(pid)
    except ProcessLookupError:
        pass


class _Session:
    """A pipe for commands/EOF and a PTY only for line-buffered output."""
    def __init__(self, binary):
        self.master, slave = pty.openpty()
        try:
            self.proc = subprocess.Popen([str(binary), '--interactive'], stdin=subprocess.PIPE,
                                         stdout=slave, stderr=slave, start_new_session=True)
        finally:
            os.close(slave)
        self.output = ''
        self.owned = set()
        self.finished = set()
        self.rescued = []

    def read(self, duration=0.01):
        if select.select([self.master], [], [], duration)[0]:
            try:
                chunk = os.read(self.master, 65536)
            except OSError as exc:
                if exc.errno != errno.EIO:
                    raise
                chunk = b''
            self.output += chunk.decode(errors='replace')
            # Every READY line is emitted by our helper, before it can move or stop.
            self.owned.update(map(int, re.findall(r'READY pid=(\d+)', self.output)))
            # Also capture a launch whose helper failed before READY.
            self.owned.update(map(int, re.findall(r'\[\d+\] (\d+) ', self.output)))

    def until(self, predicate):
        deadline = time.monotonic() + GUARD
        while not predicate():
            if time.monotonic() >= deadline:
                raise ValueError('readiness guard: ' + self.output)
            self.read(min(0.01, max(0, deadline - time.monotonic())))

    def send(self, command):
        self.proc.stdin.write((command + '\n').encode())
        self.proc.stdin.flush()

    def launch(self, helper, mode, argument=''):
        before = len(re.findall(r'READY pid=', self.output))
        self.send(f'{helper} {mode} {argument} &')
        self.until(lambda: len(re.findall(r'READY pid=', self.output)) > before)
        record = re.findall(r'READY pid=(\d+) parent=(\d+) group=(\d+)', self.output)[-1]
        pid, parent, group = map(int, record)
        if parent != self.proc.pid or group != pid:
            raise ValueError('helper was not a direct child in its initial private group')
        return pid

    def finish(self, kind):
        if kind == 'quit':
            self.send('quit')
        else:
            self.proc.stdin.close()
        try:
            self.proc.wait(timeout=GUARD)
            completed = True
        except subprocess.TimeoutExpired:
            completed = False
        self.read(0)
        return completed

    def close(self):
        # Helpers in hold/move/stop modes cannot exit voluntarily. Rescue while
        # their parent still owns each unreaped PID, then let it perform waitpid.
        self.read(0)
        if self.proc.poll() is None:
            for pid in sorted(self.owned - self.finished):
                if _exists(pid):
                    _kill_session_child(pid, self.proc.pid)
                    self.rescued.append(pid)
            if not self.proc.stdin.closed:
                try:
                    self.send('quit')
                except BrokenPipeError:
                    pass
                self.proc.stdin.close()
            try:
                self.proc.wait(timeout=GUARD)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=GUARD)
        if not self.proc.stdin.closed:
            self.proc.stdin.close()
        self.read(0)
        os.close(self.master)
        # A broken future implementation could return without cleaning at all.
        # Our helpers cannot fork or change session, so still-live announced
        # children can be identified and killed even after the shell exited.
        for pid in sorted(self.owned - self.finished):
            if _exists(pid):
                _kill_session_child(pid, self.proc.pid)
                self.rescued.append(pid)
        deadline = time.monotonic() + GUARD
        while any(_exists(pid) for pid in self.owned) and time.monotonic() < deadline:
            time.sleep(0.01)
        remaining = [pid for pid in self.owned if _exists(pid)]
        if remaining:
            raise ValueError('test child still present after cleanup: ' + repr(remaining))


_HELPER = r'''#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static volatile sig_atomic_t move_now;
static void request_move(int signal_number) { (void)signal_number; move_now = 1; }
static int move_to(pid_t group) {
    if (setpgid(0, group)) return 2;
    printf("MOVED pid=%ld group=%ld\n", (long)getpid(), (long)getpgrp());
    fflush(stdout); return 0;
}
int main(int argc, char **argv) {
    if (argc < 2) return 2;
    struct sigaction action = {0};
    action.sa_handler = request_move; sigemptyset(&action.sa_mask);
    if (sigaction(SIGUSR1, &action, NULL)) return 2;
    sigset_t blocked, old; sigemptyset(&blocked); sigaddset(&blocked, SIGUSR1);
    if (sigprocmask(SIG_BLOCK, &blocked, &old)) return 2;
    printf("READY pid=%ld parent=%ld group=%ld\n", (long)getpid(),
           (long)getppid(), (long)getpgrp()); fflush(stdout);
    if (!strcmp(argv[1], "exit")) return 0;
    if (!strcmp(argv[1], "stop")) raise(SIGSTOP);
    if (!strcmp(argv[1], "move") && move_to(getpgid(getppid()))) return 2;
    if (!strcmp(argv[1], "join")) {
        if (argc != 3 || move_to((pid_t)strtol(argv[2], NULL, 10))) return 2;
    }
    for (;;) {
        if (move_now) {
            move_now = 0;
            if (move_to(getpgid(getppid()))) return 2;
        }
        sigsuspend(&old);
    }
}
'''


def _shell_case(binary, helper, scenario, ending):
    session = _Session(binary)
    started = time.monotonic()
    try:
        first = session.launch(helper, 'hold' if scenario == 'group-remains' else scenario)
        group_present = None
        if scenario == 'stop':
            session.until(lambda: 'stopped by signal' in session.output)
        elif scenario == 'exit':
            session.until(lambda: not _exists(first))
            session.finished.add(first)
        elif scenario == 'move':
            session.until(lambda: f'MOVED pid={first} group={session.proc.pid}' in session.output)
            try:
                os.killpg(first, 0)
                group_present = True
            except ProcessLookupError:
                group_present = False
            if group_present:
                raise ValueError('moved-only child still has an old group')
        elif scenario == 'group-remains':
            second = session.launch(helper, 'join', str(first))
            session.until(lambda: f'MOVED pid={second} group={first}' in session.output)
            os.kill(first, signal.SIGUSR1)
            session.until(lambda: f'MOVED pid={first} group={session.proc.pid}' in session.output)
            if os.getpgid(second) != first or os.getpgid(first) != session.proc.pid:
                raise ValueError('group movement precondition failed')
            group_present = True
        completed = session.finish(ending)
        result = {'scenario': scenario, 'ending': ending, 'completed_before_guard': completed,
                  'exit_code_before_rescue': session.proc.returncode,
                  'old_group_exists_after_move': group_present}
    finally:
        session.close()
    result.update({'rescued_direct_children': len(session.rescued),
                   'all_created_children_gone': True, 'shell_reaped': session.proc.returncode is not None,
                   'elapsed_seconds': round(time.monotonic() - started, 4), 'output': session.output})
    return result


_RETAINED_LEADER = r'''
/* The member is also our direct child, but only the exited leader is in jobs.
 * Thus deleting the leader before group-kill loses the only group reference. */
static int await_byte(int fd) {
    char byte; ssize_t n;
    do { n=read(fd,&byte,1); } while(n<0 && errno==EINTR);
    return n==1 ? 0 : 1;
}
int main(void) {
    int ready[2], release[2];
    if(pipe(ready) || pipe(release)) return 2;
    sigset_t blocked; sigemptyset(&blocked); sigaddset(&blocked,SIGCHLD);
    if(sigprocmask(SIG_BLOCK,&blocked,&original)) return 2;
    quiet=1;
    pid_t leader=fork();
    if(leader<0) return 2;
    if(!leader) {
        if(setpgid(0,0) || write(ready[1],"L",1)!=1 || await_byte(release[0])) _exit(2);
        _exit(0);
    }
    if(await_byte(ready[0])) return 2;
    pid_t member=fork();
    if(member<0) { kill(leader,SIGKILL); waitpid(leader,NULL,0); return 2; }
    if(!member) {
        if(setpgid(0,leader) || write(ready[1],"M",1)!=1) _exit(2);
        for(;;) pause();
    }
    printf("OWNED %ld %ld\n",(long)leader,(long)member); fflush(stdout);
    if(await_byte(ready[0]) || write(release[1],"X",1)!=1) return 2;
    siginfo_t info;
    if(waitid(P_PID,(id_t)leader,&info,WEXITED|WNOWAIT)) return 2;
    jobs[0].pid=leader; jobs[0].state=BACKGROUND;
    int cleanup_result=cleanup(), status=0, member_killed=0;
    struct timespec delay={0,10000000};
    for(int i=0;i<30;i++) {
        pid_t result=waitpid(member,&status,WNOHANG);
        if(result==member) { member_killed=WIFSIGNALED(status) && WTERMSIG(status)==SIGKILL; break; }
        if(result<0 && errno!=EINTR) break;
        nanosleep(&delay,NULL);
    }
    if(!member_killed) { kill(member,SIGKILL); while(waitpid(member,NULL,0)<0 && errno==EINTR) {} }
    while(waitpid(leader,NULL,0)<0 && errno==EINTR) {}
    for(int i=0;i<2;i++) { close(ready[i]); close(release[i]); }
    printf("retained-leader cleanup=%d member-killed=%d\n",cleanup_result,member_killed);
    return cleanup_result || !member_killed;
}
'''


_KILL_ERROR = r'''
static pid_t reject_pid;
static int controlled_kill(pid_t target,int sig) {
    if(target==reject_pid || target==-reject_pid) { errno=EPERM; return -1; }
    return kill(target,sig);
}
#define kill controlled_kill
'''

_ERROR_BODY = r'''
int main(void) {
    sigset_t blocked; sigemptyset(&blocked); sigaddset(&blocked,SIGCHLD);
    if(sigprocmask(SIG_BLOCK,&blocked,&original)) return 2;
    pid_t child=fork();
    if(child<0) return 2;
    if(!child) { for(;;) pause(); }
    printf("OWNED %ld\n",(long)child); fflush(stdout);
    jobs[0].pid=child; jobs[0].state=BACKGROUND; reject_pid=child;
    int result=cleanup();
    int retained=jobs[0].state!=UNUSED, alive=kill(child,0)==0;
    kill(child,SIGKILL); while(waitpid(child,NULL,0)<0 && errno==EINTR) {}
    printf("signal-error result=%d retained=%d alive=%d\n",result,retained,alive);
    return !(result && retained && alive);
}
'''


_TEMPLATE_PREFIX = r'''#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <unistd.h>
static volatile sig_atomic_t done, handler_usr1, protected_after;
static int block_calls;
static void notification(int sig) {
    (void)sig; int saved=errno; sigset_t mask;
    if(sigprocmask(SIG_SETMASK,NULL,&mask)) _exit(20);
    handler_usr1=sigismember(&mask,SIGUSR1); done=1; errno=saved;
}
static void guard(int sig) { (void)sig; _exit(42); }
static int observed_mask(int how,const sigset_t *set,sigset_t *old) {
    int result=sigprocmask(how,set,old);
    if(result) _exit(21);
    if(how==SIG_BLOCK && set) {
        sigset_t pending; block_calls++;
        /* Inject the notification only after the actual template protects the
         * region, so both caller masks exercise pending-before-suspend. */
        if(raise(SIGCHLD) || sigpending(&pending) || sigismember(&pending,SIGCHLD)!=1) _exit(22);
    }
    return result;
}
static int observed_suspend(const sigset_t *mask) {
    int result=sigsuspend(mask), saved=errno; sigset_t after;
    if(sigprocmask(SIG_SETMASK,NULL,&after)) _exit(23);
    protected_after=sigismember(&after,SIGCHLD)==1 && sigismember(&after,SIGUSR1)==1;
    errno=saved; return result;
}
int main(int argc,char **argv) {
    if(argc!=2) return 2;
    int initially_blocked=atoi(argv[1]);
    struct sigaction action={0}; sigemptyset(&action.sa_mask);
    action.sa_handler=notification;
    if(sigaction(SIGCHLD,&action,NULL)) return 2;
    action.sa_handler=guard;
    if(sigaction(SIGALRM,&action,NULL)) return 2;
    sigset_t initial; sigemptyset(&initial); sigaddset(&initial,SIGUSR1);
    if(initially_blocked) sigaddset(&initial,SIGCHLD);
    if(sigprocmask(SIG_SETMASK,&initial,NULL)) return 2;
    struct itimerval timer={{0,0},{0,250000}};
    if(setitimer(ITIMER_REAL,&timer,NULL)) return 2;
#define sigprocmask observed_mask
#define sigsuspend observed_suspend
/* BEGIN VERBATIM HTML code#sigsuspend-wait-template */
'''

_TEMPLATE_SUFFIX = r'''
/* END VERBATIM HTML code#sigsuspend-wait-template */
#undef sigprocmask
#undef sigsuspend
    sigset_t final;
    if(sigprocmask(SIG_SETMASK,NULL,&final)) return 2;
    int restored=sigismember(&final,SIGCHLD)==initially_blocked &&
                 sigismember(&final,SIGUSR1)==1 && sigismember(&final,SIGUSR2)==0;
    printf("caller-CHLD=%d delivered=%d handler-USR1=%d protected=%d restored=%d\n",
           initially_blocked,(int)done,(int)handler_usr1,(int)protected_after,restored);
    return !(block_calls==1 && done && handler_usr1 && protected_after && restored);
}
'''


def check_signal_regressions(base: Path, run: Path, compiler: str):
    """Run strict/sanitized real-host POSIX cases and return a JSON-safe summary."""
    base, run = Path(base).resolve(), Path(run).resolve()
    run.mkdir(parents=True, exist_ok=True)
    commands, cases, mutants = [], [], []

    def command(args, expected=0, timeout=60):
        proc = subprocess.run(list(map(str,args)), capture_output=True, text=True, timeout=timeout)
        commands.append({'command': [str(x).replace(str(run),'RUN').replace(str(base),'BOOK') for x in args],
                         'exit_code':proc.returncode,'stdout':proc.stdout[:4000],'stderr':proc.stderr[:2000]})
        if expected is not None and proc.returncode != expected:
            raise ValueError('signal regression command failed: ' + repr(args) + '\n' + proc.stderr)
        return proc

    def compile_source(name, text):
        source=run/(name+'.c'); source.write_text(text)
        binary=run/name
        command([compiler,*FLAGS,source,'-o',binary])
        return binary

    def include_source(name, source, body, prefix=''):
        text=('#define _POSIX_C_SOURCE 200809L\n#include <errno.h>\n#include <signal.h>\n'
              '#include <time.h>\n'+prefix+'\n#define main original_example_main\n#include '+
              json.dumps(str(source))+'\n#undef main\n#undef kill\n'+body)
        return compile_source(name,text)

    def run_owned_harness(binary):
        proc=subprocess.Popen([str(binary)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                              start_new_session=True)
        first=''
        try:
            if not select.select([proc.stdout],[],[],GUARD)[0]:
                raise ValueError('owned harness readiness guard')
            first=proc.stdout.readline()
            if not re.fullmatch(r'OWNED(?: \d+)+\n',first):
                raise ValueError('owned harness did not identify its children: '+first)
            try:
                out,err=proc.communicate(timeout=GUARD)
            except subprocess.TimeoutExpired:
                # The harness still owns these PIDs; unblock it before reaping.
                for pid in map(int,first.split()[1:]):
                    _kill_owned(pid)
                out,err=proc.communicate(timeout=GUARD)
                raise ValueError('owned harness guard: '+first+out+err)
            if any(_exists(pid) for pid in map(int,first.split()[1:])):
                raise ValueError('owned harness left a child present')
            result={'exit_code':proc.returncode,'stdout':first+out,'stderr':err,
                    'all_created_children_reaped':True}
            commands.append({'command':[str(binary).replace(str(run),'RUN')],**result})
            return result
        finally:
            owned=list(map(int,first.split()[1:])) if re.fullmatch(r'OWNED(?: \d+)+\n',first) else []
            for pid in owned:
                if _exists(pid):
                    _kill_session_child(pid,proc.pid)
            if proc.poll() is None:
                try:
                    proc.wait(timeout=GUARD)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(timeout=GUARD)
            deadline=time.monotonic()+GUARD
            while any(_exists(pid) for pid in owned) and time.monotonic()<deadline:
                time.sleep(0.01)
            proc.stdout.close(); proc.stderr.close()
            if any(_exists(pid) for pid in owned):
                raise ValueError('owned harness cleanup did not remove all children')

    try:
        source=base/'code/ch08_shell.c'; maintained=source.read_text()
        shell=compile_source('shell',maintained)
        helper=compile_source('helper',_HELPER)
        if any(c.isspace() for c in str(helper)):
            raise ValueError('this teaching shell cannot parse whitespace in executable paths')
        command([shell],timeout=GUARD)
        for scenario in ('hold','stop','exit','move','group-remains'):
            for ending in ('quit','EOF'):
                case=_shell_case(shell,helper,scenario,ending); cases.append(case)
                if (not case['completed_before_guard'] or case['exit_code_before_rescue']!=0
                        or case['rescued_direct_children']):
                    raise ValueError('shell cleanup did not finish: '+repr(case))

        # Recreate the precise historical cleanup for a durable red control.
        old_cleanup='''static int cleanup(void) {
    reap();
    for (int i=0;i<JOBS;i++) if(jobs[i].state) kill(-jobs[i].pid,SIGKILL);
    for (int i=0;i<JOBS;i++) if(jobs[i].state) {
        while(waitpid(jobs[i].pid,NULL,0)<0 && errno==EINTR) {}
        jobs[i].state=UNUSED;
    }
    sigprocmask(SIG_SETMASK,&original,NULL); return 0;
}
'''
        historical,n=re.subn(r'static int cleanup\(void\) \{.*?\n\}',old_cleanup,maintained,
                             count=1,flags=re.S)
        if n!=1: raise ValueError('cleanup mutation target missing')
        old_binary=compile_source('shell-old-group-only',historical)
        for scenario in ('move','group-remains'):
            case=_shell_case(old_binary,helper,scenario,'quit')
            case['mutation']='historical-group-only'
            mutants.append(case)
            if case['completed_before_guard'] or not case['rescued_direct_children']:
                raise ValueError('historical cleanup unexpectedly escaped the regression')

        needle='if (kill(jobs[i].pid, SIGKILL) == 0 || errno == ESRCH)'
        group_needle='if (kill(-jobs[i].pid, SIGKILL) < 0 && errno != ESRCH)'
        if needle not in maintained or group_needle not in maintained:
            raise ValueError('fallback mutation target missing')
        fallback=maintained.replace(group_needle,
            'int group_sent = kill(-jobs[i].pid, SIGKILL);\n'
            '        if (group_sent < 0 && errno != ESRCH)',1).replace(needle,
            'if (group_sent == 0 || kill(jobs[i].pid, SIGKILL) == 0 || errno == ESRCH)',1)
        case=_shell_case(compile_source('shell-wrong-fallback',fallback),helper,'group-remains','EOF')
        case['mutation']='wrong-PID-fallback-only-when-group-missing'; mutants.append(case)
        if case['completed_before_guard'] or not case['rescued_direct_children']:
            raise ValueError('fallback-only mutation escaped the regression')

        bypass,n=re.subn(r'static int cleanup\(void\) \{.*?\n\}',
            'static int cleanup(void) {\n    sigprocmask(SIG_SETMASK,&original,NULL); return 0;\n}',
            maintained,count=1,flags=re.S)
        if n!=1: raise ValueError('bypass cleanup mutation target missing')
        case=_shell_case(compile_source('shell-bypasses-cleanup',bypass),helper,'hold','quit')
        case['mutation']='shell-returns-without-cleanup'; mutants.append(case)
        if not case['completed_before_guard'] or not case['rescued_direct_children']:
            raise ValueError('bypassed cleanup did not exercise post-shell rescue')

        retained=run_owned_harness(include_source('retained-leader',source,_RETAINED_LEADER))
        if retained['exit_code']!=0: raise ValueError('retained exited leader lost its group')
        premature=run/'shell-premature-reap.c'
        premature.write_text(maintained.replace('static int cleanup(void) {',
                                               'static int cleanup(void) {\n    reap();',1))
        retained_mutant=run_owned_harness(include_source('retained-leader-mutant',premature,_RETAINED_LEADER))
        if retained_mutant['exit_code']==0: raise ValueError('premature-reap mutation escaped')
        mutants.append({'mutation':'reap-before-signalling-retained-group',**retained_mutant})
        error_case=run_owned_harness(include_source('signal-error',source,_ERROR_BODY,_KILL_ERROR))
        if error_case['exit_code']!=0: raise ValueError('signal failure lost state or blocked')

        html=base/'notes/chapter08_exceptional.html'
        parser=_Snippet(); parser.feed(html.read_text())
        snippet=''.join(parser.parts)
        if parser.count!=1 or not snippet.strip(): raise ValueError('expected one named HTML wait template')
        (run/'sigsuspend-template-extracted.c').write_text(snippet)
        template=compile_source('sigsuspend-template',_TEMPLATE_PREFIX+snippet+_TEMPLATE_SUFFIX)
        template_cases=[]
        for initial in (0,1):
            result=command([template,str(initial)],timeout=GUARD)
            template_cases.append({'initial_CHLD_blocked':bool(initial),'exit_code':result.returncode,
                                   'stdout':result.stdout})
        missing=snippet.replace('sigdelset(&waiting, SIGCHLD);','/* mutation: target remains blocked */',1)
        if missing==snippet: raise ValueError('HTML target-unblock mutation missing')
        missing_binary=compile_source('sigsuspend-missing-unblock',_TEMPLATE_PREFIX+missing+_TEMPLATE_SUFFIX)
        result=command([missing_binary,'1'],expected=42,timeout=GUARD)
        mutants.append({'mutation':'HTML-waiting-mask-does-not-unblock-CHLD','exit_code':result.returncode})
        empty=snippet.replace('sigprocmask(SIG_SETMASK, &old, NULL);',
                              'sigemptyset(&old); sigprocmask(SIG_SETMASK, &old, NULL);',1)
        if empty==snippet: raise ValueError('HTML restore-mask mutation missing')
        empty_binary=compile_source('sigsuspend-wrong-restore',_TEMPLATE_PREFIX+empty+_TEMPLATE_SUFFIX)
        for initial in (0,1):
            result=command([empty_binary,str(initial)],expected=1,timeout=GUARD)
            mutants.append({'mutation':'HTML-restore-clears-caller-mask','initial_CHLD_blocked':bool(initial),
                            'exit_code':result.returncode,'stdout':result.stdout})

        report={'status':'passed','host':os.uname().sysname,'strict_c11_asan_ubsan':True,
                'shell_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'html_template_sha256':hashlib.sha256(snippet.encode()).hexdigest(),
                'guard_seconds':GUARD,'template_watchdog_seconds':0.25,
                'cleanup_cases':cases,'retained_exited_leader':retained,
                'signal_error_path':error_case,'template_cases':template_cases,'detected_mutations':mutants,
                'commands':commands,
                'boundaries':['Real host POSIX behavior, not Linux-only execution.',
                    'Cleanup covers still-registered groups and unreaped direct child identities.',
                    'No claim about historical descendants whose leader was already removed by the main loop.',
                    'Signal errors are injected at kill for the owned child; actual credential changes are not tested.',
                    'HTML is compiled verbatim with observational wrappers; pending CHLD is injected after its actual SIG_BLOCK call.']}
        (run/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return {'status':'passed','cleanup_exit_cases':len(cases),'retained_exited_leader':'passed',
                'signal_error_path':'passed','html_template_cases':len(template_cases),
                'detected_mutations':len(mutants),'guard_seconds':GUARD,
                'shell_source_sha256':report['shell_source_sha256'],
                'html_template_sha256':report['html_template_sha256']}
    except Exception as exc:
        (run/'failure.json').write_text(json.dumps({'error':str(exc),'cleanup_cases':cases,
                                                  'mutants':mutants,'commands':commands},
                                                 ensure_ascii=False,indent=2)+'\n')
        raise
