"""Leitor 4: ancorado no ISBN de cada linha, sem depender do cabeçalho."""
import re,json,sys,subprocess,unicodedata
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
def norm(s): return unicodedata.normalize('NFD',s or '').encode('ascii','ignore').decode().upper()
ISB=re.compile(r'(97[89]\d{10}|97[89][\d\-]{12,15}\d)')
PR=re.compile(r'^[-R$€\s]*(\d{1,3}(?:\.\d{3})*,\d{1,2}|\d{1,4})[-\s]*$')
def num(t):
    m=PR.match(t)
    if not m: return None
    v=m.group(1); return float(v.replace('.','').replace(',','.')) if ',' in v else float(v)
def parse(f):
    txt=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout
    L=txt.splitlines();idx=[i for i,l in enumerate(L) if ISB.search(l[:40])]
    authfirst=False
    for l in L[:15]:
        n=norm(l)
        if 'AUTOR' in n and 'TITUL' in n and n.index('AUTOR')<n.index('TITUL'): authfirst=True
    hascomma=bool(re.search(r'\d,\d{2}\b',txt))
    out=[]
    for j,i in enumerate(idx):
        line=L[i];m=ISB.search(line[:40]);isbn=m.group(1).replace('-','')
        rest=line[m.end():]
        block=L[i+1:idx[j+1] if j+1<len(idx) else min(len(L),i+6)][:6]
        toks=[t.strip() for t in re.split(r'\s{2,}',rest) if t.strip()]
        # split tokens that glue text and price
        tt=[]
        for t in toks:
            mm=re.match(r'^(.*?\D)\s+((?:R\$\s*)?-?\d{1,3}(?:\.\d{3})*,\d{1,2}-?)$',t)
            tt+= [mm.group(1),mm.group(2)] if mm and not mm.group(1).strip().startswith('http') else [t]
        prices=[];text=[];url=''
        for t in tt:
            if t.startswith('http'): url=t;continue
            for sub in (t.split() if all(num(x) is not None for x in t.split()) else [t]):
                v=num(sub)
                if v is not None and (',' in sub or not hascomma) and len(text)>=1: prices.append(v)
                elif v is None or len(text)<1: text.append(sub)
        if not prices:
            for b in block:
                for t in re.split(r'\s{2,}',b):
                    v=num(t.strip())
                    if v is not None and ',' in t: prices.append(v)
        for b in block:
            s=b.strip()
            if url and re.match(r'^\S+$',s) and not ISB.search(s) and len(b)-len(b.lstrip())>60: url+=s
        if not hascomma and len(prices)>2: prices=prices[-2:]  # drop qty cols
        prices=[p for p in prices if 0<p<3000]
        text=[t for t in text if not re.fullmatch(r'[\d\s.,%-]+',t)]
        if not text: continue
        a,b=(1,0) if authfirst and len(text)>1 else (0,1)
        r={'isbn':isbn,'title':text[a],'author':text[b] if len(text)>1 else '',
           'subject':text[-1] if len(text)>3 else '', 'url':url}
        if prices: r['cover']=max(prices);r['disc']=min(prices)
        out.append(r)
    return out
if __name__=='__main__':
    import glob,os
    from multiprocessing import Pool
    fs=sorted(glob.glob(CACHE+'/pdf/*.pdf'))
    with Pool(2) as P: rs=P.map(parse,fs)
    res={os.path.basename(f)[:-4]:r for f,r in zip(fs,rs)}
    json.dump(res,open(sys.argv[1],'w'),ensure_ascii=False);print('total',sum(map(len,rs)))
