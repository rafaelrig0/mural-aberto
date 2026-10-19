/* Página inicial: carrossel com as obras mais recentes, votação e destaque das organizações. */
(function () {
  "use strict";
  const { api, criar, mostrarAviso, textoDoErro, midiaDaObra, carrossel, votos, organizacoes } = window.Mural;

  const QUANTIDADE_DESTAQUES = 5;

  /* ------------------------------------------------------------- Carrossel */

  function slideDaObra(obra) {
    const meta = ["por " + obra.author_name, obra.neighborhood ? "Bairro: " + obra.neighborhood : null].filter(Boolean);
    // Dois blocos (mídia e texto) que o CSS dispõe lado a lado no computador e empilhados no celular.
    return [
      criar("div", { classe: "slide-midia" }, midiaDaObra(obra, { trecho: "slide-trecho", video: "slide-video" })),
      criar(
        "div",
        { classe: "slide-corpo" },
        criar("span", { classe: "etiqueta", texto: obra.category.name }),
        criar("h3", { texto: obra.title }),
        criar("p", { classe: "meta", texto: meta.join(" · ") }),
        criar(
          "a",
          { classe: "botao botao-pequeno", href: "obra.html?id=" + encodeURIComponent(obra.id) },
          "Ver obra",
          criar("span", { classe: "so-leitor", texto: ": " + obra.title }),
        ),
      ),
    ];
  }

  /* -------------------------------------------------------------- Votação */

  function blocoDeVotacao(obras) {
    const mensagem = criar("p", { classe: "votacao-aviso", "aria-live": "polite" });
    const apresentacao = criar("p", {});
    const botaoRemover = criar("button", {
      type: "button",
      classe: "botao botao-secundario botao-pequeno",
      texto: "Remover meu voto",
      aoClicar: () => {
        votos.removerVoto();
        atualizar("Seu voto foi removido.");
      },
    });
    const opcoes = obras.map((obra) => {
      const numero = criar("span", { classe: "voto-numero" });
      const barra = criar("i", { classe: "voto-barra", "aria-hidden": "true" });
      const miniatura = criar("span", { classe: "voto-miniatura", "aria-hidden": "true" });
      if (obra.image_url) miniatura.append(criar("img", { src: obra.image_url, alt: "", loading: "lazy" }));
      else miniatura.textContent = obra.excerpt ? "“" : "▶";
      const botao = criar(
        "button",
        {
          type: "button",
          classe: "voto-opcao",
          "aria-pressed": "false",
          aoClicar: () => {
            if (votos.lerVoto() === obra.id) {
              votos.removerVoto();
              atualizar("Seu voto foi removido.");
            } else {
              votos.votar(obra.id);
              atualizar("Voto registrado em “" + obra.title + "”. Obrigado por participar!");
            }
          },
        },
        miniatura,
        criar(
          "span",
          {},
          criar("span", { classe: "voto-titulo", texto: obra.title }),
          criar("span", { classe: "voto-autor", texto: "por " + obra.author_name }),
        ),
        numero,
        barra,
      );
      return { obra, botao, numero, barra, item: criar("li", {}, botao) };
    });

    function atualizar(texto) {
      const meu = votos.lerVoto();
      const total = opcoes.reduce((soma, o) => soma + votos.contagem(o.obra.id), 0);
      for (const o of opcoes) {
        const n = votos.contagem(o.obra.id);
        const percentual = total ? Math.round((n / total) * 100) : 0;
        const escolhida = meu === o.obra.id;
        o.botao.setAttribute("aria-pressed", String(escolhida));
        o.botao.setAttribute(
          "aria-label",
          "Votar em " + o.obra.title + ", por " + o.obra.author_name + ". " + n + (n === 1 ? " voto, " : " votos, ") + percentual + "%.",
        );
        o.numero.textContent = percentual + "% · " + n + (escolhida ? " ✓" : "");
        o.barra.style.width = percentual + "%";
      }
      apresentacao.textContent = meu
        ? "Seu voto está registrado. Toque nele de novo para remover ou escolha outra obra para mudar."
        : "Escolha a sua obra favorita. Cada pessoa tem um voto.";
      botaoRemover.hidden = meu === null;
      if (texto !== undefined) mensagem.textContent = texto;
    }

    const raiz = criar(
      "section",
      { classe: "votacao", "aria-labelledby": "titulo-votacao" },
      criar("h3", { id: "titulo-votacao", texto: "Votação de obras" }),
      apresentacao,
      criar("ul", { classe: "votacao-opcoes" }, opcoes.map((o) => o.item)),
      criar("div", { classe: "grupo-botoes votacao-acoes" }, botaoRemover),
      criar("p", {
        classe: "votacao-aviso",
        texto: "Os votos ficam salvos apenas neste navegador: a contagem não é somada entre visitantes.",
      }),
      mensagem,
    );
    atualizar();
    return raiz;
  }

  /* -------------------------------------------------------------- Carregar */

  async function carregarObras() {
    const carregando = document.getElementById("carregando");
    const aviso = document.getElementById("aviso");
    const destaques = document.getElementById("destaques");
    try {
      const pagina = await api.get("/works?page=1&page_size=" + QUANTIDADE_DESTAQUES);
      if (pagina.items.length === 0) {
        destaques.replaceWith(
          criar(
            "div",
            { classe: "estado-vazio" },
            criar("p", { texto: "Ainda não há obras publicadas. Que tal enviar a primeira?" }),
            criar("a", { classe: "botao", href: "obras.html?enviar=1", texto: "+ Adicionar obra" }),
          ),
        );
        return;
      }
      document.getElementById("area-carrossel").append(carrossel("Obras em destaque", pagina.items.map(slideDaObra)));
      document.getElementById("area-votacao").append(blocoDeVotacao(pagina.items));
      destaques.hidden = false;
    } catch (erro) {
      mostrarAviso(aviso, "erro", " " + textoDoErro(erro));
    } finally {
      carregando.remove();
    }
  }

  /* ---------------------------------------------------------- Organizações */

  function mostrarOrganizacoes() {
    const grade = document.getElementById("lista-organizacoes");
    const lista = organizacoes.lista().slice(0, 3);
    if (lista.length === 0) {
      grade.replaceWith(criar("p", { classe: "estado-vazio", texto: "Em breve, as organizações parceiras aparecerão aqui." }));
      return;
    }
    lista.forEach((org, indice) => {
      grade.append(criar("li", {}, organizacoes.cartaoOrganizacao(org, indice, { linkTitulo: true })));
    });
  }

  mostrarOrganizacoes();
  carregarObras();
})();
