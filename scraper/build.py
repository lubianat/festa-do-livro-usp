"""Limpa os dados (maiúsculas, artigos invertidos, acentos quebrados) e gera site/<ano>/data.json."""
import json,re,subprocess,html,unicodedata
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
P={p['url']:p for p in json.load(open(CACHE+'/pubs.json'))}
D=json.load(open(CACHE+'/merged.json'))
# matrix special-case
# caso especial: a lista da Matrix traz ISBNs truncados (10 dígitos)
import os as _os
t=subprocess.run(['pdftotext','-layout',CACHE+'/pdf/matrix.pdf','-'],capture_output=True,text=True).stdout if _os.path.exists(CACHE+'/pdf/matrix.pdf') else ''
if t: D['matrix']=[]
for l in t.splitlines():
    m=re.match(r'^(97\d{8})\s+(.+?)\s{2,}(\d+,\d{2})\s+R\$\s*(\d+,\d{2})',l)
    if m: D['matrix'].append(dict(isbn='',title=m.group(2),author='',subject='',url='',price=float(m.group(4).replace(',','.')),orig=float(m.group(3).replace(',','.'))))
def bad(s,pubname):
    s=s.strip(' -;|')
    if not s or s in('R$','#REF!','-') or (re.fullmatch(r'[\W\d.,]+',s) and not re.fullmatch(r'\d{3,4}',s)): return ''
    if re.match(r'^\d+,\d{2}\s',s): s=re.sub(r'^\d+,\d{2}\s*','',s)
    return s
def strip_pub(s,names):
    for n in names:
        if n and s.lower().startswith(n.lower()+' '): return s[len(n)+1:]
    return s
SMALL={'a','o','as','os','e','de','da','do','das','dos','em','na','no','nas','nos','para','por','com','um','uma','à','ao','aos','às','the','of','and','y','la','el','le','les','des','du','et','en','sem','sob','entre'}
ROMAN=re.compile(r'^(?=[ivxlc]+$)c{0,3}(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$')
def tcase(s):
    letters=[c for c in s if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters)/len(letters)<0.85: return s
    out=[];first=True
    for w in re.split(r'(\s+|-|/|\()',s.lower()):
        if not w or w.isspace() or w in '-/(': out.append(w);continue
        core=w.strip('.,:;!?"\'')
        if ROMAN.match(core) and len(core)>0: out.append(w.upper())
        elif not first and core in SMALL: out.append(w)
        else: out.append(w[:1].upper()+w[1:] if w[0].isalpha() else w[:2].upper()+w[2:] if len(w)>1 and not w[0].isalnum() else w)
        first=w.endswith((':','.','?','!'))
    s2=re.sub(r'([A-Z]\.)([a-z])',lambda m:m.group(1)+m.group(2).upper(),''.join(out))
    return re.sub(r'\b([a-z])\.(?=[a-z]|\s|$)',lambda m:m.group(1).upper()+'.',s2)
ART=re.compile(r'^(.*?),\s*(O|A|OS|AS|Os|As|o|a|os|as|UM|UMA|Um|Uma)\s*$')
def fixmoji(s):
    if any(x in s for x in ('Ã','Â','â€')):
        try: return s.encode('cp1252').decode('utf8')
        except Exception:
            return s.replace('Â€“','–').replace('â€“','–').replace('â€”','—').replace('â€œ','“').replace('â€','”').replace('Â','')
    return s
NAMEPAT=re.compile(r"^[A-ZÀ-Ý][\w'’.-]+(?: [\w'’.-]+){0,2}, [A-ZÀ-Ý][\w.]*(?: [\w.]+){0,3}$")
def clean_author(au,name):
    if not au: return au
    nl=name.lower();al=au.lower().strip()
    first=re.sub(r'\(.*\)','',nl).split()[0] if nl.split() else nl
    if al in(nl,'editora '+nl,'equipe '+first,first,'editora '+first) or al==nl.split(' (')[0]: return ''
    au=re.sub(r'\s+(editora\s+)?'+re.escape(name.split(' (')[0])+r'\s*$','',au,flags=re.I)
    au=re.sub(r'\s*\bEDITORA\b.*$','',au,flags=re.I) if not re.match(r'(?i)editora',au) else au
    au=re.sub(r'(?<=[a-zà-ú])EDITORA.*$','',au)
    return au.strip()
def kern(s): return re.sub(r'(^|[\s("“-])([TVWYPFAL]) (?=[a-zà-ÿ]{2})',r'\1\2',s)
def uninvert(t):
    m=ART.match(t)
    if m and len(m.group(1))>2: return m.group(2).capitalize()+' '+m.group(1)
    return t
# ponytail: hand-fixed rows where the PDF swaps title and author; a sort-order heuristic could catch more (~50 found)
SWAP={'9788594933065'}  # Aves no Sesc Bertioga
pubs=[];rows=[]
for k,v in sorted(D.items(),key=lambda kv:P[kv[0]]['name'].lower()):
    p=P[k];name=html.unescape(p['name']).strip()
    if not v: continue
    i=len(pubs);pubs.append({'n':name,'logo':p.get('logo') or '','pdf':p['price_list'],'site':p.get('site') or '','c':0})
    names=[name,'Editora '+name.split()[0], 'Editora Nós']
    for r in v:
        title=bad(kern(fixmoji(r['title'])),name);title=uninvert(tcase(title)) if title else title
        if not title or len(title)<2: continue
        au=tcase(clean_author(strip_pub(bad(kern(fixmoji(r['author'])),name),names),name));su=tcase(bad(fixmoji(r['subject']),name))
        if title and au and NAMEPAT.match(title) and not NAMEPAT.match(au) and ',' not in au: title,au=uninvert(au),title
        if r['isbn'] in SWAP: title,au=au,title
        if su==title: su=''
        if au==title: au=''
        rows.append([i,title,au,su,r['isbn'] if len(r['isbn'])>=10 else '',r['price'],r['orig'],r['url']])
        pubs[i]['c']+=1
json.dump({'pubs':pubs,'rows':rows},open(OUT_DATA,'w'),ensure_ascii=False,separators=(',',':'))
print(len(pubs),'pubs',len(rows),'rows');import os;print(os.path.getsize(OUT_DATA)//1024,'KB')
