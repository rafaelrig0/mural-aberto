/* Página Obras: galeria com busca, filtro e paginação (estado na URL) e janela (modal) de envio de obra. */
(function () {
  "use strict";
  const {
    config, api, criar, limpar, consulta, mostrarAviso, textoDoErro, cartaoObra, paginacao, numeroDaConsulta,
    definirErro, limparErros, focarPrimeiroErro, comBotaoOcupado, errosPorCampo, tipoDaCategoria,
  } = window.Mural;

  /* ====================================================================== Galeria */

  const TAMANHO_PAGINA = 12;
  const parametros = new URLSearchParams(location.search);
  const filtros = {
    q: (parametros.get("q") || "").slice(0, 100),
    category_id: /^\d+$/.test(parametros.get("category_id") || "") ? parametros.get("category_id") : "",
  };
  const pagina = numeroDaConsulta(parametros, "page", 1);

  const formularioFiltros = document.getElementById("filtros");
  const aviso = document.getElementById("aviso");
  const resumo = document.getElementById("resumo");
  const carregando = document.getElementById("carregando");
  const lista = document.getElementById("lista-obras");

  const categoriasPorId = new Map();
  let categoriasCarregadas = null; // promessa: o modal também espera por ela

  function carregarCategorias() {
    const filtro = document.getElementById("filtro-categoria");
    const escolha = document.getElementById("categoria");
    return api
      .get("/categories")
      .then((categorias) => {
        categorias.forEach((c) => {
          categoriasPorId.set(String(c.id), c);
          filtro.append(criar("option", { value: c.id, texto: c.name }));
          escolha.append(criar("option", { value: c.id, texto: c.name }));
        });
        filtro.value = filtros.category_id;
        return true;
      })
      .catch((erro) => {
        // O filtro some, mas a galeria continua. No modal, o aviso aparece ao abrir.
        categoriasPorId.clear();
        return erro;
      });
  }

  function enderecoDaPagina(numero) {
    return "obras.html" + consulta({ ...filtros, page: numero > 1 ? numero : "" });
  }

  async function carregarObras() {
    try {
      const resultado = await api.get("/works" + consulta({ ...filtros, page: pagina, page_size: TAMANHO_PAGINA }));
      limpar(lista);
      const total = resultado.total;
      resumo.textContent = total === 1 ? "1 obra encontrada." : total + " obras encontradas.";

      if (resultado.items.length === 0) {
        lista.replaceWith(
          criar(
            "div",
            { classe: "estado-vazio" },
            criar("p", { texto: filtros.q || filtros.category_id ? "Nenhuma obra encontrada para esta busca." : "Ainda não há obras publicadas. Seja a primeira pessoa a enviar!" }),
            filtros.q || filtros.category_id ? criar("a", { href: "obras.html", texto: "Limpar filtros" }) : null,
          ),
        );
        return;
      }
      resultado.items.forEach((obra) => lista.append(cartaoObra(obra)));
      document
        .getElementById("paginacao")
        .append(paginacao(resultado.page, resultado.page_size, total, { href: enderecoDaPagina }));
    } catch (erro) {
      mostrarAviso(aviso, "erro", " " + textoDoErro(erro));
    } finally {
      carregando.remove();
    }
  }

  /* ================================================================= Modal de envio */

  const modal = document.getElementById("modal-obra");
  const formulario = document.getElementById("formulario");
  const avisoModal = document.getElementById("aviso-modal");
  const confirmacao = document.getElementById("modal-confirmacao");
  const blocoTexto = document.getElementById("bloco-texto");
  const blocoVisual = document.getElementById("bloco-visual");
  const erroArquivos = document.getElementById("erro-arquivos");
  const botaoAbrir = document.getElementById("abrir-modal");
  const campoData = document.getElementById("data");

  const TIPOS_IMAGEM = ["image/jpeg", "image/png", "image/webp"];
  const TIPOS_VIDEO = ["video/mp4", "video/webm"];
  const MB = 1024 * 1024;

  document.getElementById("dica-imagem").textContent = "Tamanho máximo: " + config.MAX_IMAGEM_MB + " MB.";
  document.getElementById("dica-video").textContent = "Tamanho máximo: " + config.MAX_VIDEO_MB + " MB.";

  function definirDataMaxima() {
    const hoje = new Date();
    campoData.max = [hoje.getFullYear(), String(hoje.getMonth() + 1).padStart(2, "0"), String(hoje.getDate()).padStart(2, "0")].join("-");
  }

  /** O servidor pede "categoria" e "tipo"; aqui a pessoa escolhe só a categoria e o tipo é deduzido dela. */
  function tipoEscolhido() {
    return tipoDaCategoria(categoriasPorId.get(formulario.elements.category_id.value));
  }

  function atualizarTipo() {
    const texto = tipoEscolhido() === "text";
    blocoTexto.hidden = !texto;
    blocoVisual.hidden = texto;
    formulario.elements.body_text.required = texto;
  }

  function validar() {
    const f = formulario.elements;
    const obrigatorio = (nome, mensagem) => {
      if (!f[nome].value.trim()) definirErro(formulario, nome, mensagem);
    };

    obrigatorio("title", "Informe o título da obra.");
    obrigatorio("author_name", "Informe o seu nome.");
    if (!f.contact_email.value.trim()) definirErro(formulario, "contact_email", "Informe o seu e-mail.");
    else if (!f.contact_email.validity.valid) definirErro(formulario, "contact_email", "Digite um e-mail válido, como nome@exemplo.com.");
    if (!f.category_id.value) definirErro(formulario, "category_id", "Escolha uma categoria.");
    if (!f.created_on.value) definirErro(formulario, "created_on", "Informe a data de criação.");
    else if (f.created_on.value > campoData.max) definirErro(formulario, "created_on", "A data não pode ser no futuro.");

    // O que se exige da obra depende da categoria; sem categoria escolhida ainda não dá para saber.
    if (f.category_id.value) {
      if (tipoEscolhido() === "text") {
        obrigatorio("body_text", "Escreva o texto da obra.");
      } else {
        const imagem = f.image.files[0];
        const video = f.video.files[0];
        if (!imagem && !video) erroArquivos.textContent = "Envie uma imagem ou um vídeo.";
        if (imagem) {
          if (!TIPOS_IMAGEM.includes(imagem.type)) definirErro(formulario, "image", "Use uma imagem JPEG, PNG ou WebP.");
          else if (imagem.size > config.MAX_IMAGEM_MB * MB) definirErro(formulario, "image", "A imagem passa de " + config.MAX_IMAGEM_MB + " MB.");
          if (!f.alt_text.value.trim()) definirErro(formulario, "alt_text", "Descreva a imagem para quem não consegue vê-la.");
        }
        if (video) {
          if (!TIPOS_VIDEO.includes(video.type)) definirErro(formulario, "video", "Use um vídeo MP4 ou WebM.");
          else if (video.size > config.MAX_VIDEO_MB * MB) definirErro(formulario, "video", "O vídeo passa de " + config.MAX_VIDEO_MB + " MB.");
        }
      }
    }
    if (!f.usage_authorized.checked) definirErro(formulario, "usage_authorized", "É preciso autorizar a divulgação para enviar a obra.");

    return !formulario.querySelector('[aria-invalid="true"]') && !erroArquivos.textContent;
  }

  function montarEnvio() {
    const f = formulario.elements;
    const tipo = tipoEscolhido();
    const dados = new FormData();
    dados.set("title", f.title.value.trim());
    dados.set("author_name", f.author_name.value.trim());
    dados.set("contact_email", f.contact_email.value.trim());
    dados.set("category_id", f.category_id.value);
    dados.set("work_type", tipo);
    dados.set("created_on", f.created_on.value);
    dados.set("usage_authorized", "true");
    if (f.neighborhood.value.trim()) dados.set("neighborhood", f.neighborhood.value.trim());
    if (tipo === "text") {
      dados.set("body_text", f.body_text.value.trim());
    } else {
      if (f.alt_text.value.trim()) dados.set("alt_text", f.alt_text.value.trim());
      if (f.image.files[0]) dados.set("image", f.image.files[0]);
      if (f.video.files[0]) dados.set("video", f.video.files[0]);
    }
    return dados;
  }

  function reiniciarFormulario() {
    formulario.reset();
    limparErros(formulario);
    erroArquivos.textContent = "";
    mostrarAviso(avisoModal, "info", "");
    avisoModal.className = "";
    confirmacao.hidden = true;
    formulario.hidden = false;
    definirDataMaxima();
    atualizarTipo();
  }

  async function abrirModal() {
    reiniciarFormulario();
    if (typeof modal.showModal === "function") modal.showModal();
    else modal.setAttribute("open", "");
    formulario.elements.title.focus();

    // As categorias vêm da API; se ainda não chegaram (ou falharam), o aviso aparece aqui dentro.
    const resultado = await categoriasCarregadas;
    if (resultado !== true) {
      mostrarAviso(avisoModal, "erro", " Não foi possível carregar as categorias. " + textoDoErro(resultado));
    }
  }

  function fecharModal() {
    if (typeof modal.close === "function") modal.close();
    else modal.removeAttribute("open");
  }

  modal.addEventListener("close", () => {
    reiniciarFormulario();
    botaoAbrir.focus();
  });

  botaoAbrir.addEventListener("click", abrirModal);
  document.getElementById("modal-fechar-x").addEventListener("click", fecharModal);
  document.getElementById("modal-cancelar").addEventListener("click", fecharModal);
  document.getElementById("modal-fechar-ok").addEventListener("click", fecharModal);
  formulario.elements.category_id.addEventListener("change", atualizarTipo);

  document.getElementById("enviar-outra").addEventListener("click", () => {
    reiniciarFormulario();
    formulario.elements.title.focus();
  });

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(formulario);
    erroArquivos.textContent = "";
    mostrarAviso(avisoModal, "info", "");

    if (!validar()) {
      mostrarAviso(avisoModal, "erro", " Há campos para corrigir. Eles estão marcados abaixo.");
      focarPrimeiroErro(formulario);
      return;
    }

    try {
      await comBotaoOcupado(document.getElementById("enviar"), "Enviando…", () =>
        api.post("/works", { formulario: montarEnvio() }),
      );
      formulario.hidden = true;
      avisoModal.className = "";
      confirmacao.hidden = false;
      document.getElementById("titulo-confirmacao").focus();
    } catch (erro) {
      Object.entries(errosPorCampo(erro)).forEach(([campo, mensagem]) => definirErro(formulario, campo, mensagem));
      mostrarAviso(avisoModal, "erro", " " + textoDoErro(erro));
      focarPrimeiroErro(formulario);
      avisoModal.scrollIntoView({ block: "nearest" });
    }
  });

  /* ====================================================================== Início */

  formularioFiltros.elements.q.value = filtros.q;
  categoriasCarregadas = carregarCategorias();
  carregarObras();
  definirDataMaxima();
  atualizarTipo();

  // Links como "Adicionar obra" da página inicial chegam com ?enviar=1: abre o modal e limpa o endereço.
  if (parametros.get("enviar") === "1") {
    parametros.delete("enviar");
    const resto = parametros.toString();
    history.replaceState(null, "", location.pathname + (resto ? "?" + resto : "") + location.hash);
    abrirModal();
  }
})();
