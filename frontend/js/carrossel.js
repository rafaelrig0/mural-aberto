/* Carrossel acessível, sem bibliotecas.
 *
 * - Rolagem horizontal com "snap" (funciona com o dedo, o mouse e as setas do teclado).
 * - Botões Anterior/Próximo (dão a volta no fim), contador "2 / 5" anunciado a leitores de tela.
 * - Slides que não estão à vista ficam `inert` (não recebem foco nem são lidos).
 * - Sem rolagem animada para quem pediu menos movimento (prefers-reduced-motion).
 * - Não troca de slide sozinho (sem autoplay), para não atrapalhar a leitura.
 */
(function () {
  "use strict";
  const { criar } = window.Mural;

  /**
   * @param {string} rotulo  nome do carrossel para leitores de tela
   * @param {Node[]} slides  conteúdo de cada slide
   * @returns {HTMLElement}
   */
  function carrossel(rotulo, slides) {
    const total = slides.length;
    const trilho = criar(
      "div",
      { classe: "carrossel-trilho", tabindex: "0", role: "group", "aria-label": "Slides. Use as setas do teclado para trocar." },
      slides.map((conteudo, i) =>
        criar(
          "div",
          { classe: "slide", role: "group", "aria-roledescription": "slide", "aria-label": i + 1 + " de " + total },
          conteudo,
        ),
      ),
    );
    const contador = criar("span", { classe: "carrossel-contador", "aria-live": "polite", "aria-atomic": "true" });
    const raiz = criar("div", { classe: "carrossel", role: "region", "aria-roledescription": "carrossel", "aria-label": rotulo }, trilho);

    let atual = 0;

    function reduzirMovimento() {
      return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    function marcar(indice) {
      atual = indice;
      contador.textContent = indice + 1 + " / " + total;
      [...trilho.children].forEach((slide, i) => {
        if (i === indice) slide.removeAttribute("inert");
        else slide.setAttribute("inert", "");
      });
    }

    function ir(indice) {
      const destino = (indice + total) % total;
      trilho.scrollTo({ left: destino * trilho.clientWidth, behavior: reduzirMovimento() ? "auto" : "smooth" });
      marcar(destino);
    }

    trilho.addEventListener("scroll", () => {
      if (!trilho.clientWidth) return;
      const indice = Math.min(total - 1, Math.max(0, Math.round(trilho.scrollLeft / trilho.clientWidth)));
      if (indice !== atual) marcar(indice);
    });

    trilho.addEventListener("keydown", (evento) => {
      if (evento.key === "ArrowRight") {
        evento.preventDefault();
        ir(atual + 1);
      } else if (evento.key === "ArrowLeft") {
        evento.preventDefault();
        ir(atual - 1);
      } else if (evento.key === "Home") {
        evento.preventDefault();
        ir(0);
      } else if (evento.key === "End") {
        evento.preventDefault();
        ir(total - 1);
      }
    });

    // Se a janela mudar de tamanho, mantém o slide atual alinhado.
    window.addEventListener("resize", () => {
      trilho.scrollTo({ left: atual * trilho.clientWidth, behavior: "auto" });
    });

    marcar(0);

    if (total > 1) {
      raiz.append(
        criar(
          "div",
          { classe: "carrossel-controles" },
          contador,
          criar("button", { classe: "carrossel-botao", type: "button", "aria-label": "Slide anterior", texto: "‹", aoClicar: () => ir(atual - 1) }),
          criar("button", { classe: "carrossel-botao", type: "button", "aria-label": "Próximo slide", texto: "›", aoClicar: () => ir(atual + 1) }),
        ),
      );
    }
    return raiz;
  }

  window.Mural.carrossel = carrossel;
})();
