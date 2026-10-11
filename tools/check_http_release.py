#!/usr/bin/env python3
"""Verify an owned local static preview against source/release bytes and MIME types."""
from pathlib import Path
import argparse,hashlib,json
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import quote
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release-id')
    ap.add_argument('--output',type=Path,default=ROOT/'tmp/audit-fix-http/http-responses.json')
    args=ap.parse_args();session=json.loads((ROOT/'tmp/audit-fix-http/session.json').read_text())
    origin=session['origin'];start=datetime.now(timezone.utc).isoformat()
    if args.release_id:
        metadata=json.loads((ROOT/'deploy/releases'/args.release_id/'release.json').read_text())
        names=[r['path'] for r in metadata['files']]
        expected={r['path']:r['sha256'] for r in metadata['files']}
    else:
        manifest=json.loads((ROOT/'code/programs.json').read_text())
        names=['index.html']+[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'notes').glob('*.html'))]
        names += [n for p in manifest['programs'] for n in p['files'].values()]
        names += ['assets/essentials-of-stochastic-processes.pdf']
        expected={n:hashlib.sha256((ROOT/n if n!='index.html' else ROOT/'tmp/audit-fix-http/site/index.html').read_bytes()).hexdigest() for n in names}
    results=[]
    for prefix in ['', '/library/stochastic']:
        for name in names:
            with urlopen(origin+prefix+'/'+quote(name),timeout=15) as response:
                blob=response.read();mime=response.headers.get_content_type()
                sha=hashlib.sha256(blob).hexdigest()
                assert response.status==200 and sha==expected[name],(prefix,name)
                suffix=Path(name).suffix
                want={'.html':'text/html','.json':'application/json','.pdf':'application/pdf','.c':'text/plain','.py':'text/plain','.md':'text/plain'}.get(suffix,'application/octet-stream')
                assert mime==want,(name,mime,want)
                assert response.headers['X-Content-Type-Options']=='nosniff'
                assert response.headers['Cache-Control']=='no-cache'
                csp=response.headers['Content-Security-Policy'];assert "sha256-" in csp and "script-src 'self'" in csp
                results.append({'mount':prefix or '/', 'path':name,'status':response.status,'mime':mime,'bytes':len(blob),'sha256':sha})
        with urlopen(Request(origin+prefix+'/assets/essentials-of-stochastic-processes.pdf',headers={'Range':'bytes=32-63'}),timeout=15) as response:
            assert response.status==206 and response.read()==(ROOT/'assets/essentials-of-stochastic-processes.pdf').read_bytes()[32:64]
            assert response.headers['Content-Range']=='bytes 32-63/2579008'
        for path,method,want in [('/.git/config','GET',404),('/notes/absent.html','GET',404),('/notes/book_overview.html','POST',403)]:
            try:urlopen(Request(origin+prefix+path,method=method,data=b'' if method=='POST' else None),timeout=15)
            except HTTPError as exc:assert exc.code==want
            else:raise AssertionError('Expected HTTP rejection')
    result={'status':'pass','started_at_utc':start,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
            'origin':origin,'release_id':args.release_id,'checked_files_per_mount':len(names),'mounts':['/','/library/stochastic/'],
            'files':results,'pdf_range':'206 bytes32-63 match','method_and_missing_path_checks':'pass'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'pass','responses':len(results),'pdf_range':'pass'}))


if __name__=='__main__':main()
