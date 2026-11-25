"""Funções auxiliares (rótulos de colunas, regex de ISBN e preço) usadas pelo leitor 6."""
import pdfplumber,re,json,sys,unicodedata
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
def norm(s): return unicodedata.normalize('NFD',s or '').encode('ascii','ignore').decode().upper()
ISBN=re.compile(r'(97[89][\d\-]{10,15}\d|97[89]\d{7,10})')
MONEY=re.compile(r'^\D{0,4}?(\d{1,3}(?:\.\d{3})*,\d{1,2}|\d{1,4}\.\d{2})\D{0,3}$')
INT=re.compile(r'^\D{0,4}?(\d{1,4})\D{0,2}$')
def label(t):
    n=norm(t)
    if not n.strip(): return None
    for k,ws in [('url',['URL','LINK','SITE','HTTP']),('isbn',['ISBN','BARRA','EAN','COD']),('title',['TITUL','TITLE','DESCRI','PRODUTO','OBRA','NOME DO LIVRO']),
                 ('author',['AUTOR','NOMAUT','AUTHOR']),('subject',['ASSUNTO','AREA','CATEG','GENERO','TEMA','INTERESSE','SUBJECT','COLEC']),
                 ('disc',['%','DESCONT','DESC.','DESC ','FEIRA']),('qty',['QTD','QTDE','QUANT','ESTOQ','VEND','SKU']),('pub',['EDITORA','SELO','MARCA','PUBLISHER']),
                 ('disc',['DESCONT','FEIRA','50%','USP','POR ','COM','FESTA','PROMO']),('cover',['CAPA','PRECO','VALOR','VLR','UNIT','$',' DE '])]:
        if any(w in ' '+n+' ' for w in ws): return k
def lines(chars,tol=2.2):
    cs=sorted(chars,key=lambda c:(c['top'],c['x0']));L=[]
    for c in cs:
        if L and abs(L[-1]['top']-c['top'])<tol: L[-1]['c'].append(c)
        else: L.append({'top':c['top'],'c':[c]})
    for l in L: l['c'].sort(key=lambda c:c['x0'])
    return L
def words(cs,gap=2.5):
    W=[];cur=None
    for c in cs:
        if c['text'].isspace(): 
            if cur: cur['sp']=True
            continue
        if cur and c['x0']-cur['x1']<gap and not (cur.get('sp') and c['x0']-cur['x1']>0.8): cur['t']+=c['text'];cur['x1']=c['x1']
        elif cur and c['x0']-cur['x1']<gap: cur['t']+=' '+c['text'];cur['x1']=c['x1'];cur['sp']=False
        else: cur={'t':c['text'],'x0':c['x0'],'x1':c['x1']};W.append(cur)
    return W
def gutters(L,W,x0,x1):
    # coverage of chars per 1pt bin
    n=int(x1-x0)+2;cov=[0]*n
    for l in L:
        seen=set()
        for c in l['c']:
            if c['text'].isspace(): continue
            for b in range(int(c['x0']-x0),int(c['x1']-x0)+1):
                if 0<=b<n: seen.add(b)
        for b in seen: cov[b]+=1
    th=max(1,len(L)*0.03)
    cuts=[];i=0
    while i<n:
        if cov[i]<th:
            j=i
            while j<n and cov[j]<th: j+=1
            if j-i>=3 and i>0 and j<n: cuts.append(x0+(i+j)/2)
            i=j
        else: i+=1
    return cuts
