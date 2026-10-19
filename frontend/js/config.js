/* Configuração do site. Altere aqui o endereço da API quando publicar. */
window.CONFIG = {
  // Endereço do backend (inclua o prefixo /api/v1, sem barra no final).
  URL_API: "https://mural-aberto.onrender.com/api/v1",
  // Devem acompanhar MAX_IMAGE_SIZE_MB e MAX_VIDEO_SIZE_MB do backend (o servidor é quem decide).
  MAX_IMAGEM_MB: 10,
  MAX_VIDEO_MB: 50,
  // Apelidos (slug) das categorias que são obras em TEXTO. As demais são obras visuais (imagem/vídeo).
  // Ao criar uma categoria de texto nova no painel, acrescente o apelido dela aqui.
  CATEGORIAS_DE_TEXTO: ["poema", "cronica", "conto"],
};
