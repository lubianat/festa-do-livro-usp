"""Leitor 2: posição das palavras sob o cabeçalho (para PDFs sem bordas). Roda só onde o leitor 1 falhou."""
import pdfplumber,re,json,sys,os
from parse import norm,classify,money
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
PRICE=re.compile(r'^(R\$)?\d{1,3}(\.\d{3})*,\d{2}$')
ISB=re.compile(r'^(97[89][\d\-]{10,14}|97[89]\d{10})(.*)$')
def cells_of(line):
    line=sorted(line,key=lambda w:w['x0']);cs=[];cur=None
    for w in line:
        if cur and w['x0']-cur['x1']<5: cur['text']+=' '+w['text'];cur['x1']=w['x1']
        else: cur=dict(text=w['text'],x0=w['x0'],x1=w['x1'],top=w['top']);cs.append(cur)
    return cs
def lines_of(words):
    words=sorted(words,key=lambda w:(round(w['top']),w['x0']));L=[]
    for w in words:
        if L and abs(L[-1][0]['top']-w['top'])<2.5: L[-1].append(w)
        else: L.append([w])
    return L
def parse(f):
    out=[];hdr=None
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            words=page.extract_words(x_tolerance=1.5,y_tolerance=2)
            # split stuck R$ and ISBN+title
            ws=[]
            for w in words:
                t=w['text']
                if t=='R$': continue
                m=ISB.match(t)
                if m and m.group(2) and not m.group(2)[0].isdigit():
                    cw=(w['x1']-w['x0'])/len(t);k=len(m.group(1))
                    ws.append({**w,'text':m.group(1),'x1':w['x0']+cw*k});ws.append({**w,'text':m.group(2),'x0':w['x0']+cw*k});continue
                ws.append({**w,'text':t.replace('R$','')})
            L=lines_of(ws);top0=0
            for i,l in enumerate(L):
                txt=norm(' '.join(w['text'] for w in l))
                if 'TITUL' in txt and ('AUTOR' in txt or 'ISBN' in txt):
                    hw=[w for j in range(max(0,i-2),min(len(L),i+3)) for w in L[j] if abs(L[j][0]['top']-l[0]['top'])<25]
                    h={}
                    for w in hw:
                        k=classify(w['text'])
                        if k and k not in('cover','disc'): h.setdefault(k,[]).append((w['x0']+w['x1'])/2)
                    hdr={k:sum(v)/len(v) for k,v in h.items()};top0=max(w['bottom'] for w in hw);break
            if not hdr: continue
            body=[l for l in L if l[0]['top']>top0+1]
            anchors=[]
            for l in body:
                pr=[w for w in l if PRICE.match(w['text'])]
                if pr: anchors.append((l[0]['top'],sorted(pr,key=lambda w:w['x0'])))
            if not anchors: continue
            recs=[{'_y':y,'_p':[money(w['text']) for w in p],'_px':{id(w) for w in p}} for y,p in anchors]
            pids=set().union(*[r['_px'] for r in recs])
            for l in body:
                y=l[0]['top']
                r=min(recs,key=lambda r:abs(r['_y']-y))
                if abs(r['_y']-y)>30: continue
                for c in cells_of([w for w in l if id(w) not in pids]):
                    if PRICE.match(c['text'].split()[-1]): continue
                    cx=c['x0'] if c['x1']-c['x0']>60 else (c['x0']+c['x1'])/2
                    m=ISB.match(c['text'].replace(' ',''))
                    k='isbn' if m and 'isbn' in hdr else min(hdr,key=lambda k:abs(hdr[k]-cx) if hdr[k]>=cx-40 else 1e9)
                    if c['x1']-c['x0']>60: # long cell: column whose center is inside it, leftmost
                        inside=[k2 for k2 in hdr if c['x0']-15<=hdr[k2]<=c['x1']+15]
                        if inside: k=min(inside,key=lambda k2:hdr[k2])
                    r.setdefault(k,[]).append((y,c['x0'],c['text']))
            for r in recs:
                p=r['_p'];o={}
                for k in hdr:
                    if k in r: o[k]=' '.join(t for _,_,t in sorted(r[k])).replace('- ','-') if k=='url' else ' '.join(t for _,_,t in sorted(r[k]))
                if k=='url' and 'url' in o: o['url']=o['url'].replace(' ','')
                if 'url' in o: o['url']=o['url'].replace(' ','')
                o['cover']=str(max(p)) ; o['disc']=str(min(p))
                if o.get('title'): out.append(o)
    return out
if __name__=='__main__':
    from multiprocessing import Pool
    names=sys.argv[2:]
    with Pool(8) as P: rs=P.map(parse,[CACHE+f'/pdf/{n}.pdf' for n in names])
    res=dict(zip(names,rs));json.dump(res,open(sys.argv[1],'w'),ensure_ascii=False)
    print('total',sum(map(len,rs)),'empty',[n for n,r in res.items() if not r])