def parse(f):
    out=[];hdr=None
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            ch=[c for c in page.chars if c.get('upright',True)]
            if not ch: continue
            L=lines(ch)
            for l in L: l['w']=words(l['c']);l['txt']=' '.join(w['t'] for w in l['w'])
            hi=None
            for i,l in enumerate(L[:25]):
                n=norm(l['txt'])
                if any(k in n for k in('TITUL','TITLE','PRODUTO','DESCRI')) and not ISBN.search(l['txt']): hi=i;break
            body_start=0
            if hi is not None:
                hl=[w for l in L if abs(l['top']-L[hi]['top'])<22 and not ISBN.search(l['txt']) for w in l['w']]
                hdr=hl;body_start=max(j for j,l in enumerate(L) if abs(l['top']-L[hi]['top'])<22 and not ISBN.search(l['txt']))+1
            if hdr is None: continue
            B=L[body_start:]
            anchors=[l for l in B if ISBN.search(l['txt'][:40])]
            if not anchors: continue
            x0=min(c['x0'] for c in ch);x1=max(c['x1'] for c in ch)
            cuts=gutters(anchors,None,x0,x1)
            bounds=[x0-1]+cuts+[x1+1]
            cols=[(bounds[i],bounds[i+1]) for i in range(len(bounds)-1)]
            # label columns from header words (center inside)
            lab={}
            for ci,(a,b) in enumerate(cols):
                ws=[w['t'] for w in hdr if a<= (w['x0']+w['x1'])/2 <b]
                if not ws: ws=[w['t'] for w in hdr if w['x0']<b and w['x1']>a]
                lab[ci]=label(' '.join(ws))
            # row bands
            ys=[a['top'] for a in anchors]
            recs=[{'_y':y,'cells':{}} for y in ys]
            for l in B:
                if l in anchors: r=recs[anchors.index(l)]
                else:
                    k=min(range(len(ys)),key=lambda k:abs(ys[k]-l['top']))
                    if abs(ys[k]-l['top'])>28: continue
                    r=recs[k]
                for c in l['c']:
                    if c['text'].isspace(): continue
                    cx=(c['x0']+c['x1'])/2
                    ci=next(i for i,(a,b) in enumerate(cols) if a<=cx<b)
                    r['cells'].setdefault(ci,{}).setdefault(round(l['top'],1),[]).append(c)
            for r in recs:
                cells={}
                for ci,byline in r['cells'].items():
                    parts=[]
                    for y in sorted(byline):
                        parts.append(' '.join(w['t'] for w in words(sorted(byline[y],key=lambda c:c['x0']))))
                    cells[ci]=parts
                out.append({'lab':lab,'cells':cells})
    return out
def interpret(raw):
    res=[]
    for r in raw:
        lab=r['lab'];o={'title':[],'author':[],'subject':[],'pub':[],'url':'','isbn':'','money':[],'ints':[]}
        for ci in sorted(r['cells']):
            parts=r['cells'][ci];k=lab.get(ci);txt=' '.join(parts).strip()
            if not txt: continue
            m=ISBN.search(txt.replace(' ',''))
            if (k=='isbn' or (m and not o['isbn'] and k not in('title','author'))) and m:
                o['isbn']=m.group(1).replace('-','');rest=txt.replace(' ','').replace(m.group(1),'',1)
                if k=='isbn' and len(rest)>3 and re.search('[A-Za-z]',rest):  # glued title
                    o['title'].append(txt[txt.find(m.group(1)[-3:])+3:].strip() if m.group(1)[-3:] in txt else rest)
                continue
            if k=='url' or txt.startswith('http'):
                o['url']=''.join(parts).replace(' ','');continue
            toks=txt.split()
            if all(MONEY.match(t) or INT.match(t) for t in toks):
                for t in toks:
                    mm=MONEY.match(t)
                    if mm: v=mm.group(1);o['money'].append((k,float(v.replace('.','').replace(',','.')) if ',' in v else float(v)))
                    elif k in('cover','disc'): o['money'].append((k,float(INT.match(t).group(1))))
                continue
            if k in('qty',): continue
            if k in('cover','disc') and re.fullmatch(r'[\W\d.,R$]*',txt): continue
            if k in('title','author','subject','pub'): o[k].append(txt)
            elif k in ('cover','disc','isbn',None):
                # unlabeled text: fill title then author then subject
                (o['title'] if not o['title'] else o['author'] if not o['author'] else o['subject']).append(txt)
        res.append(o)
    return res
if __name__=='__main__':
    import glob,os
    from multiprocessing import Pool
    names=sys.argv[2:] or [os.path.basename(x)[:-4] for x in sorted(glob.glob(CACHE+'/pdf/*.pdf'))]
    def go(n):
        try: return n,interpret(parse(CACHE+f'/pdf/{n}.pdf'))
        except Exception as e: print('ERR',n,e,file=sys.stderr);return n,[]
    with Pool(2) as P: res=dict(P.map(go,names))
    json.dump(res,open(sys.argv[1],'w'),ensure_ascii=False)
    print('total',sum(map(len,res.values())))
