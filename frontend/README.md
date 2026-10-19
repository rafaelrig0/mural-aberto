# Mural Aberto — Frontend

Site público e painel do administrador do catálogo de obras. É feito só com **HTML, CSS e
JavaScript puros** (sem Node, sem build, sem dependências): páginas estáticas que conversam com a
API do `backend/`. O visual segue o site de exemplo (fundo branco, cartões arredondados, menu em
"pílula" e destaque laranja).

## Páginas

| Arquivo | Para quê |
|---|---|
| `index.html` | Início: **carrossel** com as obras mais recentes, **votação de obras**, destaque das organizações e "como funciona" |
| `obras.html` | Obras com busca, filtro por **categoria** e paginação. O botão **+ Adicionar obra** abre uma **janela (modal)** de envio |
| `obra.html?id=N` | Detalhe da obra, voto, comentários aprovados e formulário de comentário |
| `organizacoes.html` | **Organizações** parceiras (divulgação) |
| `feedback.html` | **Enviar Feedback:** nome (opcional), tipo, mensagem e nota de 1 a 5 (opcional) |
| `admin.html` | Painel: obras, comentários, feedbacks, categorias e histórico de moderação |

Não existe mais `enviar-obra.html`: quem clica em "Adicionar obra" (inclusive na página inicial)
vai para `obras.html`, onde o modal abre.

## Como rodar (Windows, CMD)

1. Deixe o backend rodando em `http://localhost:8000` (veja `backend/README.md`).
2. Em outro CMD:
```bat
cd /d D:\projetos\mural-aberto\frontend
python -m http.server 5173
```
3. Abra http://localhost:5173

Use exatamente a porta **5173**: é a origem que o backend libera em `CORS_ORIGINS`. Não abra os
arquivos com duplo clique (`file://`): o navegador bloqueia as chamadas à API.

Para usar outra porta ou endereço, ajuste `CORS_ORIGINS` no `.env` do backend e `URL_API` em
`js/config.js`.

## Primeiro uso

Nenhuma obra aparece no site até um administrador aprová-la. Entre em `admin.html` com o e-mail
criado por `python -m app.scripts.create_admin`, abra **Obras → Pendentes** e aprove. Enquanto
não houver obras aprovadas, o carrossel e a votação mostram um convite para enviar a primeira.

## Categoria e tipo da obra (são a mesma coisa)

No modal a pessoa escolhe só a **Categoria**. O backend também exige o campo `work_type`
(`visual` ou `text`); o site o deduz da categoria:

- categorias de **texto** (Poema, Crônica, Conto) mostram o campo "Texto da obra";
- as demais (Fotografia, Pintura, Grafite, Desenho…) pedem imagem e/ou vídeo.

A lista de categorias de texto está em `js/config.js` (`CATEGORIAS_DE_TEXTO`, pelo apelido/slug da
categoria). Se criar no painel uma categoria nova que seja de texto, acrescente o apelido dela ali.
O filtro "Tipo" e a etiqueta de tipo foram removidos das páginas.

## Votação de obras — limite importante

O backend **ainda não tem um recurso de votos**. Por isso a votação funciona só no navegador
(`localStorage`): cada pessoa tem um voto, pode mudá-lo ou removê-lo, mas a contagem **não é somada
entre visitantes** (e o site avisa isso na tela). Todo o acesso aos votos está em `js/votos.js`
(`lerVoto`, `contagem`, `votar`, `removerVoto`); quando o backend ganhar o recurso, basta trocar
essas quatro funções por chamadas à API.

## Organizações parceiras

O backend não tem cadastro de organizações; a lista fica em **`js/organizacoes-dados.js`** (nome,
descrição, contribuições e site). Os itens que vêm no arquivo são **exemplos** (`Organização
Exemplo 1…4`, com endereços `example.org`): troque pelos dados reais. A página `organizacoes.html`
e o destaque da página inicial usam essa mesma lista.

## Identidade visual

Cores, fontes e espaçamentos ficam nas variáveis do início de `css/estilo.css` (bloco `:root`).
As fontes **Bricolage Grotesque** e **Figtree** vêm do Google Fonts; sem internet, o site usa as
fontes do sistema. O nome e o menu estão em `js/comum.js` (lista `MENU`, `montarCabecalho` e
`montarRodape`).

## Segurança

- Todo texto vindo da API é inserido como **texto** (nunca `innerHTML`), então HTML ou scripts
  enviados por visitantes aparecem escritos na tela e não executam.
- O login do administrador guarda o token só em `sessionStorage` (some ao fechar a aba) e o
  token expirado leva de volta à tela de login.
- O e-mail de contato das obras só aparece no painel; nunca nas páginas públicas.
- Links das organizações só aceitam `http(s)` e abrem com `rel="noopener noreferrer"`.

## Acessibilidade

Link "Pular para o conteúdo", menu navegável por teclado, foco sempre visível, campos com rótulo
e mensagens de erro ligadas ao campo, avisos que não dependem só de cor, modal com foco preso,
fechamento por Esc e retorno do foco ao botão, carrossel com botões, contador anunciado a leitores
de tela, setas do teclado e sem troca automática, alvos de toque com 44 px ou mais e respeito a
`prefers-reduced-motion`.
