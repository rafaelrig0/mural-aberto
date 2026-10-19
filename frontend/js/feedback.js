/* Página de feedback: opinião, sugestão ou relato de problema, com nota opcional de 1 a 5. */
(function () {
  "use strict";
  const {
    api, criar, mostrarAviso, textoDoErro, definirErro, limparErros, focarPrimeiroErro,
    comBotaoOcupado, errosPorCampo,
  } = window.Mural;

  const MAXIMO_MENSAGEM = 2000;
  const MINIMO_MENSAGEM = 5;

  const formulario = document.getElementById("formulario");
  const aviso = document.getElementById("aviso");
  const mensagem = document.getElementById("mensagem");
  const contador = document.getElementById("contador");
  const estrelas = document.getElementById("estrelas");

  /* ---- Nota por estrelas: botões de opção reais (teclado e leitor de tela funcionam) ---- */

  const NOMES_NOTA = ["", "1 estrela", "2 estrelas", "3 estrelas", "4 estrelas", "5 estrelas"];
  const textoNota = criar("span", { classe: "estrelas-valor", "aria-live": "polite" });

  function pintarEstrelas() {
    const escolhida = Number(formulario.elements.rating?.value || 0);
    estrelas.querySelectorAll("label.estrela").forEach((rotulo, indice) => {
      rotulo.classList.toggle("ativa", indice < escolhida);
    });
    textoNota.textContent = escolhida ? escolhida + " de 5" : "Sem nota";
    limparNota.hidden = !escolhida;
  }

  const limparNota = criar("button", {
    type: "button",
    classe: "botao botao-secundario botao-pequeno",
    texto: "Limpar nota",
    aoClicar: () => {
      formulario.querySelectorAll('input[name="rating"]').forEach((r) => (r.checked = false));
      pintarEstrelas();
    },
  });

  for (let valor = 1; valor <= 5; valor += 1) {
    estrelas.append(
      criar("input", { type: "radio", name: "rating", id: "nota-" + valor, value: valor, aoMudar: pintarEstrelas }),
      criar(
        "label",
        { classe: "estrela", for: "nota-" + valor },
        criar("span", { "aria-hidden": "true", texto: "★" }),
        criar("span", { classe: "so-leitor", texto: NOMES_NOTA[valor] }),
      ),
    );
  }
  estrelas.append(textoNota, limparNota);
  pintarEstrelas();

  /* ---- Contador de caracteres ---- */

  function atualizarContador() {
    contador.textContent = mensagem.value.length + " de " + MAXIMO_MENSAGEM + " caracteres";
  }
  mensagem.addEventListener("input", atualizarContador);
  atualizarContador();

  /* ---- Validação e envio ---- */

  function validar() {
    const f = formulario.elements;
    if (!f.feedback_type.value) definirErro(formulario, "feedback_type", "Escolha o tipo de feedback.");
    const texto = f.message.value.trim();
    if (!texto) definirErro(formulario, "message", "Escreva a sua mensagem.");
    else if (texto.length < MINIMO_MENSAGEM) definirErro(formulario, "message", "Escreva pelo menos " + MINIMO_MENSAGEM + " caracteres.");
    return !formulario.querySelector('[aria-invalid="true"]');
  }

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(formulario);
    mostrarAviso(aviso, "info", "");

    if (!validar()) {
      mostrarAviso(aviso, "erro", " Há campos para corrigir. Eles estão marcados abaixo.");
      return focarPrimeiroErro(formulario);
    }

    const f = formulario.elements;
    const corpo = {
      author_name: f.author_name.value.trim() || null,
      feedback_type: f.feedback_type.value,
      message: f.message.value.trim(),
      rating: f.rating.value ? Number(f.rating.value) : null,
    };

    try {
      await comBotaoOcupado(document.getElementById("enviar"), "Enviando…", () =>
        api.post("/feedback", { json: corpo }),
      );
      formulario.reset();
      pintarEstrelas();
      atualizarContador();
      mostrarAviso(aviso, "sucesso", " Feedback enviado. Muito obrigado por ajudar a melhorar o Mural Aberto!");
      aviso.scrollIntoView({ block: "nearest" });
    } catch (erro) {
      Object.entries(errosPorCampo(erro)).forEach(([campo, texto]) => definirErro(formulario, campo, texto));
      mostrarAviso(aviso, "erro", " " + textoDoErro(erro));
      focarPrimeiroErro(formulario);
    }
  });
})();
