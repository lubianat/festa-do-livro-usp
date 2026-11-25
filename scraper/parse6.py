"""Leitor 6 (o principal): lê os caracteres na ordem em que o PDF os desenha, o que separa colunas sobrepostas."""
import pdfplumber,re,json,sys
from parse5 import norm,label,ISBN,MONEY,INT
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
def runs(chars):
    R=[];cur=None
    for c in chars:
        t=c['text']
        if not c.get('upright',True): continue
        sz=c.get('size',8) or 8
        if cur and abs(c['top']-cur['top'])<sz*0.5 and -1.0<c['x0']-cur['x1']<sz*0.55:
            if t==' ': cur['sp']=True;continue
            g=c['x0']-cur['x1']
            if cur['sp'] or g>sz*0.2:
                cur['gaps'].append((len(cur['t']),cur['x1'],g,sz));cur['t']+=' '
            cur['t']+=t;cur['x1']=max(cur['x1'],c['x1']);cur['sp']=False
        else:
            if t==' ': 
                if cur: cur['sp']=True
                continue
            cur={'t':t,'x0':c['x0'],'x1':c['x1'],'top':c['top'],'bot':c['bottom'],'sp':False,'gaps':[]};R.append(cur)
    return [r for r in R if r['t'].strip()]
def lines(R,tol=2.5):
    L=[]
    for r in sorted(R,key=lambda r:(r['top'],r['x0'])):
        if L and abs(L[-1]['top']-r['top'])<tol: L[-1]['r'].append(r)
        else: L.append({'top':r['top'],'r':[r]})
    for l in L: l['r'].sort(key=lambda r:r['x0']);l['txt']=' '.join(r['t'] for r in l['r'])
    return L
def header_cols(H):
    # cluster header runs by x overlap
    rs=sorted([r for l in H for r in l['r']],key=lambda r:r['x0']);C=[]
    for r in rs:
        for c in C:
            if r['x0']<c['x1']+1 and r['x1']>c['x0']-1:
                c['x0']=min(c['x0'],r['x0']);c['x1']=max(c['x1'],r['x1']);c['ws'].append(r);break
        else: C.append({'x0':r['x0'],'x1':r['x1'],'ws':[r]})
    C.sort(key=lambda c:c['x0'])
    for c in C:
        c['t']=' '.join(r['t'] for r in sorted(c['ws'],key=lambda r:(r['top'],r['x0'])));c['k']=label(c['t']);c['cx']=(c['x0']+c['x1'])/2
    return C
def split(rs,C):
    out=[]
    for r in rs:
        cuts=[]
        for c in C[1:]:
            if r['x0']+4<c['x0']<r['x1']-4:
                cand=[g for g in r['gaps'] if c['x0']-30<=g[1]<=c['x0']+6 and g[2]>=g[3]*0.3]
                if cand: cuts.append(max(cand,key=lambda g:g[2]))
        if not cuts: out.append(r);continue
        cuts=sorted(set(cuts));prev=0;px=r['x0']
        for idx,x,g,sz in cuts:
            out.append({**r,'t':r['t'][prev:idx].strip(),'x0':px,'x1':x});prev=idx+1;px=x+g
        out.append({**r,'t':r['t'][prev:].strip(),'x0':px})
    return [o for o in out if o['t']]
def align(rs,C):
    # monotone assignment of runs to header cols minimizing distance
    n,m=len(rs),len(C);INF=1e18
    def cost(r,c):
        cx=c['cx'];a,b=r['x0'],r['x1']
        if a<=cx<=b: return 0
        return min(abs(a-cx),abs(b-cx))*(1 if r['x1']-r['x0']<200 else 0.3) + (0 if c['x0']-5<=a<=c['x1']+5 else 5)
    D=[[INF]*m for _ in range(n)];B=[[0]*m for _ in range(n)]
    for j in range(m): D[0][j]=cost(rs[0],C[j])
    for i in range(1,n):
        best=INF;bj=0
        for j in range(m):
            if D[i-1][j]<best: best=D[i-1][j];bj=j
            D[i][j]=best+cost(rs[i],C[j]);B[i][j]=bj
    j=min(range(m),key=lambda j:D[n-1][j]);out=[0]*n
    for i in range(n-1,-1,-1): out[i]=j;j=B[i][j]
    return out
