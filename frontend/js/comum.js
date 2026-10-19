/* Mural Aberto — funções compartilhadas por todas as páginas.
 *
 * SEGURANÇA: todo texto vindo da API (títulos, comentários, mensagens...) é inserido na página
 * apenas como TEXTO (textContent / nós de texto), nunca como HTML. Por isso um conteúdo como
 * "<script>" aparece escrito na tela e não é executado. Não use innerHTML com dados da API.
 */
(function () {
  "use strict";

  const config = window.CONFIG;

  /* ------------------------------------------------------------------ DOM */

  const EVENTOS = { aoClicar: "click", aoEnviar: "submit", aoMudar: "change", aoDigitar: "input" };

  function criar(tag, atributos, ...filhos) {
    const no = document.createElement(tag);
    for (const [chave, valor] of Object.entries(atributos || {})) {
      if (valor === null || valor === undefined || valor === false) continue;
      if (chave === "classe") no.className = valor;
      else if (chave === "texto") no.textContent = valor;
      else if (EVENTOS[chave]) no.addEventListener(EVENTOS[chave], valor);
      else no.setAttribute(chave, valor === true ? "" : String(valor));
    }
    for (const filho of filhos.flat()) {
      if (filho === null || filho === undefined || filho === false) continue;
      no.append(filho instanceof Node ? filho : document.createTextNode(String(filho)));
    }
    return no;
  }

  function limpar(no) {
    while (no.firstChild) no.removeChild(no.firstChild);
    return no;
  }

  /* ------------------------------------------------------------- Rótulos */

  const ROTULOS_CAMPOS = {
    title: "Título",
    author_name: "Nome",
    contact_email: "E-mail de contato",
    category_id: "Categoria",
    work_type: "Categoria",
    created_on: "Data de criação",
    neighborhood: "Bairro",
    body_text: "Texto da obra",
    alt_text: "Descrição da imagem",
    usage_authorized: "Autorização de uso",
    content: "Comentário",
    feedback_type: "Tipo de feedback",
    message: "Mensagem",
    rating: "Nota",
    image: "Imagem",
    video: "Vídeo",
    email: "E-mail",
    password: "Senha",
    name: "Nome",
    reason: "Motivo",
  };

  const TIPOS_FEEDBACK = {
    opinion: "Opinião",
    suggestion: "Sugestão",
    bug: "Relatar problema",
    other: "Outro",
  };

  const STATUS_OBRA = {
    pending: "Pendente",
    approved: "Aprovada",
    rejected: "Rejeitada",
    archived: "Arquivada",
  };

  const STATUS_COMENTARIO = { pending: "Pendente", approved: "Aprovado", rejected: "Rejeitado" };

  /** Categoria e tipo da obra são a mesma coisa para quem usa o site: a pessoa escolhe só a categoria.
   *  O servidor exige também o "tipo" (visual ou texto); ele é deduzido da categoria escolhida.
   *  Categorias de texto: o apelido (slug) delas fica em CATEGORIAS_DE_TEXTO, em js/config.js. */
  function tipoDaCategoria(categoria) {
    const textos = config.CATEGORIAS_DE_TEXTO || [];
    return categoria && textos.includes(categoria.slug) ? "text" : "visual";
  }

  /* ----------------------------------------------------------- Sessão admin */

  const CHAVE_TOKEN = "mural-aberto-token";
  let tokenEmMemoria = null; // usado se o navegador bloquear o armazenamento

  function obterToken() {
    try {
      return sessionStorage.getItem(CHAVE_TOKEN) || tokenEmMemoria;
    } catch {
      return tokenEmMemoria;
    }
  }

  function salvarToken(token) {
    tokenEmMemoria = token;
    try {
      sessionStorage.setItem(CHAVE_TOKEN, token);
    } catch {
      /* sem armazenamento: o login vale apenas enquanto a página estiver aberta */
    }
  }

  function limparToken() {
    tokenEmMemoria = null;
    try {
      sessionStorage.removeItem(CHAVE_TOKEN);
    } catch {
      /* ignora */
    }
  }

  /* ------------------------------------------------------------------ API */

  class ErroApi extends Error {
    constructor(status, codigo, mensagem, detalhes) {
      super(mensagem);
      this.status = status;
      this.codigo = codigo;
      this.detalhes = detalhes || [];
    }
  }

  async function requisitar(metodo, caminho, opcoes = {}) {
    const cabecalhos = {};
    let corpo;
    if (opcoes.json !== undefined) {
      cabecalhos["Content-Type"] = "application/json";
      corpo = JSON.stringify(opcoes.json);
    } else if (opcoes.formulario) {
      corpo = opcoes.formulario; // o navegador define o Content-Type multipart sozinho
    }
    if (opcoes.admin) {
      const token = obterToken();
      if (token) cabecalhos.Authorization = "Bearer " + token;
    }

    let resposta;
    try {
      resposta = await fetch(config.URL_API + caminho, { method: metodo, headers: cabecalhos, body: corpo });
    } catch {
      throw new ErroApi(
        0,
        "sem_conexao",
        "Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.",
        [],
      );
    }

    if (resposta.status === 204) return null;

    let dados = null;
    try {
      dados = await resposta.json();
    } catch {
      /* resposta sem JSON */
    }

    if (!resposta.ok) {
      const erro = dados && dados.error ? dados.error : {};
      if (opcoes.admin && resposta.status === 401) {
        limparToken();
        document.dispatchEvent(new CustomEvent("mural:sessao-expirada"));
      }
      throw new ErroApi(
        resposta.status,
        erro.code || "erro",
        erro.message || "Ocorreu um erro inesperado. Tente novamente.",
        erro.details || [],
      );
    }
    return dados;
  }

  const api = {
    get: (caminho, opcoes) => requisitar("GET", caminho, opcoes),
    post: (caminho, opcoes) => requisitar("POST", caminho, opcoes),
    put: (caminho, opcoes) => requisitar("PUT", caminho, opcoes),
    excluir: (caminho, opcoes) => requisitar("DELETE", caminho, opcoes),
  };

  /** Monta a query string ignorando valores vazios. */
  function consulta(parametros) {
    const busca = new URLSearchParams();
    for (const [chave, valor] of Object.entries(parametros)) {
      if (valor !== "" && valor !== null && valor !== undefined) busca.set(chave, valor);
    }
    const texto = busca.toString();
    return texto ? "?" + texto : "";
  }

  /* --------------------------------------------------------------- Erros */

  /** Texto amigável (em português) para qualquer erro da API. */
  function textoDoErro(erro) {
    if (!(erro instanceof ErroApi)) return "Ocorreu um erro inesperado. Tente novamente.";
    if (erro.codigo === "validation_error" && erro.detalhes.length) {
      const nomes = erro.detalhes.map((d) => ROTULOS_CAMPOS[d.field] || d.field).filter(Boolean);
      return "Confira os campos: " + [...new Set(nomes)].join(", ") + ".";
    }
    if (erro.codigo === "invalid_parameter") return "Um dos valores informados não é válido.";
    return erro.message;
  }

  /** Mapa campo -> mensagem, para marcar cada campo do formulário que a API recusou. */
  function errosPorCampo(erro) {
    const mapa = {};
    if (erro instanceof ErroApi && erro.codigo === "validation_error") {
      for (const d of erro.detalhes) {
        const rotulo = ROTULOS_CAMPOS[d.field] || d.field;
        mapa[d.field] = 'Verifique o campo "' + rotulo + '".';
      }
    }
    return mapa;
  }

  /* ---------------------------------------------------------- Formulários */

  function campoDe(formulario, nome) {
    const controle = formulario.elements[nome];
    const primeiro = controle && controle.length !== undefined && !controle.tagName ? controle[0] : controle;
    return primeiro ? primeiro.closest(".campo") : null;
  }

  function definirErro(formulario, nome, mensagem) {
    const campo = campoDe(formulario, nome);
    if (!campo) return false;
    const aviso = campo.querySelector(".campo-erro");
    if (aviso) aviso.textContent = mensagem;
    for (const controle of campo.querySelectorAll("input, select, textarea")) {
      controle.setAttribute("aria-invalid", "true");
    }
    return true;
  }

  function limparErros(formulario) {
    for (const aviso of formulario.querySelectorAll(".campo-erro")) aviso.textContent = "";
    for (const controle of formulario.querySelectorAll("[aria-invalid]")) {
      controle.removeAttribute("aria-invalid");
    }
  }

  /** Leva o foco ao primeiro campo com erro, para leitores de tela e teclado. */
  function focarPrimeiroErro(formulario) {
    const alvo = formulario.querySelector('[aria-invalid="true"]');
    if (alvo) alvo.focus();
  }

  /** Mostra um aviso (sucesso, erro ou info) com texto, sem depender só de cor. */
  function mostrarAviso(recipiente, tipo, texto) {
    limpar(recipiente);
    if (!texto) return;
    const prefixo = { sucesso: "Pronto:", erro: "Atenção:", info: "Aviso:" }[tipo];
    recipiente.className = "aviso aviso-" + tipo;
    recipiente.setAttribute("role", tipo === "erro" ? "alert" : "status");
    recipiente.append(criar("strong", { texto: prefixo }), document.createTextNode(texto));
  }

  /** Impede envio duplo: desativa o botão enquanto a requisição está em andamento. */
  async function comBotaoOcupado(botao, textoOcupado, tarefa) {
    const textoOriginal = botao.textContent;
    botao.disabled = true;
    botao.textContent = textoOcupado;
    try {
      return await tarefa();
    } finally {
      botao.disabled = false;
      botao.textContent = textoOriginal;
    }
  }

  /* ---------------------------------------------------------- Formatação */

  function formatarData(texto, comHora) {
    if (!texto) return "";
    const data = /^\d{4}-\d{2}-\d{2}$/.test(texto) ? new Date(texto + "T12:00:00") : new Date(texto);
    if (Number.isNaN(data.getTime())) return "";
    const opcoes = comHora
      ? { dateStyle: "short", timeStyle: "short" }
      : { day: "2-digit", month: "long", year: "numeric" };
    return data.toLocaleString("pt-BR", opcoes);
  }

  function estrelas(nota) {
    if (!nota) return criar("span", { classe: "meta", texto: "Sem nota" });
    return criar(
      "span",
      { classe: "estrelas", role: "img", "aria-label": "Nota " + nota + " de 5" },
      criar("span", { "aria-hidden": "true", texto: "★".repeat(nota) + "☆".repeat(5 - nota) }),
    );
  }

  /* ----------------------------------------------------- Cartão de obra */

  function cartaoObra(obra) {
    let midia;
    if (obra.image_url) {
      midia = criar("img", {
        src: obra.image_url,
        alt: obra.alt_text || "Imagem da obra " + obra.title,
        loading: "lazy",
      });
    } else if (obra.excerpt) {
      midia = criar("p", { classe: "cartao-trecho" }, criar("span", { texto: obra.excerpt }));
    } else if (obra.video_url) {
      midia = criar("span", { classe: "cartao-video", texto: "▶ Obra em vídeo" });
    } else {
      midia = criar("span", { classe: "cartao-video", texto: "Sem pré-visualização" });
    }

    const partesMeta = ["por " + obra.author_name, obra.category.name];
    return criar(
      "li",
      {},
      criar(
        "article",
        { classe: "cartao" },
        criar("div", { classe: "cartao-midia" }, midia),
        criar(
          "div",
          { classe: "cartao-corpo" },
          criar(
            "h3",
            {},
            criar("a", { classe: "cartao-titulo", href: "obra.html?id=" + encodeURIComponent(obra.id), texto: obra.title }),
          ),
          criar("p", { classe: "meta", texto: partesMeta.join(" · ") }),
          obra.neighborhood ? criar("p", { classe: "meta", texto: "Bairro: " + obra.neighborhood }) : null,
        ),
      ),
    );
  }

  /** Mídia de uma obra para vitrines (carrossel, votação): imagem, trecho do texto ou aviso de vídeo. */
  function midiaDaObra(obra, classes) {
    if (obra.image_url) {
      return criar("img", { src: obra.image_url, alt: obra.alt_text || "Imagem da obra " + obra.title, loading: "lazy" });
    }
    if (obra.excerpt) {
      return criar("p", { classe: classes.trecho }, criar("span", { texto: obra.excerpt }));
    }
    return criar("span", { classe: classes.video, texto: obra.video_url ? "▶ Obra em vídeo" : "Sem pré-visualização" });
  }

  /* ------------------------------------------------------------ Paginação */

  /**
   * opcoes.href(n)  -> endereço da página n (links, para páginas públicas)
   * opcoes.aoIr(n)  -> função chamada ao clicar (botões, para o painel)
   */
  function paginacao(pagina, tamanho, total, opcoes) {
    const totalPaginas = Math.max(1, Math.ceil(total / tamanho));
    const nav = criar("nav", { classe: "paginacao", "aria-label": "Paginação" });
    if (totalPaginas <= 1) return nav;

    function controle(rotulo, destino, desativado) {
      if (desativado) {
        return criar("span", { classe: "botao botao-secundario botao-pequeno", "aria-disabled": "true", texto: rotulo });
      }
      if (opcoes.href) {
        return criar("a", { classe: "botao botao-secundario botao-pequeno", href: opcoes.href(destino), texto: rotulo });
      }
      return criar("button", {
        type: "button",
        classe: "botao botao-secundario botao-pequeno",
        texto: rotulo,
        aoClicar: () => opcoes.aoIr(destino),
      });
    }

    nav.append(
      controle("← Anterior", pagina - 1, pagina <= 1),
      criar("span", { "aria-current": "page", texto: "Página " + pagina + " de " + totalPaginas }),
      controle("Próxima →", pagina + 1, pagina >= totalPaginas),
    );
    return nav;
  }

  function numeroDaConsulta(parametros, nome, padrao) {
    const valor = Number.parseInt(parametros.get(nome), 10);
    return Number.isFinite(valor) && valor > 0 ? valor : padrao;
  }

  /* ----------------------------------------------- Cabeçalho e rodapé */

  const MENU = [
    { arquivo: "index.html", rotulo: "Início" },
    { arquivo: "obras.html", rotulo: "Obras" },
    { arquivo: "organizacoes.html", rotulo: "Organizações" },
    { arquivo: "feedback.html", rotulo: "Feedback" },
  ];

  function arquivoAtual() {
    const ultimo = location.pathname.split("/").pop();
    return ultimo || "index.html";
  }

  /** Logotipo em SVG (decorativo): quadrado arredondado com um "M". */
  function logotipo() {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    for (const [chave, valor] of Object.entries({ width: "34", height: "34", viewBox: "0 0 32 32", "aria-hidden": "true", focusable: "false" })) {
      svg.setAttribute(chave, valor);
    }
    const fundo = document.createElementNS(ns, "rect");
    for (const [chave, valor] of Object.entries({ width: "32", height: "32", rx: "10", fill: "#c2410c" })) {
      fundo.setAttribute(chave, valor);
    }
    const letra = document.createElementNS(ns, "path");
    for (const [chave, valor] of Object.entries({
      d: "M8 24V11l8 8 8-8v13",
      stroke: "#fff",
      "stroke-width": "3",
      fill: "none",
      "stroke-linejoin": "round",
      "stroke-linecap": "round",
    })) {
      letra.setAttribute(chave, valor);
    }
    svg.append(fundo, letra);
    return svg;
  }

  function montarCabecalho(alvo) {
    const atual = arquivoAtual();
    const lista = criar(
      "ul",
      {},
      MENU.map((item) =>
        criar(
          "li",
          {},
          criar("a", {
            href: item.arquivo,
            texto: item.rotulo,
            "aria-current": item.arquivo === atual || (atual === "obra.html" && item.arquivo === "obras.html") ? "page" : false,
          }),
        ),
      ),
    );
    const menu = criar("nav", { classe: "menu-principal", id: "menu-principal", "aria-label": "Principal" }, lista);
    const botao = criar("button", {
      type: "button",
      classe: "menu-botao",
      "aria-expanded": "false",
      "aria-controls": "menu-principal",
      texto: "Menu",
      aoClicar: () => {
        const aberto = menu.classList.toggle("aberto");
        botao.setAttribute("aria-expanded", String(aberto));
      },
    });
    alvo.classList.add("cabecalho");
    alvo.append(
      criar(
        "div",
        { classe: "conteiner cabecalho-linha" },
        criar("a", { classe: "marca", href: "index.html", "aria-label": "Mural Aberto, página inicial" }, logotipo(), "Mural Aberto"),
        botao,
        menu,
      ),
    );
  }

  function montarRodape(alvo) {
    alvo.classList.add("rodape");
    alvo.append(
      criar(
        "div",
        { classe: "conteiner rodape-linha" },
        criar("p", {}, criar("strong", { texto: "Mural Aberto" }), " — arte feita no bairro, por quem vive nele."),
        criar(
          "ul",
          {},
          criar("li", {}, criar("a", { href: "obras.html", texto: "Ver obras" })),
          criar("li", {}, criar("a", { href: "organizacoes.html", texto: "Organizações parceiras" })),
          criar("li", {}, criar("a", { href: "feedback.html", texto: "Envie sua opinião" })),
        ),
      ),
    );
  }

  function iniciarPagina() {
    const cabecalho = document.getElementById("cabecalho");
    const rodape = document.getElementById("rodape");
    if (cabecalho) montarCabecalho(cabecalho);
    if (rodape) montarRodape(rodape);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciarPagina);
  else iniciarPagina();

  window.Mural = {
    config,
    criar,
    limpar,
    api,
    consulta,
    ErroApi,
    obterToken,
    salvarToken,
    limparToken,
    textoDoErro,
    errosPorCampo,
    definirErro,
    limparErros,
    focarPrimeiroErro,
    mostrarAviso,
    comBotaoOcupado,
    formatarData,
    estrelas,
    cartaoObra,
    midiaDaObra,
    tipoDaCategoria,
    paginacao,
    numeroDaConsulta,
    ROTULOS_CAMPOS,
    TIPOS_FEEDBACK,
    STATUS_OBRA,
    STATUS_COMENTARIO,
  };
})();
