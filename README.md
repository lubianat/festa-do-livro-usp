# Catálogo da Festa do Livro da USP

Site que junta, num só lugar, as listas de preços que as editoras publicam no site oficial da [Festa do Livro da USP](https://festadolivro.edusp.com.br): busca por título, autor e tema, filtro por editora, favoritos e o mapa de onde fica cada editora.

**Edição atual: 2026 (28ª Festa).** Site: <https://lubianat.github.io/festa-do-livro-usp/2026/>

Projeto independente, não oficial. Os dados são lidos automaticamente dos PDFs das editoras e podem ter erros — confira sempre o PDF original antes de ir ao estande.

## O que o site faz

- **Busca por palavras**, sem precisar de acento, com tolerância a erros de digitação ("dostoievsky" acha Dostoiévski). Opção de busca exata nos Filtros.
- **Busca por tema**: encontra livros pelo sentido, não só pela palavra ("ditadura" traz livros sobre repressão e golpe de 1964), e sugere palavras próximas.
- **Filtro por editora** com busca (várias editoras ao mesmo tempo), incluindo editoras que estão no mapa mas ainda não publicaram lista.
- **Página de cada livro e de cada editora**, com minimapa destacando onde ela fica e livros parecidos.
- **Favoritos** guardados no navegador, organizados na ordem do mapa (um roteiro pela Festa).
- **Capas** carregadas na hora pelo ISBN, priorizando a Open Library: primeiro a capa da edição, depois a capa de qualquer edição da mesma obra; só se a Open Library não tiver nenhuma, usa o Google Books. Quando não há capa, a página do livro tem um link para adicioná-la na Open Library.
- **App instalável (PWA)**: "Adicionar à tela inicial" no celular; funciona sem internet depois da primeira visita (as capas só com internet).
- Links de busca compartilháveis: `.../2026/?q=mitologia` (e `&tema` para busca por tema).

## Estrutura

```
site/                     o que vai para o GitHub Pages
  index.html              página inicial com a lista de edições (gerada pelo scraper/seo.py)
  2026/                   site da edição 2026
    index.html            o app inteiro (HTML + CSS + JS, sem dependências)
    data.json             livros e editoras
    words.json, *.b64.txt vetores da busca por tema
    *.webp                mapas oficiais da Festa
    sw.js, manifest.webmanifest, icon-*.png, og.png   PWA e compartilhamento
scraper/                  pipeline que gera os dados
  run.py                  roda tudo
  paths.py                caminhos e edição (variável EDICAO)
  edicoes/2026/           configuração e tabelas do mapa da edição 2026
  cache/                  PDFs e arquivos intermediários (fora do git)
.github/workflows/
  pages.yml               publica site/ no GitHub Pages a cada mudança
  update.yml              roda o scraper todo dia e publica se houver lista nova
```

## Como os dados são gerados

1. **fetch** (`pubs.py`): lista as editoras do evento pela API do site da Festa.
2. **download** (`download.py`): baixa o PDF da lista de preços de cada editora.
3. **parse** (`parse*.py`): cada editora usa um formato de planilha diferente, então há vários leitores. O principal (`parse6.py`) lê os caracteres na ordem em que o PDF os desenha, o que resolve colunas sobrepostas; os outros cobrem casos que ele erra.
4. **merge** (`merge.py`): para cada editora, fica com o leitor que extraiu mais livros completos.
5. **build** (`build.py`, `augment.py`): limpa os textos (maiúsculas, "DEUSES DE CASACA, OS" → "Os Deuses de Casaca", acentos quebrados), liga cada editora ao seu número no mapa e inclui as editoras do mapa que ainda não publicaram lista.
6. **embed** (`embed.py`): calcula os vetores da busca por tema com os vetores de palavras em português do spaCy (`pt_core_news_lg`, baixado do GitHub na primeira vez, ~570 MB).
7. **seo** (`seo.py`): preenche descrição e imagem de compartilhamento com os números atuais e gera a página inicial, `robots.txt` e `sitemap.xml`.

## Rodar localmente

Precisa de Python 3.10+ e do `pdftotext` (pacote `poppler-utils` no Linux, `poppler` no Homebrew).

```bash
pip install -r scraper/requirements.txt
python scraper/run.py                 # tudo (10–20 min na primeira vez)
python scraper/run.py --from merge    # recomeçar de uma etapa
python -m http.server -d site 8000    # ver em http://localhost:8000/2026/
```

## Publicar no GitHub Pages

1. Suba este repositório para o GitHub.
2. Em **Settings → Pages**, escolha **Source: GitHub Actions**.
3. Pronto: o workflow `pages.yml` publica `site/` a cada push, e o `update.yml` roda todo dia às 6h17 (Brasília) procurando listas novas. Também dá para rodar o `update.yml` na mão, na aba **Actions**.

Se o site não ficar em `https://lubianat.github.io/festa-do-livro-usp/`, ajuste a variável `SITE_URL` (o workflow já calcula a partir do nome do repositório).

## Nova edição (ex.: 2027)

1. Crie `scraper/edicoes/2027/config.json` copiando o de 2026 e trocando `ano`, `edicao`, `evento` (o trecho da URL do evento no site da Festa, ex. `29-festa-do-livro-da-usp`) e `titulo`.
2. Copie `site/2026/` para `site/2027/` e, no `index.html`, troque "2026"/"28ª" pelos novos valores (título, cabeçalho, chaves `festa-2026-*` do armazenamento local) e no `sw.js` o nome do cache.
3. **Mapas** (a parte manual): baixe as imagens dos mapas da nova edição para `site/2027/`, atualize os nomes dos arquivos (`MAPF`) e as caixas de cada número (`ISL`) no `index.html`, e faça a tabela `scraper/edicoes/2027/editora_ilha.json` (`"Nome da editora": número`) a partir das legendas dos mapas. Sem isso, o site funciona normalmente, só sem minimapa.
4. Troque `EDICAO: '2026'` por `'2027'` em `.github/workflows/update.yml` e rode `EDICAO=2027 python scraper/run.py`.
5. A página inicial (`site/index.html`) passa a listar as duas edições automaticamente, com a mais recente em destaque.

As edições anteriores continuam no ar, cada uma na sua pasta.

## Limitações conhecidas

- Os PDFs não seguem um padrão; alguns livros ficam com autor faltando, título cortado ou só um preço. Cerca de 2,5% não têm preço legível.
- Algumas editoras (como Universo dos Livros e Phorte) não informam preço; a Pontes informa só o preço de capa.
- Editoras que vêm dentro da lista de um grupo (ex.: Paz e Terra e Civilização Brasileira, na lista do Grupo Record) apontam para a lista do grupo.
- A busca por tema usa vetores de palavras, não um modelo de linguagem: entende bem temas ("mitologia grega", "racismo"), mas não frases complexas.

## Licença

Código sob a licença [MIT](LICENSE). Os dados dos livros vêm das listas públicas das editoras; os mapas são da organização da Festa do Livro da USP.
