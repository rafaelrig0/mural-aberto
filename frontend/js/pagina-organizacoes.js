/* Página "Organizações": divulgação das organizações parceiras. */
(function () {
  "use strict";
  const { criar, organizacoes } = window.Mural;

  const grade = document.getElementById("lista-organizacoes");
  const lista = organizacoes.lista();

  if (lista.length === 0) {
    grade.replaceWith(criar("p", { classe: "estado-vazio", texto: "Em breve, as organizações parceiras aparecerão aqui." }));
  } else {
    lista.forEach((org, indice) => grade.append(criar("li", {}, organizacoes.cartaoOrganizacao(org, indice))));
  }

  // Se o endereço trouxer #organizacao-x, leva até o cartão (o realce vem do CSS :target).
  let identificador = location.hash.slice(1);
  try {
    identificador = decodeURIComponent(identificador);
  } catch {
    /* endereço malformado: usa como veio */
  }
  const alvo = identificador ? document.getElementById(identificador) : null;
  if (alvo) alvo.scrollIntoView({ block: "center" });
})();
