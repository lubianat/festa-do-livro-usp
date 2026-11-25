"""Para cada editora, escolhe o resultado do leitor que extraiu mais livros completos (título, preço, ISBN, autor)."""
import json,re,subprocess,glob,os
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
R=[json.load(open(CACHE+f'/{f}')) for f in ['parsed.json','parsed2.json','parsed3.json','parsed4.json','parsed6.json']]
ISB=re.compile(r'97[89][\d\-]{10,14}')
def f(x):
    try: return float(str(x).replace(',','.')) if not isinstance(x,(int,float)) else float(x)
    except: return None
def clean(r):
    o={k:(re.sub(r'\s+',' ',str(r.get(k,''))).strip()) for k in ['isbn','title','author','subject','url','pub']}
    o['isbn']=re.sub(r'[^\dX]','',(ISB.search(o['isbn'].replace(' ','')) or re.search(r'.*',o['isbn'])).group())[:13]
    from parse import money
    c=r.get('cover');d=r.get('disc')
    c=f(c) if isinstance(c,(int,float)) or re.fullmatch(r'[\d.]+',str(c or '')) else money(str(c or ''))
    d=f(d) if isinstance(d,(int,float)) or re.fullmatch(r'[\d.]+',str(d or '')) else money(str(d or ''))
    ps=[x for x in (c,d) if x]
    pass
    if c and d: o['price']=min(c,d);o['orig']=max(c,d) if abs(c-d)>0.01 else None
    elif d: o['price']=d;o['orig']=None
    elif c: o['price']=None;o['orig']=c
    else: o['price']=None;o['orig']=None
    if not o['url'].startswith('http'): o['url']=''
    return o if len(o['title'])>1 else None
def score(rows,exp):
    if not rows: return -1
    rows=dedup(rows)
    if exp and len(rows)>exp*1.15: return -0.5
    return sum((1 if (r['price'] or r['orig']) else 0.3)+(0.3 if len(r['isbn'])>=10 else 0)+(0.3 if r['author'] else 0)+(0.2 if r['orig'] else 0)+(0.2 if r['subject'] else 0)-(1 if re.search(r'\d,\d{2}|^\W*$',r['title']) else 0)-(1 if re.search(r'[a-zà-ú][A-ZÀ-Ú][a-zà-ú]+[A-ZÀ-Ú]',r['title']+' '+r['author']) else 0) for r in rows)
def dedup(rows):
    best={}
    for r in rows:
        k=r['isbn'] or r['title'].lower()
        q=(r['price'] is not None)*2+(r['orig'] is not None)+bool(r['author'])*.5+bool(r['subject'])*.3
        if k not in best or q>best[k][0]: best[k]=(q,r)
    return [v for _,v in best.values()]
out={};rep=[]
for p in sorted(glob.glob(CACHE+'/pdf/*.pdf')):
    k=os.path.basename(p)[:-4]
    t=subprocess.run(['pdftotext','-layout',p,'-'],capture_output=True,text=True).stdout
    exp=len(set(re.findall(r'97[89]\d{10}',t.replace('-',''))))
    cands=[[c for c in map(clean,Ri.get(k,[])) if c] for Ri in R]
    best=max(range(5),key=lambda i:score(cands[i],exp)*(1.08 if i==4 else 1))
    out[k]=dedup(cands[best]);rep.append((k,exp,best,[len(c) for c in cands],best,round(score(cands[best],exp),2)))
json.dump(out,open(CACHE+'/merged.json','w'),ensure_ascii=False)
print('total',sum(map(len,out.values())))
for r in rep:
    if r[4]<0.6*max(r[1],1): print(r)
