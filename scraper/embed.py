"""Busca por tema: calcula um vetor para cada livro (título + assunto) com vetores de palavras em português do spaCy."""
import json,re,unicodedata,numpy as np
from collections import Counter
from spacy.vocab import Vocab
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
VEC=os.path.join(VEC_CACHE,'pt_core_news_lg','vocab')
if not os.path.exists(os.path.join(VEC,'vectors')):
    # Portuguese word vectors from spaCy's pt_core_news_lg release on GitHub (~570 MB download, only the vocab is kept)
    import urllib.request,zipfile,shutil
    whl=os.path.join(VEC_CACHE,'pt_core_news_lg.whl');os.makedirs(VEC_CACHE,exist_ok=True)
    if not os.path.exists(whl):
        print('downloading pt_core_news_lg …',flush=True)
        urllib.request.urlretrieve('https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-3.8.0/pt_core_news_lg-3.8.0-py3-none-any.whl',whl)
    with zipfile.ZipFile(whl) as z:
        for m in z.namelist():
            if '/vocab/' in m and not m.endswith('/'):
                dst=os.path.join(VEC,os.path.basename(m));os.makedirs(VEC,exist_ok=True)
                with z.open(m) as a,open(dst,'wb') as b: shutil.copyfileobj(a,b)
    os.remove(whl)
voc=Vocab().from_disk(VEC);V=voc.vectors
def strip(s): return ''.join(c for c in unicodedata.normalize('NFD',s) if not unicodedata.combining(c))
TOK=re.compile(r"[a-zà-ÿ]+(?:-[a-zà-ÿ]+)?")
STOP=set("a o e de da do das dos as os um uma uns umas em no na nos nas para por com sem sob ao aos à às que se sua seu suas seus ou mais como entre sobre the of and to in vol volume edição ed nova capa dura brochura kit box livro livros i ii iii iv v".split())
D=json.load(open(OUT_DATA));rows=D['rows']
def toks(s): return [t for t in TOK.findall((s or '').lower()) if len(t)>1 and t not in STOP]
# vector lookup with fallbacks (exact, capitalized)
cache={}
def wvec(t):
    if t in cache: return cache[t]
    v=None
    for f in (t,t.capitalize(),t.upper()):
        k=voc.strings[f]
        if k in V: v=V[k];break
    cache[t]=v;return v
docs_t=[(toks(r[1]),toks(r[3])) for r in rows]
freq=Counter(t for a,b in docs_t for t in set(a+b))
N=len(rows);a=1e-3*N
def wt(t): return a/(a+freq.get(t,0))
X=np.zeros((N,300),np.float32);has=np.zeros(N,bool)
for i,(ti,su) in enumerate(docs_t):
    acc=np.zeros(300,np.float32);ws=0
    for t,m in [(t,1.0) for t in ti]+[(t,1.3) for t in su]:
        v=wvec(t)
        if v is None: continue
        w=wt(t)*m;acc+=w*v/ (np.linalg.norm(v)+1e-6);ws+=w
    if ws>0: X[i]=acc/ws;has[i]=True
print('docs with vec',has.mean())
# PCA
mu=X[has].mean(0);Xc=X[has]-mu
U,S,Vt=np.linalg.svd(Xc[np.random.RandomState(0).choice(len(Xc),min(15000,len(Xc)),replace=False)],full_matrices=False)
K=int(__import__('sys').argv[1]) if len(__import__('sys').argv)>1 else 96
pc1=Vt[0]
def proj(M): 
    M=M-mu; M=M-np.outer(M@pc1,pc1); return M@Vt[1:K+1].T
Z=np.zeros((N,K),np.float32);Z[has]=proj(X[has])
Z/=np.linalg.norm(Z,axis=1,keepdims=True)+1e-9;Z[~has]=0
# word table: catalog vocab + common pt words
vocab={}
for t,c in freq.items():
    if wvec(t) is not None: vocab[strip(t)]=(t,c+1000)
# common words: first rows of vector table that are lowercase words
keys=list(V.key2row.items());keys.sort(key=lambda kr:kr[1])
added=0
for k,r in keys:
    try: s=voc.strings[k]
    except KeyError: continue
    if not re.fullmatch(r'[a-zà-ÿ]{3,}',s) or s in STOP: continue
    sk=strip(s)
    if sk not in vocab: vocab[sk]=(s,0);added+=1
    if added>=25000: break
words=sorted(vocab,key=lambda w:-vocab[w][1])
W=np.stack([wvec(vocab[w][0]) for w in words]).astype(np.float32)
W/=np.linalg.norm(W,axis=1,keepdims=True)
WZ=(W-mu)@Vt[1:K+1].T  # same space minus mean; pc1 removed at query time via proj on summed vec
# for query we sum weighted raw-word projections then remove pc1 component in reduced space? pc1 orthogonal to Vt[1:], already excluded
wts=np.array([wt(vocab[w][0]) if vocab[w][1]>=1000 else a/(a+0) for w in words],np.float32)
wts=np.minimum(wts,1.0)
print('vocab',len(words),'K',K)
def q8(M):
    s=np.abs(M).max(1,keepdims=True)+1e-9;return np.round(M/s*127).astype(np.int8),s.astype(np.float32).ravel()
Zq,_=q8(Z)  # docs: unit vectors, per-row scale not needed for cosine ranking
Wq,ws_=q8(WZ)
import base64
open(os.path.join(SITE,'docs.b64.txt'),'w').write(base64.b64encode(Zq.tobytes()).decode())
open(os.path.join(SITE,'words.b64.txt'),'w').write(base64.b64encode(Wq.tobytes()).decode())
json.dump({'K':K,'words':words,'disp':[vocab[w][0] for w in words],'scale':[round(float(x),5) for x in ws_],'wt':[round(float(x),4) for x in wts],'mu_proj':[0]*K},open(os.path.join(SITE,'words.json'),'w'),ensure_ascii=False,separators=(',',':'))