TITLEW=('TITUL','TITLE','PRODUTO','DESCRI','OBRA')
def parse(f):
    out=[];C=None
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            L=lines(runs(page.chars))
            hi=None
            for i,l in enumerate(L[:30]):
                n=norm(l['txt'])
                if any(k in n for k in TITLEW) and not ISBN.search(l['txt'].replace(' ','')[:40]) and len(l['r'])>=2: hi=i;break
            start=0
            if hi is not None:
                H=[l for l in L if abs(l['top']-L[hi]['top'])<20 and not ISBN.search(l['txt'][:40]) and not re.search(r'\d,\d\d',l['txt'])]
                C=header_cols(H);start=L.index(H[-1])+1
            if not C: continue
            B=L[start:]
            def isanchor(l):
                if re.match(r'^\s*\d{1,5}-\d{1,7}-\d{1,7}-[\dX]\b',l['r'][0]['t']): return True
                return bool(ISBN.search(l['r'][0]['t'].replace(' ','').replace('-','')[:20])) or (len(l['r'])>1 and bool(ISBN.fullmatch(l['r'][1]['t'].replace('-','')) or ISBN.match(l['r'][1]['t'].replace('-',''))) and len(l['r'][0]['t'])<9)
            A=[l for l in B if isanchor(l)]
            if not A: continue
            ys=[a['top'] for a in A];recs=[{} for _ in A]
            # bands: midpoint between anchors; allow wrap above
            for l in B:
                k=min(range(len(ys)),key=lambda k:abs(ys[k]-l['top']))
                if abs(ys[k]-l['top'])>30: continue
                rr=l['r'];asg=align(rr,C)
                for r,j in zip(rr,asg):
                    recs[k].setdefault(j,[]).append((l['top'],r['x0'],r['t']))
            for rec in recs:
                d={}
                for j,v in sorted(rec.items()):
                    d.setdefault(C[j]['k'] or ('?'+C[j]['t']),[]).extend(t for _,_,t in sorted(v))
                out.append(d)
    return out
def num(t,allow_int):
    m=MONEY.match(t)
    if m: v=m.group(1);return float(v.replace('.','').replace(',','.')) if ',' in v else float(v)
    if allow_int:
        m=INT.match(t)
        if m: return float(m.group(1))
MTOK=re.compile(r'(?:-?R\$\s*)?-?(\d{1,3}(?:\.\d{3})*,\d{1,2}|\d{1,4}\.\d{2})-?(?=\s|$)')
ISB13=re.compile(r'(97[89]\d{10})')
def getisbn(t):
    d=re.sub(r'[\s\-]','',t);m=ISB13.match(d) or ISB13.search(d[:20])
    if m: return m.group(1)
    m=re.match(r'(97[89]\d{7})',d)
    if m: return m.group(1)
    m=re.match(r'^\s*(\d{1,5}-\d{1,7}-\d{1,7}-[\dX])\b',t)
    return m.group(1).replace('-','') if m else ''
def strip_isbn(t):
    return re.sub(r'^\s*97[89][\d\-]{10,16}?(?=\D|\d{1,4}\s|$)','',t).strip() if getisbn(t) else t
