# Mural Artístico

## Sobre o projeto

O **Mural Artístico** é uma plataforma digital desenvolvida como projeto acadêmico, com o objetivo de oferecer um espaço aberto para artistas independentes divulgarem suas produções e ampliarem sua visibilidade.

A plataforma permite que artistas compartilhem suas obras sem a necessidade de criar uma conta, contribuindo para a democratização do acesso à arte e para a valorização de diferentes expressões artísticas.

As obras enviadas passam por uma etapa de moderação administrativa antes de serem disponibilizadas publicamente, promovendo um ambiente organizado e adequado para artistas e visitantes.

## Objetivos

- Promover a divulgação de artistas independentes.
- Facilitar o compartilhamento de diferentes manifestações artísticas.
- Democratizar o acesso à produção cultural.
- Oferecer um espaço digital de interação entre artistas e público.
- Implementar mecanismos de moderação para garantir a qualidade das publicações.

## Funcionalidades

### Para artistas
- Envio de obras artísticas sem necessidade de cadastro.
- Informações de identificação do autor, incluindo nome e e-mail para contato.
- Publicação de diferentes formatos de conteúdo artístico.
- Acompanhamento do processo de análise e publicação por meio das comunicações previstas pela plataforma.
- Recebimento do motivo da rejeição de uma obra, quando aplicável.

### Para visitantes
- Visualização das obras aprovadas e publicadas.
- Acesso a diferentes categorias de produções artísticas.
- Possibilidade de interação por meio de comentários, sujeitos à aprovação administrativa.

### Para administradores
- Autenticação para acesso à área administrativa.
- Análise das obras submetidas.
- Aprovação ou rejeição de publicações.
- Inclusão de justificativas para obras rejeitadas.
- Moderação dos comentários enviados pelos visitantes.

## Tipos de conteúdo

A plataforma foi planejada para contemplar diferentes manifestações artísticas, incluindo:

- Imagens e ilustrações.
- Vídeos.
- Poemas.
- Crônicas.
- Contos.
- Textos livres.

## Tecnologias utilizadas

- **Python:** desenvolvimento do backend e implementação das regras de negócio.
- **HTML:** estruturação das páginas da aplicação.
- **JavaScript:** implementação de interatividade e funcionalidades no frontend.
- **Supabase Storage:** armazenamento dos arquivos de mídia enviados à plataforma.

Outras bibliotecas, serviços e tecnologias poderão ser adicionados conforme a implementação do projeto.

## Fluxo de publicação

1. O artista preenche o formulário de envio e informa os dados necessários para identificar sua obra.
2. A obra é registrada com o status `pendente`.
3. Um administrador analisa o conteúdo enviado.
4. A obra é aprovada ou rejeitada.
5. Caso seja aprovada, fica disponível para visualização pública.
6. Caso seja rejeitada, o autor poderá receber a justificativa correspondente.

Os comentários enviados pelos visitantes também passam por aprovação administrativa antes de serem exibidos publicamente.

## Estrutura do projeto

A organização inicial do repositório está prevista da seguinte forma:

```text
mural-artistico/
├── backend/
│   ├── .env
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── ...
├── .gitignore
└── README.md
```

**Observação:** a estrutura acima é ilustrativa. Os arquivos e diretórios devem ser ajustados de acordo com a organização efetiva do código-fonte.

## Pré-requisitos

Antes de executar o projeto, verifique se você possui:

- Python instalado.
- Git instalado.
- Um navegador atualizado.
- Um editor de código, como o Visual Studio Code.
- Acesso às configurações necessárias do Supabase Storage, caso a integração esteja habilitada.

## Instalação e execução

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd mural-artistico
```

Substitua `<URL_DO_REPOSITORIO>` pelo endereço do repositório Git.

### 2. Configurar o backend

Acesse a pasta do backend:

```bash
cd backend
```

Crie um ambiente virtual Python:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```powershell
.venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### 3. Configurar as variáveis de ambiente

Crie um arquivo `.env` na pasta do backend, utilizando os nomes de variáveis exigidos pelo código da aplicação.

Exemplo ilustrativo:

```env
SUPABASE_URL=sua_url
SUPABASE_KEY=sua_chave
SECRET_KEY=sua_chave_secreta
```

Os nomes acima são exemplos e devem ser adaptados às variáveis realmente utilizadas pelo projeto. Preencha os valores com as credenciais apropriadas, sem compartilhá-las publicamente.

### 4. Executar o backend

Inicie o servidor utilizando o comando correspondente ao ponto de entrada da aplicação Python.

Por exemplo, caso o projeto utilize um arquivo executável chamado `main.py`:

```bash
python main.py
```

O comando definitivo depende do framework e da estrutura implementados no backend.

### 5. Executar o frontend

Abra os arquivos do frontend no navegador ou utilize um servidor de desenvolvimento local, conforme a configuração adotada no projeto.

Caso o frontend utilize um servidor próprio, consulte os arquivos de configuração para identificar o comando correto de inicialização.

## Segurança e boas práticas

- O arquivo `.env` não deve ser enviado ao repositório.
- O `.gitignore` deve excluir credenciais, ambientes virtuais, caches e arquivos temporários.
- As credenciais administrativas devem ser protegidas.
- O acesso aos arquivos de mídia deve respeitar as permissões definidas para cada conteúdo.
- Arquivos privados devem ser disponibilizados por mecanismos de acesso controlado, como URLs temporárias, quando aplicável.
- As operações administrativas devem ser protegidas por autenticação e validação de permissões.
- Os conteúdos enviados devem ser validados antes de sua publicação.

## Contexto acadêmico

Este projeto foi desenvolvido no contexto universitário, com o propósito de aplicar conhecimentos de desenvolvimento web, programação backend, integração de serviços e organização de sistemas.

Além do aprendizado técnico, a proposta busca incentivar a valorização da produção artística independente por meio da tecnologia.

## Contribuição

Contribuições para o aprimoramento do projeto podem ser realizadas por meio de sugestões, identificação de problemas e implementação de melhorias.

Para contribuir:

1. Crie um fork ou uma branch para sua alteração.
2. Implemente a melhoria desejada.
3. Teste as alterações realizadas.
4. Envie um pull request para análise.

## Licença

A licença do projeto deverá ser definida pela equipe responsável. Até que uma licença seja escolhida e adicionada ao repositório, não presuma que o código esteja liberado para redistribuição ou uso irrestrito.

---

**Mural Artístico — Tecnologia e criatividade a serviço da arte independente.**
