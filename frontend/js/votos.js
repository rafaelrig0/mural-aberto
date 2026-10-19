/* Votação de obras — guardada SOMENTE neste navegador (localStorage).
 *
 * IMPORTANTE: o backend ainda não tem um recurso de votos. Por isso cada navegador guarda o próprio
 * voto e a contagem NÃO é compartilhada entre visitantes. Quando o backend ganhar esse recurso,
 * basta trocar as funções abaixo (lerVoto, contagem, votar, removerVoto) por chamadas à API; as
 * páginas só usam essas quatro funções.
 */
(function () {
  "use strict";

  const CHAVE = "mural-aberto-votos";
  let emMemoria = { meu: null, contagens: {} }; // usado se o navegador bloquear o armazenamento

  function ler() {
    try {
      const bruto = JSON.parse(localStorage.getItem(CHAVE) || "null");
      if (bruto && typeof bruto === "object") {
        const contagens = {};
        for (const [id, n] of Object.entries(bruto.contagens || {})) {
          if (/^\d+$/.test(id) && Number.isInteger(n) && n > 0) contagens[id] = n;
        }
        const meu = Number.isInteger(bruto.meu) ? bruto.meu : null;
        emMemoria = { meu, contagens };
      }
    } catch {
      /* usa o que está em memória */
    }
    return emMemoria;
  }

  function gravar(estado) {
    emMemoria = estado;
    try {
      localStorage.setItem(CHAVE, JSON.stringify(estado));
    } catch {
      /* sem armazenamento: o voto vale enquanto a página estiver aberta */
    }
  }

  /** Identificador da obra em que esta pessoa votou (ou null). */
  function lerVoto() {
    return ler().meu;
  }

  /** Quantos votos a obra tem (neste navegador). */
  function contagem(id) {
    return ler().contagens[String(id)] || 0;
  }

  function descontar(estado, id) {
    const chave = String(id);
    if (estado.contagens[chave]) {
      estado.contagens[chave] -= 1;
      if (estado.contagens[chave] <= 0) delete estado.contagens[chave];
    }
  }

  /** Registra o voto; se a pessoa já tinha votado em outra obra, o voto é movido. */
  function votar(id) {
    const numero = Number(id);
    const estado = ler();
    if (estado.meu === numero) return;
    if (estado.meu !== null) descontar(estado, estado.meu);
    estado.meu = numero;
    estado.contagens[String(numero)] = (estado.contagens[String(numero)] || 0) + 1;
    gravar(estado);
  }

  function removerVoto() {
    const estado = ler();
    if (estado.meu !== null) descontar(estado, estado.meu);
    estado.meu = null;
    gravar(estado);
  }

  window.Mural.votos = { lerVoto, contagem, votar, removerVoto };
})();
