/* Painel do administrador: login, moderação de obras e comentários, feedbacks, categorias e histórico. */
(function () {
  "use strict";
  const {
    api, criar, limpar, consulta, obterToken, salvarToken, limparToken, textoDoErro,
    errosPorCampo, definirErro, limparErros, focarPrimeiroErro, mostrarAviso, comBotaoOcupado,
    formatarData, estrelas, paginacao, TIPOS_FEEDBACK, STATUS_OBRA, STATUS_COMENTARIO,
  } = window.Mural;

  const TAMANHO = 10;
  const admin = { admin: true };

  const areaLogin = document.getElementById("area-login");
  const areaPainel = document.getElementById("area-painel");
  const avisoGeral = document.getElementById("aviso");
  const avisoPainel = document.getElementById("aviso-painel");
  const conteudo = document.getElementById("conteudo");

  const ABAS = [
    { id: "obras", rotulo: "Obras", desenhar: abaObras },
    { id: "comentarios", rotulo: "Comentários", desenhar: abaComentarios },
    { id: "feedback", rotulo: "Feedback", desenhar: abaFeedback },
    { id: "categorias", rotulo: "Categorias", desenhar: abaCategorias },
    { id: "historico", rotulo: "Histórico", desenhar: abaHistorico },
  ];

  /* ------------------------------------------------------------ diálogo */

  const dialogo = document.getElementById("dialogo");
  const dialogoForm = document.getElementById("dialogo-form");

  /**
   * Abre o diálogo e devolve uma promessa com { confirmado, valor }.
   * opcoes.campo = { rotulo, valorInicial, obrigatorio, minimo, multilinha } para pedir um texto.
   */
  function perguntar(opcoes) {
    document.getElementById("dialogo-titulo").textContent = opcoes.titulo;
    document.getElementById("dialogo-texto").textContent = opcoes.texto || "";
    const blocoCampo = document.getElementById("dialogo-campo");
    const entrada = document.getElementById("dialogo-entrada");
    const area = document.getElementById("dialogo-area");
    const erro = document.getElementById("dialogo-erro");
    const confirmar = document.getElementById("dialogo-confirmar");

    erro.textContent = "";
    confirmar.textContent = opcoes.confirmar || "Confirmar";
    confirmar.className = "botao" + (opcoes.perigo ? " botao-perigo" : "");

    const campo = opcoes.campo;
    blocoCampo.hidden = !campo;
    let controle = entrada;
    if (campo) {
      controle = campo.multilinha ? area : entrada;
      entrada.hidden = Boolean(campo.multilinha);
      area.hidden = !campo.multilinha;
      document.getElementById("dialogo-rotulo").setAttribute("for", controle.id);
      document.getElementById("dialogo-rotulo").textContent = campo.rotulo;
      controle.value = campo.valorInicial || "";
    }

    return new Promise((resolver) => {
      function finalizar(confirmado) {
        dialogo.removeEventListener("close", aoFechar);
        dialogoForm.removeEventListener("submit", aoEnviar);
        document.getElementById("dialogo-cancelar").removeEventListener("click", aoCancelar);
        if (dialogo.open) dialogo.close();
        resolver({ confirmado, valor: campo ? controle.value.trim() : "" });
      }
      function aoEnviar(evento) {
        evento.preventDefault();
        if (campo) {
          const valor = controle.value.trim();
          if (campo.obrigatorio && valor.length < (campo.minimo || 1)) {
            erro.textContent = campo.minimo > 1 ? "Escreva pelo menos " + campo.minimo + " caracteres." : "Preencha este campo.";
            return controle.focus();
          }
        }
        finalizar(true);
      }
      const aoCancelar = () => finalizar(false);
      const aoFechar = () => finalizar(false);
      dialogoForm.addEventListener("submit", aoEnviar);
      document.getElementById("dialogo-cancelar").addEventListener("click", aoCancelar);
      dialogo.addEventListener("close", aoFechar);
      dialogo.showModal();
      (campo ? controle : document.getElementById("dialogo-cancelar")).focus();
    });
  }

  /* ------------------------------------------------------------ sessão */

  function mostrarLogin(mensagem) {
    areaPainel.hidden = true;
    areaLogin.hidden = false;
    limpar(conteudo);
    if (mensagem) mostrarAviso(avisoGeral, "info", " " + mensagem);
  }

  async function mostrarPainel() {
    try {
      const eu = await api.get("/auth/me", admin);
      document.getElementById("usuario").textContent = "Conectado como " + eu.email;
    } catch (erro) {
      if (erro.status === 401) return mostrarLogin();
      return mostrarAviso(avisoGeral, "erro", " " + textoDoErro(erro));
    }
    areaLogin.hidden = true;
    areaPainel.hidden = false;
    mostrarAviso(avisoGeral, "info", "");
    desenharAbas();
    abrirAbaDaUrl();
  }

  document.addEventListener("mural:sessao-expirada", () => mostrarLogin("Sua sessão expirou. Entre novamente."));

  document.getElementById("form-login").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    limparErros(formulario);
    mostrarAviso(avisoGeral, "info", "");
    const email = formulario.elements.email.value.trim();
    const senha = formulario.elements.password.value;
    if (!email) definirErro(formulario, "email", "Informe o seu e-mail.");
    if (!senha) definirErro(formulario, "password", "Informe a sua senha.");
    if (!email || !senha) return focarPrimeiroErro(formulario);

    try {
      const resposta = await comBotaoOcupado(formulario.querySelector("button"), "Entrando…", () =>
        api.post("/auth/login", { json: { email, password: senha } }),
      );
      salvarToken(resposta.access_token);
      formulario.reset();
      await mostrarPainel();
    } catch (erro) {
      const porCampo = errosPorCampo(erro);
      Object.entries(porCampo).forEach(([campo, texto]) => definirErro(formulario, campo, texto));
      mostrarAviso(avisoGeral, "erro", " " + textoDoErro(erro));
    }
  });

  document.getElementById("sair").addEventListener("click", () => {
    limparToken();
    mostrarLogin("Você saiu do painel.");
  });

  /* -------------------------------------------------------------- abas */

  function desenharAbas() {
    const nav = limpar(document.getElementById("abas"));
    ABAS.forEach((aba) => nav.append(criar("a", { href: "#" + aba.id, "data-aba": aba.id, texto: aba.rotulo })));
  }

  function abrirAbaDaUrl() {
    const id = location.hash.slice(1);
    const aba = ABAS.find((a) => a.id === id) || ABAS[0];
    document.querySelectorAll("#abas a").forEach((link) => {
      if (link.dataset.aba === aba.id) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    mostrarAviso(avisoPainel, "info", "");
    limpar(conteudo);
    aba.desenhar();
  }

  window.addEventListener("hashchange", () => {
    if (!areaPainel.hidden) abrirAbaDaUrl();
  });

  /* ------------------------------------------------------- utilitários */

  function selecao(rotulo, nome, opcoes, valorInicial, aoMudar) {
    const select = criar("select", { id: "filtro-" + nome, name: nome, aoMudar });
    opcoes.forEach(([valor, texto]) => select.append(criar("option", { value: valor, texto })));
    select.value = valorInicial;
    return criar("div", { classe: "campo" }, criar("label", { for: "filtro-" + nome, texto: rotulo }), select);
  }

  const CLASSE_STATUS = { pending: "pendente", approved: "aprovada", rejected: "rejeitada", archived: "arquivada" };

  function etiquetaStatus(status, tabela) {
    return criar("span", { classe: "etiqueta etiqueta-" + CLASSE_STATUS[status], texto: tabela[status] });
  }

  /** Esqueleto comum das abas com filtros + lista + paginação. */
  function abaComLista({ filtros, buscar, desenharItem, vazio }) {
    const barra = criar("div", { classe: "filtros" }, filtros.nos);
    const lista = criar("ul", { classe: "lista" });
    const resumo = criar("p", { classe: "meta", "aria-live": "polite" });
    const rodape = criar("div");
    conteudo.append(barra, resumo, lista, rodape);

    let pagina = 1;
    async function carregar() {
      lista.setAttribute("aria-busy", "true");
      try {
        const resultado = await buscar(pagina, filtros.valores());
        limpar(lista);
        limpar(rodape);
        resumo.textContent = resultado.total === 1 ? "1 registro." : resultado.total + " registros.";
        if (resultado.items.length === 0) {
          lista.append(criar("li", { classe: "estado-vazio", texto: vazio }));
        }
        resultado.items.forEach((item) => lista.append(criar("li", { classe: "item" }, desenharItem(item, recarregar))));
        rodape.append(paginacao(resultado.page, resultado.page_size, resultado.total, { aoIr: (n) => { pagina = n; carregar(); } }));
      } catch (erro) {
        if (erro.status !== 401) mostrarAviso(avisoPainel, "erro", " " + textoDoErro(erro));
      } finally {
        lista.removeAttribute("aria-busy");
      }
    }
    function recarregar(mensagem) {
      if (mensagem) mostrarAviso(avisoPainel, "sucesso", " " + mensagem);
      return carregar();
    }
    filtros.aoMudar(() => { pagina = 1; carregar(); });
    carregar();
  }

  /** Executa uma ação do painel e mostra o resultado. */
  async function executar(botao, textoOcupado, tarefa, mensagemSucesso, recarregar) {
    try {
      await comBotaoOcupado(botao, textoOcupado, tarefa);
      await recarregar(mensagemSucesso);
    } catch (erro) {
      if (erro.status !== 401) mostrarAviso(avisoPainel, "erro", " " + textoDoErro(erro));
    }
  }

  /**
   * O navegador zera event.currentTarget depois do primeiro "await"; por isso o botão é entregue
   * ao tratador já guardado em { currentTarget }, e continua válido depois de abrir o diálogo.
   */
  function botao(texto, classe, aoClicar) {
    const no = criar("button", { type: "button", classe: "botao botao-pequeno " + classe, texto });
    no.addEventListener("click", () => aoClicar({ currentTarget: no }));
    return no;
  }

  /* -------------------------------------------------------------- obras */

  function abaObras() {
    const status = selecao("Situação", "status", [["pending", "Pendentes"], ["approved", "Aprovadas"], ["rejected", "Rejeitadas"], ["archived", "Arquivadas"], ["", "Todas"]], "pending");
    const ordem = selecao("Ordem", "ordem", [["newest", "Mais recentes primeiro"], ["oldest", "Mais antigas primeiro"]], "newest");
    abaComLista({
      filtros: {
        nos: [status, ordem],
        valores: () => ({ status: status.querySelector("select").value, order: ordem.querySelector("select").value }),
        aoMudar: (f) => [status, ordem].forEach((n) => n.querySelector("select").addEventListener("change", f)),
      },
      buscar: (pagina, v) => api.get("/admin/works" + consulta({ ...v, page: pagina, page_size: TAMANHO }), admin),
      desenharItem: cartaoObraAdmin,
      vazio: "Nenhuma obra nesta situação.",
    });
  }

  function cartaoObraAdmin(obra, recarregar) {
    const acoes = criar("div", { classe: "item-acoes" });
    const rotaAcao = (acao, texto, classe, ocupado, sucesso, corpo) =>
      botao(texto, classe, (e) =>
        executar(e.currentTarget, ocupado, () => api.post("/admin/works/" + obra.id + "/" + acao, { ...admin, json: corpo }), sucesso, recarregar));

    if (obra.status === "pending") {
      acoes.append(rotaAcao("approve", "Aprovar", "", "Aprovando…", "Obra aprovada e publicada."));
      acoes.append(botao("Rejeitar", "botao-perigo", async (e) => {
        const r = await perguntar({ titulo: "Rejeitar obra", texto: "A rejeição é definitiva. Informe o motivo (fica no histórico; não escreva dados pessoais).", confirmar: "Rejeitar", perigo: true, campo: { rotulo: "Motivo", obrigatorio: true, minimo: 3, multilinha: true } });
        if (r.confirmado) await executar(e.currentTarget, "Rejeitando…", () => api.post("/admin/works/" + obra.id + "/reject", { ...admin, json: { reason: r.valor } }), "Obra rejeitada.", recarregar);
      }));
    }
    if (obra.status === "approved") acoes.append(rotaAcao("archive", "Arquivar", "botao-secundario", "Arquivando…", "Obra arquivada (saiu do site)."));
    if (obra.status === "archived") acoes.append(rotaAcao("unarchive", "Reativar", "", "Reativando…", "Obra reativada e publicada novamente."));
    acoes.append(botao("Excluir", "botao-perigo", async (e) => {
      const r = await perguntar({ titulo: "Excluir obra", texto: 'Excluir "' + obra.title + '" definitivamente? Os arquivos e os comentários também serão apagados. Não dá para desfazer.', confirmar: "Excluir", perigo: true });
      if (r.confirmado) await executar(e.currentTarget, "Excluindo…", () => api.excluir("/admin/works/" + obra.id, admin), "Obra excluída.", recarregar);
    }));

    const midia = [];
    if (obra.image_url) midia.push(criar("img", { classe: "item-miniatura", src: obra.image_url, alt: obra.alt_text || "Imagem enviada com a obra", loading: "lazy" }));
    if (obra.video_url) midia.push(criar("video", { classe: "item-miniatura", src: obra.video_url, controls: true, preload: "none" }));

    return [
      criar("div", { classe: "item-topo" }, criar("h3", { texto: obra.title }), etiquetaStatus(obra.status, STATUS_OBRA)),
      criar("p", { classe: "meta", texto: "por " + obra.author_name + " · " + obra.category.name }),
      criar("p", { classe: "meta", texto: "Contato: " + obra.contact_email + " · Criada em " + formatarData(obra.created_on) + (obra.neighborhood ? " · Bairro: " + obra.neighborhood : "") }),
      criar("p", { classe: "meta", texto: "Enviada em " + formatarData(obra.created_at, true) + " · Autorização de uso em " + formatarData(obra.usage_authorized_at, true) }),
      ...midia,
      obra.body_text ? criar("details", {}, criar("summary", { texto: "Ler o texto da obra" }), criar("p", { classe: "item-texto", texto: obra.body_text })) : null,
      obra.rejection_reason ? criar("p", { classe: "item-texto", texto: "Motivo da rejeição: " + obra.rejection_reason }) : null,
      acoes,
    ];
  }

  /* -------------------------------------------------------- comentários */

  function abaComentarios() {
    const status = selecao("Situação", "status", [["pending", "Pendentes"], ["approved", "Aprovados"], ["rejected", "Rejeitados"], ["", "Todos"]], "pending");
    const ordem = selecao("Ordem", "ordem", [["newest", "Mais recentes primeiro"], ["oldest", "Mais antigos primeiro"]], "newest");
    const obra = criar("div", { classe: "campo" }, criar("label", { for: "filtro-obra", texto: "Número da obra (opcional)" }), criar("input", { id: "filtro-obra", type: "number", min: "1", inputmode: "numeric" }));
    abaComLista({
      filtros: {
        nos: [status, ordem, obra],
        valores: () => ({ status: status.querySelector("select").value, order: ordem.querySelector("select").value, work_id: obra.querySelector("input").value }),
        aoMudar: (f) => { [status, ordem].forEach((n) => n.querySelector("select").addEventListener("change", f)); obra.querySelector("input").addEventListener("change", f); },
      },
      buscar: (pagina, v) => api.get("/admin/comments" + consulta({ ...v, page: pagina, page_size: TAMANHO }), admin),
      desenharItem: cartaoComentario,
      vazio: "Nenhum comentário nesta situação.",
    });
  }

  function cartaoComentario(comentario, recarregar) {
    const acoes = criar("div", { classe: "item-acoes" });
    if (comentario.status === "pending") {
      acoes.append(botao("Aprovar", "", (e) => executar(e.currentTarget, "Aprovando…", () => api.post("/admin/comments/" + comentario.id + "/approve", admin), "Comentário aprovado.", recarregar)));
      acoes.append(botao("Rejeitar", "botao-perigo", async (e) => {
        const r = await perguntar({ titulo: "Rejeitar comentário", texto: "O motivo é opcional.", confirmar: "Rejeitar", perigo: true, campo: { rotulo: "Motivo (opcional)", obrigatorio: false, multilinha: true } });
        if (r.confirmado) await executar(e.currentTarget, "Rejeitando…", () => api.post("/admin/comments/" + comentario.id + "/reject", { ...admin, json: { reason: r.valor || null } }), "Comentário rejeitado.", recarregar);
      }));
    }
    acoes.append(botao("Excluir", "botao-perigo", async (e) => {
      const r = await perguntar({ titulo: "Excluir comentário", texto: "Excluir este comentário definitivamente? Não dá para desfazer.", confirmar: "Excluir", perigo: true });
      if (r.confirmado) await executar(e.currentTarget, "Excluindo…", () => api.excluir("/admin/comments/" + comentario.id, admin), "Comentário excluído.", recarregar);
    }));
    return [
      criar("div", { classe: "item-topo" }, criar("h3", { texto: comentario.author_name }), etiquetaStatus(comentario.status, STATUS_COMENTARIO)),
      criar("p", { classe: "meta", texto: "Obra nº " + comentario.work_id + " · " + formatarData(comentario.created_at, true) }),
      criar("p", { classe: "item-texto", texto: comentario.content }),
      comentario.rejection_reason ? criar("p", { classe: "meta", texto: "Motivo da rejeição: " + comentario.rejection_reason }) : null,
      acoes,
    ];
  }

  /* ----------------------------------------------------------- feedback */

  function abaFeedback() {
    const tipo = selecao("Tipo", "tipo", [["", "Todos"], ...Object.entries(TIPOS_FEEDBACK)], "");
    const ordem = selecao("Ordem", "ordem", [["newest", "Mais recentes primeiro"], ["oldest", "Mais antigos primeiro"]], "newest");
    abaComLista({
      filtros: {
        nos: [tipo, ordem],
        valores: () => ({ feedback_type: tipo.querySelector("select").value, order: ordem.querySelector("select").value }),
        aoMudar: (f) => [tipo, ordem].forEach((n) => n.querySelector("select").addEventListener("change", f)),
      },
      buscar: (pagina, v) => api.get("/admin/feedback" + consulta({ ...v, page: pagina, page_size: TAMANHO }), admin),
      desenharItem: (f) => [
        criar("div", { classe: "item-topo" }, criar("h3", { texto: f.author_name || "Anônimo" }), criar("span", { classe: "etiqueta", texto: TIPOS_FEEDBACK[f.feedback_type] })),
        criar("p", { classe: "meta" }, estrelas(f.rating), " · " + formatarData(f.created_at, true)),
        criar("p", { classe: "item-texto", texto: f.message }),
      ],
      vazio: "Nenhum feedback recebido ainda.",
    });
  }

  /* --------------------------------------------------------- categorias */

  async function abaCategorias() {
    const aviso = criar("div", { "aria-live": "polite" });
    const campo = criar("input", { id: "nova-categoria", name: "name", type: "text", maxlength: "80" });
    const erroCampo = criar("span", { classe: "campo-erro" });
    const formulario = criar("form", { classe: "linha-inline", novalidate: true },
      criar("div", { classe: "campo" }, criar("label", { for: "nova-categoria", texto: "Nova categoria" }), campo, erroCampo),
      criar("button", { classe: "botao", type: "submit", texto: "Adicionar" }));
    const lista = criar("ul", { classe: "lista" });
    conteudo.append(formulario, aviso, lista);

    async function carregar(mensagem) {
      try {
        const categorias = await api.get("/categories");
        limpar(lista);
        if (mensagem) mostrarAviso(avisoPainel, "sucesso", " " + mensagem);
        categorias.forEach((c) => lista.append(criar("li", { classe: "item" },
          criar("div", { classe: "item-topo" }, criar("h3", { texto: c.name }), criar("span", { classe: "meta", texto: "endereço: " + c.slug })),
          criar("div", { classe: "item-acoes" },
            botao("Renomear", "botao-secundario", async (e) => {
              const r = await perguntar({ titulo: "Renomear categoria", confirmar: "Salvar", campo: { rotulo: "Novo nome", valorInicial: c.name, obrigatorio: true, minimo: 2 } });
              if (r.confirmado) await executar(e.currentTarget, "Salvando…", () => api.put("/admin/categories/" + c.id, { ...admin, json: { name: r.valor } }), "Categoria renomeada.", carregar);
            }),
            botao("Excluir", "botao-perigo", async (e) => {
              const r = await perguntar({ titulo: "Excluir categoria", texto: 'Excluir a categoria "' + c.name + '"? Categorias que têm obras não podem ser excluídas.', confirmar: "Excluir", perigo: true });
              if (r.confirmado) await executar(e.currentTarget, "Excluindo…", () => api.excluir("/admin/categories/" + c.id, admin), "Categoria excluída.", carregar);
            })))));
      } catch (erro) {
        if (erro.status !== 401) mostrarAviso(avisoPainel, "erro", " " + textoDoErro(erro));
      }
    }

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      limparErros(formulario);
      const nome = campo.value.trim();
      if (nome.length < 2) {
        campo.setAttribute("aria-invalid", "true");
        erroCampo.textContent = "Escreva um nome com pelo menos 2 caracteres.";
        return campo.focus();
      }
      await executar(formulario.querySelector("button"), "Adicionando…", () => api.post("/admin/categories", { ...admin, json: { name: nome } }), "Categoria criada.", async (m) => { campo.value = ""; await carregar(m); });
    });
    carregar();
  }

  /* ---------------------------------------------------------- histórico */

  const ROTULO_ACAO = { approve: "Aprovou", reject: "Rejeitou", archive: "Arquivou", unarchive: "Reativou", delete: "Excluiu" };
  const ROTULO_ALVO = { work: "Obra", comment: "Comentário" };

  function abaHistorico() {
    const alvo = selecao("Alvo", "alvo", [["", "Todos"], ["work", "Obras"], ["comment", "Comentários"]], "");
    const acao = selecao("Ação", "acao", [["", "Todas"], ...Object.entries(ROTULO_ACAO)], "");
    const resumo = criar("p", { classe: "meta", "aria-live": "polite" });
    const tabelaBox = criar("div");
    const rodape = criar("div");
    conteudo.append(criar("div", { classe: "filtros" }, alvo, acao), resumo, tabelaBox, rodape);

    let pagina = 1;
    async function carregar() {
      try {
        const v = { target_type: alvo.querySelector("select").value, action: acao.querySelector("select").value };
        const r = await api.get("/admin/moderation-logs" + consulta({ ...v, page: pagina, page_size: 20 }), admin);
        limpar(tabelaBox);
        limpar(rodape);
        resumo.textContent = r.total === 1 ? "1 registro." : r.total + " registros.";
        if (r.items.length === 0) {
          tabelaBox.append(criar("p", { classe: "estado-vazio", texto: "Nenhum registro encontrado." }));
          return;
        }
        tabelaBox.append(criar("div", { classe: "tabela-rolagem", role: "region", tabindex: "0", "aria-label": "Histórico de moderação" },
          criar("table", {},
            criar("thead", {}, criar("tr", {}, ["Data", "Administrador", "Ação", "Alvo", "Motivo"].map((t) => criar("th", { scope: "col", texto: t })))),
            criar("tbody", {}, r.items.map((l) => criar("tr", {},
              criar("td", { texto: formatarData(l.created_at, true) }),
              criar("td", { texto: l.admin_email }),
              criar("td", { texto: ROTULO_ACAO[l.action] }),
              criar("td", { texto: ROTULO_ALVO[l.target_type] + " nº " + l.target_id }),
              criar("td", { texto: l.reason || "—" })))))));
        rodape.append(paginacao(r.page, r.page_size, r.total, { aoIr: (n) => { pagina = n; carregar(); } }));
      } catch (erro) {
        if (erro.status !== 401) mostrarAviso(avisoPainel, "erro", " " + textoDoErro(erro));
      }
    }
    [alvo, acao].forEach((n) => n.querySelector("select").addEventListener("change", () => { pagina = 1; carregar(); }));
    carregar();
  }

  /* ------------------------------------------------------------- início */

  if (obterToken()) mostrarPainel();
  else mostrarLogin();
})();
