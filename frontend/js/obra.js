/* Detalhe de uma obra: conteúdo, comentários aprovados e formulário de comentário. */
(function () {
  "use strict";
  const {
    api, criar, limpar, mostrarAviso, textoDoErro, formatarData, definirErro, limparErros,
    focarPrimeiroErro, comBotaoOcupado, errosPorCampo, votos,
  } = window.Mural;

  const aviso = document.getElementById("aviso");
  const carregando = document.getElementById("carregando");
  const recipiente = document.getElementById("obra");
  const identificador = new URLSearchParams(location.search).get("id");

  function listaDeComentarios(comentarios) {
    if (comentarios.length === 0) {
      return criar("p", { classe: "meta", texto: "Ainda não há comentários. Seja a primeira pessoa a comentar." });
    }
    return criar(
      "ul",
      { classe: "comentarios" },
      comentarios.map((c) =>
        criar(
          "li",
          { classe: "comentario" },
          criar("strong", { texto: c.author_name }),
          " ",
          criar("span", { classe: "meta", texto: "em " + formatarData(c.created_at, true) }),
          criar("p", { texto: c.content }),
        ),
      ),
    );
  }

  function formularioDeComentario(idObra) {
    const resposta = criar("div", { id: "aviso-comentario", "aria-live": "polite" });
    const formulario = criar(
      "form",
      { classe: "formulario", novalidate: true },
      criar(
        "div",
        { classe: "campo" },
        criar("label", { for: "comentario-nome" }, "Seu nome ", criar("span", { classe: "obrigatorio", "aria-hidden": "true", texto: "*" })),
        criar("input", { id: "comentario-nome", name: "author_name", type: "text", maxlength: "120", autocomplete: "name", required: true, "aria-describedby": "erro-author_name" }),
        criar("span", { id: "erro-author_name", classe: "campo-erro" }),
      ),
      criar(
        "div",
        { classe: "campo" },
        criar("label", { for: "comentario-texto" }, "Comentário ", criar("span", { classe: "obrigatorio", "aria-hidden": "true", texto: "*" })),
        criar("textarea", { id: "comentario-texto", name: "content", rows: "4", maxlength: "2000", required: true, "aria-describedby": "erro-content" }),
        criar("span", { id: "erro-content", classe: "campo-erro" }),
      ),
      criar("button", { classe: "botao", type: "submit", texto: "Enviar comentário" }),
    );

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      limparErros(formulario);
      mostrarAviso(resposta, "info", "");
      const nome = formulario.elements.author_name.value.trim();
      const texto = formulario.elements.content.value.trim();
      if (!nome) definirErro(formulario, "author_name", "Informe o seu nome.");
      if (!texto) definirErro(formulario, "content", "Escreva o seu comentário.");
      if (!nome || !texto) return focarPrimeiroErro(formulario);

      const botao = formulario.querySelector("button[type=submit]");
      try {
        await comBotaoOcupado(botao, "Enviando…", () =>
          api.post("/works/" + encodeURIComponent(idObra) + "/comments", {
            json: { author_name: nome, content: texto },
          }),
        );
        formulario.reset();
        mostrarAviso(resposta, "sucesso", " Comentário enviado! Ele aparecerá aqui depois de ser aprovado pela equipe.");
      } catch (erro) {
        const porCampo = errosPorCampo(erro);
        Object.entries(porCampo).forEach(([campo, mensagem]) => definirErro(formulario, campo, mensagem));
        mostrarAviso(resposta, "erro", " " + textoDoErro(erro));
        focarPrimeiroErro(formulario);
      }
    });

    return criar("section", { "aria-labelledby": "titulo-comentar" }, criar("h2", { id: "titulo-comentar", texto: "Deixe um comentário" }), resposta, formulario);
  }

  /** Botão de voto. Os votos ficam só neste navegador (veja js/votos.js). */
  function blocoDeVoto(obra) {
    const texto = criar("p", {});
    const mensagem = criar("p", { classe: "meta", "aria-live": "polite" });
    const botao = criar("button", { type: "button", classe: "botao", "aria-pressed": "false", aoClicar: alternar });

    function atualizar(aviso) {
      const meu = votos.lerVoto();
      const votei = meu === obra.id;
      const n = votos.contagem(obra.id);
      botao.setAttribute("aria-pressed", String(votei));
      botao.textContent = votei ? "✓ Voto registrado (remover)" : meu === null ? "Votar nesta obra" : "Mudar meu voto para esta obra";
      texto.textContent = votei
        ? "Você votou nesta obra. Obrigado por participar!"
        : meu === null
          ? "Gostou? Vote nesta obra. Cada pessoa tem um voto."
          : "Você já votou em outra obra. Se votar aqui, o voto muda para esta.";
      mensagem.textContent =
        (aviso ? aviso + " " : "") + "Votos neste navegador: " + n + ". Os votos não são somados entre visitantes.";
    }

    function alternar() {
      if (votos.lerVoto() === obra.id) {
        votos.removerVoto();
        atualizar("Voto removido.");
      } else {
        votos.votar(obra.id);
        atualizar("Voto registrado.");
      }
    }

    atualizar();
    return criar("section", { classe: "votar-bloco", "aria-labelledby": "titulo-voto" },
      criar("h2", { id: "titulo-voto", texto: "Votação" }), texto, botao, mensagem);
  }

  function desenharObra(obra) {
    document.title = "Mural Aberto – " + obra.title;
    limpar(recipiente);

    const midia = criar("div", { classe: "obra-midia" });
    if (obra.image_url) {
      midia.append(criar("img", { src: obra.image_url, alt: obra.alt_text || "Imagem da obra " + obra.title }));
    }
    if (obra.video_url) {
      midia.append(
        criar("video", { src: obra.video_url, controls: true, preload: "metadata" },
          "Seu navegador não consegue reproduzir este vídeo."),
      );
    }

    recipiente.append(
      criar("h1", { texto: obra.title }),
      criar(
        "div",
        { classe: "dados" },
        criar("span", { texto: "por " + obra.author_name }),
        criar("span", { classe: "etiqueta", texto: obra.category.name }),
        criar("span", { texto: "Criada em " + formatarData(obra.created_on) }),
        obra.neighborhood ? criar("span", { texto: "Bairro: " + obra.neighborhood }) : null,
      ),
      midia.childNodes.length ? midia : null,
      obra.body_text ? criar("div", { classe: "obra-texto", texto: obra.body_text }) : null,
      blocoDeVoto(obra),
      criar("hr"),
      criar("h2", { texto: "Comentários" }),
      listaDeComentarios(obra.comments),
      formularioDeComentario(obra.id),
    );
    recipiente.hidden = false;
  }

  async function carregar() {
    if (!/^\d+$/.test(identificador || "")) {
      carregando.remove();
      return mostrarAviso(aviso, "erro", " Obra não encontrada. Volte para a lista e escolha uma obra.");
    }
    try {
      desenharObra(await api.get("/works/" + identificador));
    } catch (erro) {
      const naoEncontrada = erro.status === 404 || erro.status === 422;
      mostrarAviso(aviso, "erro", " " + (naoEncontrada ? "Obra não encontrada ou ainda não publicada." : textoDoErro(erro)));
    } finally {
      carregando.remove();
    }
  }

  carregar();
})();