def interpret(raw):
    res=[]
    for r in raw:
        o={'isbn':'','title':'','author':'','subject':'','url':'','cover':None,'disc':None,'_m':[]}
        texts=[]
        for k,parts in r.items():
            parts=[p for p in parts if p.strip() not in('R$','-R$','-','R$-','$')]
            hp=[p for p in parts if p.startswith('http') or (o['url'] and k=='url' and not ' ' in p and not re.search(r'\d,\d',p))]
            if hp:
                o['url']=''.join(hp).replace(' ','');parts=[p for p in parts if p not in hp]
            parts=[p for p in parts if not re.fullmatch(r'USP\d*|Link|link',p.strip())]
            txt=re.sub(r'(^|\s)-?R\$\s*',r'\1',' '.join(parts)).strip()
            if not txt: continue
            if k=='url': k=None
            if not o['isbn'] and getisbn(txt) and (k=='isbn' or k in('title',None) or k.startswith('?')):
                o['isbn']=getisbn(txt)
                d=re.sub(r'^\s+','',txt);i=0;n=0
                while i<len(d) and n<len(o['isbn']):
                    if d[i].isdigit(): n+=1
                    i+=1
                rest=d[i:].strip(' -')
                if (len(rest)>2 and re.search('[A-Za-zÀ-ú]{2}',rest)) or re.fullmatch(r'\d{1,4}',rest):
                    rest=re.sub(r'^(Editora|Edições|Ed\.)\s+\S+\s+','',rest)
                    texts.append(('_rest',rest))
                continue
            vals=[num(t,k in('cover','disc')) for t in re.split(r'\s+(?=\S*\d)',txt)] if re.search(r'\d',txt) else [None]
            if vals and all(v is not None for v in vals) and k not in('title','author','subject'):
                if k=='qty': continue
                for v in vals: o['_m'].append((k,v))
                continue
            if k=='qty': continue
            if k not in('title',):
                for mm in MTOK.finditer(txt): v=mm.group(1);o['_m'].append(('x',float(v.replace('.','').replace(',','.')) if ',' in v else float(v)))
                txt=MTOK.sub(' ',txt).strip(' -')
            if re.fullmatch(r'[-R$\s\d.,]*',txt) and not (k=='title' and re.fullmatch(r'\d{1,4}',txt.strip())): continue
            texts.append((k,txt))
        for k,t in texts:
            if k in('title','author','subject'): o[k]=(o[k]+' '+t).strip()
        for k,t in texts:
            if k=='_rest':
                if not o['title']: o['title']=t
                elif not o['author']: o['author']=t
        for k,t in texts:
            if k not in('title','author','subject','pub','_rest'):
                for kk in('title','author','subject'):
                    if not o[kk]: o[kk]=t;break
        if len(o['_m'])<=1:
            ints=[]
            for k,t in list(texts):
                if k in('title',) : continue
                m=re.match(r'^(\d{1,4})(?:\s+(\d{1,4}))?(?:\s+(.*))?$',t)
                if m and 5<=int(m.group(1))<=2000:
                    ints.append(float(m.group(1)))
                    if m.group(2) and 3<=int(m.group(2))<=2000: ints.append(float(m.group(2)))
                    rest=(m.group(3) or '').strip()
                    if k in('subject','author') and o[k].startswith(t): o[k]=rest
                    elif k in('subject','author') and t in o[k]: o[k]=o[k].replace(t,rest).strip()
            if o['_m'] and len(ints)==1 and ints[0]<o['_m'][0][1]: o['_m'].append(('x',ints[0]))
            elif not o['_m'] and 1<=len(ints)<=2: o['_m']=[('x',v) for v in ints]
        ms=o.pop('_m');ms=[(k,v) for k,v in ms if 0<v<5000]
        disc=[v for k,v in ms if k=='disc'];cov=[v for k,v in ms if k!='disc']
        if disc and cov: o['disc']=min(disc);o['cover']=max(cov)
        elif disc and len(ms)>1: o['disc']=min(v for _,v in ms);o['cover']=max(v for _,v in ms)
        elif len(ms)>=2: o['disc']=min(v for _,v in ms);o['cover']=max(v for _,v in ms)
        elif disc: o['disc']=disc[0]
        elif cov: o['cover']=cov[0]
        if o['cover'] and o['disc'] and o['cover']<o['disc']: o['cover'],o['disc']=o['disc'],o['cover']
        if o['title']: res.append(o)
    return res
if __name__=='__main__':
    import glob,os
    from multiprocessing import Pool
    names=sys.argv[2:] or [os.path.basename(x)[:-4] for x in sorted(glob.glob(CACHE+'/pdf/*.pdf'))]
    def go(n):
        try: return n,interpret(parse(CACHE+f'/pdf/{n}.pdf'))
        except Exception as e:
            import traceback;print('ERR',n,repr(e),file=sys.stderr);return n,[]
    with Pool(2) as P: res=dict(P.map(go,names))
    json.dump(res,open(sys.argv[1],'w'),ensure_ascii=False)
    print('total',sum(map(len,res.values())))
