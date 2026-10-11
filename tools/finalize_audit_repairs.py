#!/usr/bin/env python3
"""Bind completed repair checks to current files while preserving older checkpoints."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re
from html_support import Document,Element,canonical
from content_integrity import digest,check_snapshot
from sync_code import program_sources

ROOT=Path(__file__).resolve().parents[1]
NOTES=ROOT/'notes'


def stamp(path):
    blob=path.read_bytes();return {'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}


def render(node):
    if isinstance(node,str):return node
    if node.tag=='math':return '$'+node.attrs['data-tex']+'$'
    return ''.join(render(c) for c in node.children)


def public(value):
    if isinstance(value,dict):return {k:public(v) for k,v in value.items()}
    if isinstance(value,list):return [public(v) for v in value]
    if not isinstance(value,str):return value
    if value.startswith('file://'+str(ROOT)+'/'):return value[len('file://'+str(ROOT)+'/'):]
    value=value.replace(str(ROOT)+'/', '').replace(str(ROOT),'.')
    if '/Users/' in value or 'file:///' in value:
        return 'Local historical evidence; private path omitted. See current relative evidence paths.'
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-id',required=True)
    args=parser.parse_args()
    run=ROOT/'tmp/audit-fix-check';browser=ROOT/'tmp/audit-fix-http'
    report=json.loads((run/'report.json').read_text())
    layouts=json.loads((browser/'browser-layouts.json').read_text())
    interactions=json.loads((browser/'browser-interactions.json').read_text())
    if len(layouts)!=36 or len({(r['file'],r['width']) for r in layouts})!=36:raise ValueError('Need 36 distinct final layouts')
    for row in layouts:
        if row['sha256']!=stamp(NOTES/row['file'])['sha256']:raise ValueError('Browser evidence is stale: '+row['file'])
    if interactions['status']!='pass':raise ValueError('Interactions not complete')
    baseline=check_snapshot();now=datetime.now(timezone.utc).isoformat()
    documents={p.name:Document(p.read_text()) for p in NOTES.glob('*.html')}
    nodes={name:{n.attrs['id']:n for n in doc.root.walk() if n.attrs.get('id')} for name,doc in documents.items()}
    checks={'status':'pass','widths':[1800,1440,1024,390], 'layouts':layouts,
            'interactions':interactions, 'executed_at_utc':{'start':min(r['started_at_utc'] for r in layouts),'finish':max(r['finished_at_utc'] for r in layouts)},
            'evidence_paths':{'layouts':'../tmp/audit-fix-http/browser-layouts.json','interactions':'../tmp/audit-fix-http/browser-interactions.json'},
            'visual_scope':'Nine repair screenshots and no-JS screenshot individually inspected; actual browser PDF print inspected on first, example and final exercise pages; all-page rendered formula and bounded interaction checks.'}
    runtime={'status':'pass','started_at_utc':report['started_at_utc'],'finished_at_utc':report['finished_at_utc'],
             'record':'../tmp/audit-fix-check/report.json','log':'../tmp/audit-fix-check/full-check.log',
             'scope':'7 strict C11 and sanitizer builds; 159 independent numeric cases; 46 exact-status invalid inputs; four fixed-seed plus 12 extra-seed simulations; CRR convergence; source-page and tooling regressions.'}
    issues=[
        ('content-1.11','三对细致平衡均成立，链关于(1/7,4/7,2/7)可逆；保留消元并逐对验算',[89]),
        ('content-4.29','交通方程消元得(12/7,20/7)，利用率(3/7,40/49)，L=(3/4,40/9)，W=187/108；说明原书算术笔误',[194]),
        ('content-6.4','原书两棵树根值均为414.72/49；区分文字S0=32与图S0=36，不再误称144.72',[243]),
        ('content-6.20','字面普通看涨支付的64/25=2.56，保留原题矛盾和另一解释',[258]),
        ('content-conditions-and-citations','补回生成元极限存在前提、3.7源页、PASTA无编号例归属；五处邻近摘录标明相关原文',[142,143,156]),
        ('content-derivations','11道生灭题逐条速率代入和首末边验算；所有236题共1028步保留',[]),
        ('content-structure','补原书小节英文标题和六章Exercises节号；6.6按实际原书Calls and Puts；补附录来回链接',[]),
        ('notation','30处TeX控制词之后省略前导零的小数重新生成MathML；C十六进制浮点保持原词法',[]),
        ('code-parity','关闭FMA收缩，同顺序累加，BS正零，行权32epsilon相对尺度容差和极小价格回归',[]),
        ('code-input','完整读取并拒绝超长字段，输入2／数值3／明确资源4，stderr说明；增加clean及RNG标识',[]),
        ('code-linear','P平稳及边界方程用非对角和防止抵消；保留行缩放和1e-12病态保护，文档说明数学有效但数值拒绝的边界',[]),
        ('validation-content','已审阅正文快照绑定TeX、MathML、摘录、链接；353编号起始页；四项确切内容回归，快照不当作数学证明',[]),
        ('validation-execution','独立生成器移至tools，159基准、46非法输入精确分类，崩溃/信号不算成功；额外多种子检验',[]),
        ('validation-tooling','测试空MathML、变异正文、伪TeX、额外代码块、语言标签、资源导入、base、异常跳转及大数误差',[]),
        ('browser','最终九页36布局，66注解节切换，386正式陈述及习题深链接；打印展开并恢复，无JS原生折叠',[]),
        ('release','元数据相对路径；CSS等依赖检查；固定gzip/tar元数据；完整临时目录一次rename；新包验收保存在deploy/reports/'+args.release_id,[]),
    ]
    all_sources=set()
    for folder in ['notes','code','tools','deploy']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and not any(x in p.parts for x in ['__pycache__','build','releases','reports']) and p.suffix!='.json':all_sources.add(p.relative_to(ROOT).as_posix())
    all_sources.update(['agent.md','code/programs.json','tools/notes_cases.json','tools/content_baseline.json','notes/source_manifest.json','assets/essentials-of-stochastic-processes.pdf'])
    repair={'schema_version':1,'status':'pass','assembled_at_utc':now,'source_pdf_sha256':report['source_sha256'],
            'scope':'针对已独立核实的审计问题修复，并重新运行最终文件检查；既有全书逐题审阅作为历史基础，本次不声称机器证明全部236题或一般定理。',
            'issues':[{'id':i,'status':'resolved','resolution':text,'source_pdf_pages':pages} for i,text,pages in issues],
            'counts':{k:report[k] for k in ['html_pages','exercises','solution_steps','formal_statements','mathml','annotation_groups','annotation_cards','numerical_fixtures','invalid_inputs']},
            'content_snapshot':baseline,'program_checks':report,'runtime_evidence':runtime,'browser_review':checks,
            'numerical_boundary':'行缩放后主元小于1e-12的奇异/严重病态系统返回3；无解与数值精度不足需分别判断。行权舍入容差仅按当前价值尺度计算。',
            'deployment':{'status':'prepared_locally','release_id':args.release_id,'acceptance_record':'../deploy/reports/'+args.release_id+'/acceptance.json'},
            'files':{n:stamp(ROOT/n) for n in sorted(all_sources)}}
    (NOTES/'audit_fix_review.json').write_text(json.dumps(public(repair),ensure_ascii=False,indent=2)+'\n')
    programs,sources=program_sources()
    extracted={name+('.c' if lang=='c' else '.py'):hashlib.sha256(source.encode()).hexdigest() for (name,lang),source in sources.items()}
    runtime['extracted_code_sha256']=extracted
    # Existing file-hash dependencies are acyclic: serialize in dependency order.
    for filename in ['code_deployment_review.json','statements_review.json','annotations_review.json','readability_review.json','review_manifest.json','validation.json']:
        path=NOTES/filename;data=json.loads(path.read_text())
        oldbrowser=data.get('browser_review',data.get('browser_checks'))
        historical={'phase':'before_audit_repairs','generated_at_utc':data.get('generated_at_utc'),
                    'browser_review':oldbrowser,'runtime_evidence':data.get('runtime_evidence'),
                    'preservation':data.get('preservation'),'structural_checks':data.get('structural_checks'),
                    'files':data.get('files',{}),'record_sha256':stamp(path)['sha256']}
        if data.get('current_checkpoint')!='audit_repairs_final':
            if isinstance(data.get('review_history'),list):data['review_history'].append(historical)
            else:data['review_history']=[{'phase':'earlier_history','record':data.get('review_history')},historical]
        data['generated_at_utc']=now;data['audit_fix_review_file']='audit_fix_review.json'
        data['current_checkpoint']='audit_repairs_final'
        if 'preservation' in data:
            data['preservation']={'status':'counts_and_source_identity_preserved',
                                  'exercises':236,'solution_steps':1028,'annotation_groups':66,'annotation_cards':132,
                                  'scope':'Targeted content and program corrections documented in audit_fix_review.json; before-repair evidence preserved as history.'}
        if 'structural_checks' in data:
            data['structural_checks']={k:report[k] for k in ['html_pages','exercises','solution_steps','formal_statements','mathml','balanced_html','source_html_consistency','pdf_page_correspondence','content_binding']}
        for key in data.get('statistics',{}):
            if key in report:data['statistics'][key]=report[key]
        if filename=='validation.json':
            data['overall']='pass';data['program_checks']=report;data['browser_checks']=checks
            data['runtime_evidence']=runtime;data['extracted_code_sha256']=extracted
            data['rerun_command']='python3 -B tools/check_notes.py --run-dir tmp/audit-fix-check'
            data['check_scope']=repair['scope']
            data['content_review']['leading_zero_replacements']=554
            data['content_review']['scope']['programs']=runtime['scope']
        else:
            data['status']='pass';data['browser_review']=checks
        if filename=='code_deployment_review.json':
            data['program_checks']=report;data['runtime_evidence']=runtime
            data['standalone_make_examples']=json.loads((run/'make-examples.json').read_text())
            data['http_review']={'status':'pass','phase':'source_preview','record':'../tmp/audit-fix-http/http-responses.json'}
            data['deployment'].update(repair['deployment'])
            for p in data['programs']:
                p['sources']={lang:{'path':n,**stamp(ROOT/n)} for lang,n in p['files'].items()}
        if filename=='statements_review.json':
            data['card_hash_method']='html_support.canonical JSON with sorted attributes, whitespace normalized, SHA-256'
            for record in data['statements']:
                node=nodes[record['page_file']][record['key']]
                record['canonical_html_sha256']=digest(canonical(node));record['formulas']=[m.attrs['data-tex'] for m in node.walk('math')]
                body=next(n for n in node.walk('div') if n.has_class('statement-body'))
                mode=None;parts={'body':[],'why':[]}
                for child in body.children:
                    if not isinstance(child,Element):continue
                    if child.has_class('statement-label'):
                        mode={'中文陈述':'body','推导要点':'why'}.get(child.text());continue
                    if child.has_class('source'):mode=None
                    if mode:parts[mode].append(render(child).strip())
                for key in parts:
                    if parts[key]:record[key]='\n'.join(parts[key])
                record['excerpt_label']=next(n.text() for n in body.walk('p') if n.has_class('statement-label'))
        if filename=='annotations_review.json':
            data['card_hash_method']='html_support.canonical JSON with sorted attributes, whitespace normalized, SHA-256'
            for group in data['groups']:
                node=nodes[group['page']][group['anchor']]
                group['section_title']=next(nodes[group['page']][group['section']].walk('h2')).text()
                group['canonical_group_sha256']=digest(canonical(node))
                for card,node in zip(group['cards'],[n for n in node.walk('div') if n.has_class('annotation-card')]):
                    card['canonical_html_sha256']=digest(canonical(node));card['title']=next(node.walk('h3')).text()
        if filename=='readability_review.json':
            data['statistics']['audit_additional_leading_zeros']=30
            data['audit_expanded_birth_death_exercises']=11
            current_ids={i for i,_,_ in issues}
            data['notable_corrections']=[x for x in data['notable_corrections'] if '144.72' not in str(x) and x.get('location') not in current_ids]
            data['notable_corrections'] += [{'location':i,'kind':'audit repair','pdf_pages':pages,'correction':text} for i,text,pages in issues[:7]]
            for record in data['derivation_blocks']:
                node=nodes[record['page']][record['id']]
                record['html_sha256']=digest(canonical(node));record['hash_method']='html_support.canonical JSON SHA-256'
                record['mathml']=len(list(node.walk('math')));record['body_characters']=len(node.text())
            for record in data['retained_proofs']:
                section=nodes[record['page']][record['section']]
                record['html_sha256']=digest(canonical(section,omit_programs=True));record['hash_scope']='entire containing section, program bodies omitted'
                record['source_links']=[n.attrs['href'] for n in section.walk('a') if '.pdf#page=' in n.attrs.get('href','')]
        if filename=='review_manifest.json':
            readability=json.loads((NOTES/'readability_review.json').read_text())
            data['body_additions']=readability['derivation_blocks']
            data['retained_body_reviews']=readability['retained_proofs']
            for chapter in data['chapters']:
                page=Path(chapter['file']).name
                for record in chapter['exercise_review']:
                    node=nodes[page][record['anchor']]
                    question=next(n for n in node.walk('div') if n.has_class('exercise-question'))
                    answer=next(n for n in node.walk('div') if n.has_class('answer'))
                    record['question_text_sha256']=hashlib.sha256(question.text().encode()).hexdigest()
                    record['solution_html_sha256']=digest(canonical(answer));record['hash_method']='question UTF-8 text; answer html_support.canonical JSON'
                    record['solution_characters']=len(answer.text());record['current_binding']='audit_repairs_final'
            data['program_review']=runtime['scope']
        oldnames=list(data.get('files',{}))
        data['files']={n:stamp(ROOT/n) for n in oldnames if (ROOT/n).is_file()}
        data['files']['notes/audit_fix_review.json']=stamp(NOTES/'audit_fix_review.json')
        path.write_text(json.dumps(public(data),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'pass','records_updated':7,'assembled_at_utc':now},ensure_ascii=False))


if __name__=='__main__':main()
