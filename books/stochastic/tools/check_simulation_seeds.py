#!/usr/bin/env python3
"""Replay four teaching simulations at three extra seeds using isolated copies."""
from pathlib import Path
import json
import math
import re
import shutil
import subprocess
import sys
from sync_code import program_sources


def main():
    directory = Path(sys.argv[1]).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    programs, sources = program_sources()
    checked = []
    for name in ['poisson', 'renewal', 'ctmc', 'stopping']:
        for seed in [1, 42, 4294967295]:
            py = re.sub(r'(?m)^state=20261010$', 'state='+str(seed), sources[name, 'python'])
            c, count = re.subn(r'(static uint32_t state=UINT32_C\()20261010(\);)', r'\g<1>'+str(seed)+r'\g<2>', sources[name, 'c'])
            if count != 1 or py == sources[name, 'python']:
                raise ValueError('Expected exactly one seed declaration: '+name)
            a, b = directory/(name+str(seed)+'.py'), directory/(name+str(seed)+'.c')
            a.write_text(py); b.write_text(c)
            executable = b.with_suffix('')
            subprocess.run([shutil.which('clang'), '-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2','-ffp-contract=off',b,'-lm','-o',executable],check=True,capture_output=True)
            run = lambda args: subprocess.run(args,check=True,capture_output=True,text=True,timeout=30).stdout
            x, y = run([sys.executable,a]), run([executable])
            if x != y: raise AssertionError('Seeded C/Python replay differs: '+name)
            rows = [list(map(float,line.split())) for line in x.splitlines()]
            if name == 'poisson':
                assert abs(sum(row[2] for row in rows)-1)<1e-10
                assert all(abs(p-f)<=7*math.sqrt(p*(1-p)/100000)+0.00005 for _,p,f in rows)
            elif name == 'renewal':
                frequency = rows[0][1]
                assert abs(frequency-0.5)<=7*math.sqrt(0.25/100000)
                assert abs(rows[0][2]-frequency/(frequency+9*(1-frequency)))<1e-10
            elif name == 'ctmc':
                assert rows[0][1] == rows[1][1] == 0.5
                for row,mean in zip(rows,[0.5,1.0]):
                    assert abs(row[3]-mean)<=7*mean/math.sqrt(50000)
                assert abs(rows[0][2]-1/3)<0.015
            else:
                mean,p = rows[0]
                # For simple symmetric exit from [-5,5], E T=25,
                # Var T=(2/3)*5^2*(5^2-1)=400; upper-exit probability 1/2.
                assert abs(mean-25)<=7*math.sqrt(400/100000)
                assert abs(p-0.5)<=7*math.sqrt(0.25/100000)
            checked.append({'program':name,'seed':seed,'status':'pass'})
    print(json.dumps({'status':'pass','extra_simulation_runs':len(checked),'checks':checked,
                      'scope':'Isolated seed substitutions; original displayed fixed-seed sources remain unchanged. Finite statistical checks do not prove distributional correctness.'}))


if __name__=='__main__':main()
