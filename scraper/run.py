"""Pipeline completo.
  python scraper/run.py                 roda tudo (coleta, PDFs, leitura, dados, busca por tema, SEO)
  python scraper/run.py --from merge    recomeça a partir de uma etapa
Etapas: fetch, download, parse, merge, build, embed, seo. A edição vem da variável EDICAO (padrão 2026)."""
import sys,os,subprocess,json,time
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE);from paths import *
py=sys.executable
def run(*a):
    t=time.time();print('→',' '.join(a),flush=True);subprocess.run([py,os.path.join(HERE,a[0]),*a[1:]],check=True);print(f'  ({time.time()-t:.0f}s)',flush=True)
def parse2():
    d=json.load(open(os.path.join(CACHE,'parsed.json')));empty=[k for k,v in d.items() if not v]
    run('parse2.py',os.path.join(CACHE,'parsed2.json'),*empty)
STEPS=[('fetch',lambda:run('pubs.py',os.path.join(CACHE,'pubs.json'))),
       ('download',lambda:run('download.py')),
       ('parse',lambda:[run('parse.py',os.path.join(CACHE,'parsed.json')),parse2(),
                        run('parse3.py',os.path.join(CACHE,'parsed3.json')),run('parse4.py',os.path.join(CACHE,'parsed4.json')),
                        run('parse6.py',os.path.join(CACHE,'parsed6.json'))]),
       ('merge',lambda:run('merge.py')),
       ('build',lambda:[run('build.py'),run('augment.py')]),
       ('embed',lambda:run('embed.py','96')),
       ('seo',lambda:run('seo.py'))]
start=sys.argv[sys.argv.index('--from')+1] if '--from' in sys.argv else STEPS[0][0]
go=False
for name,fn in STEPS:
    go=go or name==start
    if go: print(f'== {name}',flush=True);fn()
