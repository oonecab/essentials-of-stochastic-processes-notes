#!/usr/bin/env python3
"""Exact algebra and reading assertions for the four corrected content findings."""
from fractions import Fraction as F
from pathlib import Path
import json
import re
from html_support import Document
from generate_cases import solve, finance_reference

ROOT = Path(__file__).resolve().parents[1]


def block(page, identity):
    doc = Document((ROOT/'notes'/page).read_text())
    return next(n for n in doc.root.walk() if n.attrs.get('id') == identity)


def main():
    exercise = block('chapter01_markov_chains.html','ex-1-11')
    p = [[F(1,5),F(2,5),F(2,5)],[F(1,10),F(3,5),F(3,10)],[F(1,5),F(3,5),F(1,5)]]
    pi = solve([[p[j][i]-int(i==j) for j in range(3)] for i in range(2)]+[[F(1)]*3], [F(0),F(0),F(1)])
    assert pi == [F(1,7),F(4,7),F(2,7)]
    assert all(pi[i]*p[i][j] == pi[j]*p[j][i] for i in range(3) for j in range(3))
    assert '关于' in exercise.text() and '可逆' in exercise.text() and '不满足细致平衡' not in exercise.text()
    traffic = block('chapter04_continuous_time_markov_chains.html','derive-c4-jackson-balance')
    a1,a2 = solve([[F(1),-F(1,4)],[-F(1,2),F(1)]],[F(1),F(2)])
    rho1,rho2 = a1/4,a2/F(7,2)
    assert (a1,a2,rho1,rho2)==(F(12,7),F(20,7),F(3,7),F(40,49))
    W = (rho1/(1-rho1)+rho2/(1-rho2))/3
    tex = '\n'.join(n.attrs['data-tex'] for n in traffic.walk('math'))
    assert r'\alpha_1=1+5/7=12/7' in tex and r'187/108' in tex and W==F(187,108)
    parity = block('chapter06_mathematical_finance.html','derive-c6-parity-knockout')
    assert '144.72' not in parity.text() and '414.72/49' in parity.text()
    call = F(6,7)**2*F(9,25)*32
    put = F(6,7)**2*(2*F(6,25)*13+F(4,25)*33)
    assert call==put==F(10368,1225)
    ex20 = block('chapter06_mathematical_finance.html','ex-6-20')
    rows = finance_reference({'input':'3 4 2 0.5 0.25 4 0 1 0'})
    assert rows[0]['v']==float(F(64,25))
    tex = [n.attrs.get('data-tex','') for n in ex20.walk('math')]
    assert r'\frac{64}{25}=2.56' in tex and '2.208' not in ex20.text()
    print(json.dumps({'status':'pass','checks':['1.11 detailed balance','4.29 traffic/utilization/Little','6.4 source attribution/parity','6.20 literal payoff']},ensure_ascii=False))


if __name__=='__main__':main()
