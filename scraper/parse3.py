"""Leitor 3: texto em colunas (pdftotext -layout), mapeando cada campo pelo cabeçalho."""
import re,json,sys,subprocess,unicodedata
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
def norm(s): return unicodedata.normalize('NFD',s or '').encode('ascii','ignore').decode().upper()
ISB=re.compile(r'^\s*(97[89][\d\-]{10,14}|97[89]\d{10}|85\d{8}|\d{9}[\dX])(?=\D|$)')
NUM=re.compile(r'^\D{0,3}?(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+\.\d{2})-?$')
def col(h):
    n=norm(h)
    if 'URL' in n or 'LINK' in n or 'SITE' in n: return 'url'
    if 'ISBN' in n or 'BARRA' in n or 'EAN' in n: return 'isbn'
    if 'TITUL' in n: return 'title'
    if 'AUTOR' in n: return 'author'
    if 'ASSUNTO' in n or 'AREA' in n or 'CATEGOR' in n or 'GENERO' in n or 'TEMA' in n: return 'subject'
    if 'QT' in n or 'ESTOQ' in n or 'VEND' in n: return 'qty'
    if 'EDITORA' in n or 'SELO' in n or 'MARCA' in n: return 'pub'
    if 'DESC' in n or 'FEIRA' in n or '%' in n or 'VENDA' in n or 'FESTA' in n or ' COM' in ' '+n: return 'disc'
    if 'PRECO' in n or 'CAPA' in n or 'VALOR' in n or 'VLR' in n or 'R$' in n: return 'cover'
def fields(line):
    return [(m.start(),m.group().strip()) for m in re.finditer(r'\S+(?: \S+)*',line)]
def tonum(s):
    s=s.replace('R$','').strip().rstrip('-'); m=NUM.match(s)
    if not m: return None
    v=m.group(1)
    if ',' in v: return float(v.replace('.','').replace(',','.'))
    if re.fullmatch(r'\d+\.\d{2}',v): return float(v)
    return float(v.replace('.',''))
def parse(f):
    txt=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout
    hdr=None;out=[];last=None
    for line in txt.splitlines():
        n=norm(line)
        if ('TITUL' in n) and ('AUTOR' in n or 'ISBN' in n or 'PRECO' in n or 'VALOR' in n):
            hdr=[(p,col(t)) for p,t in fields(line)];hdr=[(p,c) for p,c in hdr if c];continue
        if not hdr: continue
        fs=fields(line)
        if not fs: continue
        m=ISB.match(line)
        if not m:
            # continuation line: append text to title/author/subject of last record
            if last is not None and len(line.strip())<160:
                for p,t in fs:
                    c=min(hdr,key=lambda h:abs(h[0]-p))[1]
                    if c in('title','author','subject') and tonum(t) is None: last[c]=(last.get(c,'')+' '+t).strip()
            continue
        isbn=m.group(1);rest=line[:m.start(1)]+' '*len(isbn)+line[m.end(1):]
        r={'isbn':isbn};nums=[]
        for p,t in fields(rest):
            parts=re.split(r'\s+',t) if all(tonum(x) is not None for x in t.split()) else [t]
            for t2 in parts:
                c=min(hdr,key=lambda h:abs(h[0]-p))[1]
                v=tonum(t2)
                if v is not None and c not in('title','author','url','isbn'):
                    if c!='qty' and ',' in t2 or c in('cover','disc'): nums.append(v)
                    continue
                if c in('cover','disc','qty','isbn'):
                    c='title' if 'title' not in r else 'author' if 'author' not in r else 'subject'
                r[c]=(r.get(c,'')+' '+t2).strip()
        nums=[x for x in nums if 0<x<5000]
        if not nums or not r.get('title'): last=None;continue
        r['cover']=max(nums);r['disc']=min(nums)
        if 'url' in r: r['url']=r['url'].replace(' ','')
        out.append(r);last=r
    return out
if __name__=='__main__':
    import glob,os
    from multiprocessing import Pool
    fs=sorted(glob.glob(CACHE+'/pdf/*.pdf'))
    with Pool(2) as P: rs=P.map(parse,fs)
    res={os.path.basename(f)[:-4]:r for f,r in zip(fs,rs)}
    json.dump(res,open(sys.argv[1],'w'),ensure_ascii=False)
    print('total',sum(map(len,rs)),'empty',[k for k,v in res.items() if not v])
