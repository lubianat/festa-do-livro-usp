"""Preenche as meta tags (descrição, URL, imagem) do site da edição com os números atuais,
gera a página inicial site/index.html com a lista de edições, robots.txt e sitemap.xml."""
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import json,re,datetime,html
D=json.load(open(OUT_DATA));nb=len(D['rows']);ne=sum(1 for p in D['pubs'] if not p.get('mo'))
fmt=lambda n:f'{n:,}'.replace(',','.')
desc=f'Catálogo da {CFG["titulo"]} ({ANO}): {fmt(nb)} livros de {ne} editoras com preços da Festa, busca por título, autor e tema, e mapa de onde fica cada editora.'
root=SITE_URL if SITE_URL.endswith('/') else SITE_URL+'/'
u=root+ANO+'/'
f=os.path.join(SITE,'index.html');s=open(f).read()
for pat in [r'(<meta name="description" content=")[^"]*',r'(<meta property="og:description" content=")[^"]*',r'(<meta name="twitter:description" content=")[^"]*']:
    s=re.sub(pat,lambda m:m.group(1)+desc,s)
s=re.sub(r'(<meta property="og:url" content=")[^"]*',lambda m:m.group(1)+u,s)
s=re.sub(r'(<link rel="canonical" href=")[^"]*',lambda m:m.group(1)+u,s)
s=re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*',lambda m:m.group(1)+u+'og.png',s)
open(f,'w').write(s)
# edições publicadas (pastas site/<ano>/ com index.html), mais recente primeiro
eds=[]
for a in sorted(os.listdir(SITE_ROOT),reverse=True):
    if a.isdigit() and os.path.exists(os.path.join(SITE_ROOT,a,'index.html')):
        c=json.load(open(os.path.join(HERE,'edicoes',a,'config.json'))) if os.path.exists(os.path.join(HERE,'edicoes',a,'config.json')) else {'titulo':'Festa do Livro da USP'}
        eds.append((a,c['titulo']))
last=eds[0][0]
items='\n'.join(f'<li><a href="{a}/"><b>{a}</b> — {html.escape(t)}</a></li>' for a,t in eds)
landing=f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Catálogo da Festa do Livro da USP</title>
<meta name="description" content="Catálogos navegáveis das edições da Festa do Livro da USP: busca de livros, preços da Festa e mapa das editoras.">
<link rel="canonical" href="{root}">
<meta property="og:type" content="website"><meta property="og:title" content="Catálogo da Festa do Livro da USP">
<meta property="og:description" content="Busca de livros, preços da Festa e mapa das editoras."><meta property="og:url" content="{root}">
<meta property="og:image" content="{root}{last}/og.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{last}/icon-192.png">
<style>body{{margin:0;font:16px/1.6 "Open Sans",Arial,sans-serif;color:#333}}header{{background:#1a5490;color:#fff;border-bottom:4px solid #fcb421;padding:16px}}
h1{{margin:0;font-size:22px}}main{{max-width:760px;margin:0 auto;padding:16px}}a{{color:#1a5490}}li{{margin:6px 0}}.big{{display:inline-block;margin:8px 0 16px;padding:10px 16px;background:#1a5490;color:#fff;border-radius:3px;text-decoration:none;font-weight:700}}
footer{{max-width:760px;margin:0 auto;padding:16px;font-size:13px;color:#777;border-top:1px solid #ddd}}</style></head><body>
<header><h1>Catálogo da Festa do Livro da USP</h1></header>
<main><p>Livros, preços da Festa e o mapa de onde fica cada editora — montado a partir das listas de preços que as editoras publicam no site oficial.</p>
<a class="big" href="{last}/">Abrir a edição {last} →</a>
<h2 style="font-size:17px">Edições</h2><ul>
{items}
</ul></main>
<footer>Projeto independente, não oficial. Listas originais em <a href="https://festadolivro.edusp.com.br">festadolivro.edusp.com.br</a>. Código: <a href="https://github.com/lubianat/festa-do-livro-usp">github.com/lubianat/festa-do-livro-usp</a>.</footer>
</body></html>
'''
open(os.path.join(SITE_ROOT,'index.html'),'w').write(landing)
open(os.path.join(SITE_ROOT,'robots.txt'),'w').write(f'User-agent: *\nAllow: /\nSitemap: {root}sitemap.xml\n')
today=datetime.date.today().isoformat()
urls=''.join(f'<url><loc>{root}{a}/</loc><lastmod>{today}</lastmod></url>' for a,_ in eds)
open(os.path.join(SITE_ROOT,'sitemap.xml'),'w').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{root}</loc><lastmod>{today}</lastmod></url>{urls}</urlset>\n')
print('seo ok:',desc)
