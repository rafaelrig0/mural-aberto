/* Organizações parceiras do Mural Aberto.
 *
 * >>> ESTES SÃO DADOS DE EXEMPLO. Troque pelos dados reais das organizações parceiras. <<<
 *
 * O backend não tem cadastro de organizações, então a lista fica aqui, num único lugar, e é usada
 * pela página "Organizações" e pelo destaque da página inicial. Para incluir ou remover uma
 * organização, basta editar a lista abaixo.
 *
 * Campos de cada organização:
 *   id           apelido sem espaços nem acentos (usado no endereço organizacoes.html#id)
 *   nome         nome da organização
 *   descricao    quem são e o que fazem (1 ou 2 frases)
 *   contribuicoes lista curta do que fazem pelo bairro
 *   site         endereço completo do site, começando com https:// (ou deixe "" para não mostrar o botão)
 *   imagem       (opcional) endereço de uma imagem de capa; sem ela aparece uma capa colorida com as iniciais
 *   imagemAlt    (opcional) descrição da imagem, obrigatória se usar "imagem"
 */
window.ORGANIZACOES = [
  {
    id: "organizacao-exemplo-1",
    nome: "Organização Exemplo 1",
    descricao: "Grupo de grafiteiros e muralistas que transforma muros abandonados em galerias a céu aberto.",
    contribuicoes: ["Oficinas gratuitas de grafite para jovens", "Murais coletivos nos bairros", "Empréstimo de material de pintura"],
    site: "https://example.org/organizacao-exemplo-1",
  },
  {
    id: "organizacao-exemplo-2",
    nome: "Organização Exemplo 2",
    descricao: "Organização que registra histórias e fotografias antigas de moradores para preservar a memória local.",
    contribuicoes: ["Acervo digital de fotos de família", "Rodas de conversa com moradores mais velhos", "Exposição anual sobre a memória do bairro"],
    site: "https://example.org/organizacao-exemplo-2",
  },
  {
    id: "organizacao-exemplo-3",
    nome: "Organização Exemplo 3",
    descricao: "Escola popular de fotografia que ensina jovens a contar a história do próprio bairro com câmeras e celulares.",
    contribuicoes: ["Curso básico de fotografia", "Empréstimo de câmeras", "Mostra fotográfica anual"],
    site: "https://example.org/organizacao-exemplo-3",
  },
  {
    id: "organizacao-exemplo-4",
    nome: "Organização Exemplo 4",
    descricao: "Instituto que leva pintura e desenho a escolas públicas e centros de convivência.",
    contribuicoes: ["Aulas de desenho em escolas públicas", "Bolsas para artistas iniciantes", "Ponto de coleta de obras físicas"],
    site: "https://example.org/organizacao-exemplo-4",
  },
];
