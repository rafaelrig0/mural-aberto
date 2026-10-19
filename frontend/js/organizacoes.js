/* Cartões das organizações parceiras (usados na página "Organizações" e na página inicial).
 * Os dados ficam em js/organizacoes-dados.js. Texto sempre inserido como texto, nunca como HTML. */
(function () {
  "use strict";
  const { criar } = window.Mural;

  const QUANTIDADE_DE_CORES = 6;

  function lista() {
    return Array.isArray(window.ORGANIZACOES) ? window.ORGANIZACOES : [];
  }

  /** Aceita apenas endereços http(s); qualquer outra coisa (como "javascript:") é ignorada. */
  function enderecoSeguro(texto) {
    try {
      const url = new URL(String(texto || ""));
      return url.protocol === "https:" || url.protocol === "http:" ? url.href : "";
    } catch {
      return "";
    }
  }

  function iniciais(nome) {
    const partes = String(nome).trim().split(/\s+/).filter(Boolean);
    const letras = partes.length > 1 ? partes[0][0] + partes[partes.length - 1][0] : String(nome).trim().slice(0, 2);
    return letras.toUpperCase();
  }

  function capa(org, indice) {
    const imagem = enderecoSeguro(org.imagem);
    return criar(
      "div",
      { classe: "org-capa cor-" + (indice % QUANTIDADE_DE_CORES), "aria-hidden": imagem && org.imagemAlt ? null : "true" },
      imagem
        ? criar("img", { src: imagem, alt: org.imagemAlt || "", loading: "lazy" })
        : criar("span", { texto: iniciais(org.nome) }),
    );
  }

  /** @param {object} opcoes  { linkTitulo: true } faz do nome um link para a página Organizações */
  function cartaoOrganizacao(org, indice, opcoes = {}) {
    const site = enderecoSeguro(org.site);
    const contribuicoes = Array.isArray(org.contribuicoes) ? org.contribuicoes : [];
    const corpo = criar(
      "div",
      { classe: "org-corpo" },
      criar(
        "h3",
        {},
        opcoes.linkTitulo
          ? criar("a", { href: "organizacoes.html#" + encodeURIComponent(org.id), texto: org.nome })
          : org.nome,
      ),
      criar("p", { texto: org.descricao }),
      contribuicoes.length ? criar("h4", { texto: "O que fazem pelo bairro" }) : null,
      contribuicoes.length ? criar("ul", {}, contribuicoes.map((c) => criar("li", { texto: c }))) : null,
      site
        ? criar("a", {
            classe: "botao botao-pequeno",
            href: site,
            target: "_blank",
            rel: "noopener noreferrer",
          }, "Visitar site", criar("span", { classe: "so-leitor", texto: " de " + org.nome + " (abre em nova aba)" }))
        : null,
    );
    return criar(
      "article",
      { classe: "org", id: opcoes.linkTitulo ? null : org.id },
      capa(org, indice),
      corpo,
    );
  }

  window.Mural.organizacoes = { lista, cartaoOrganizacao };
})();
