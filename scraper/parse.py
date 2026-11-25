"""Leitor 1 dos PDFs: tabelas com bordas (pdfplumber.extract_tables)."""
import pdfplumber,re,json,sys,glob,os,unicodedata
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
ISBN=re.compile(r'^(97[89][\d\-\s]{9,16}\d|\d{9}[\dXx]|97[89]\d{10})')
MONEY=re.compile(r'(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2})')
def money(s):
    m=MONEY.search(s or '');
    if not m: return None
    v=m.group(1)
    return float(v.replace('.','').replace(',','.')) if ',' in v else float(v)
def norm(s): return unicodedata.normalize('NFD',s or '').encode('ascii','ignore').decode().upper()
KEYS=[('isbn','ISBN'),('title','TITUL'),('author','AUTOR'),('pub','EDITORA'),('subject','ASSUNTO'),('url','URL'),('cover','CAPA'),('disc','DESCONT')]
def classify(h):
    n=norm(h)
    if 'DESCONT' in n or ('COM' in n and 'PRECO' in n): return 'disc'
    if 'CAPA' in n or 'PRECO' in n: return 'cover'
    for k,w in KEYS:
        if w in n: return k
def parse(f):
    out=[]
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            for strat in ({},{"vertical_strategy":"text","horizontal_strategy":"text"}):
                tables=page.extract_tables(strat) if strat else page.extract_tables()
                got=[]
                for t in tables:
                    cols=None
                    for row in t:
                        cells=[(c or '').replace('\n',' ').strip() for c in row]
                        if cols is None or any('ISBN'==norm(c) for c in cells):
                            cand={i:classify(c) for i,c in enumerate(cells) if c and classify(c)}
                            if 'isbn' in cand.values() or ('title' in cand.values() and len(cand)>=3):
                                cols=cand; continue
                        if not cols: continue
                        r={}
                        for i,k in cols.items():
                            if i<len(cells) and cells[i]: r[k]=(r.get(k,'')+' '+cells[i]).strip()
                        if r.get('title') and (money(r.get('disc')) or money(r.get('cover'))):
                            got.append(r)
                if got: out+=got; break
    return out
if __name__=='__main__':
    res={}
    for f in sorted(glob.glob(CACHE+'/pdf/*.pdf')):
        try: res[os.path.basename(f)[:-4]]=parse(f)
        except Exception as e: res[os.path.basename(f)[:-4]]=[]; print('ERR',f,e)
    json.dump(res,open(sys.argv[1],'w'),ensure_ascii=False)
    z=[k for k,v in res.items() if not v]
    print('total',sum(map(len,res.values())),'empty',len(z),z)
