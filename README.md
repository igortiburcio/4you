# 4you RH - Sistema Gerenciador de Recursos Humanos

Aplicacao web monolitica para gestao de RH, desenvolvida em Python com Django (SSR), HTMX e SQLite.

O sistema foi pensado para pequenas e medias empresas que precisam centralizar operacoes basicas de RH com rapidez e simplicidade: cadastro, consulta, edicao e desligamento de funcionarios.

## Sumario

- [Visao geral](#visao-geral)
- [Funcionalidades](#funcionalidades)
- [Stack e arquitetura](#stack-e-arquitetura)
- [Arquitetura detalhada](#arquitetura-detalhada)
- [Requisitos](#requisitos)
- [Como executar localmente](#como-executar-localmente)
- [Credenciais iniciais](#credenciais-iniciais)
- [Comandos uteis](#comandos-uteis)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Fluxos principais](#fluxos-principais)
- [Permissoes e perfis](#permissoes-e-perfis)
- [Testes](#testes)
- [Roadmap](#roadmap)

## Visao geral

O 4you RH substitui processos manuais (planilhas e anotacoes) por uma interface web unica para o setor de RH.

Objetivos do MVP:

- centralizar dados de funcionarios e departamentos;
- reduzir erros de cadastro e consulta;
- facilitar operacoes administrativas recorrentes;
- disponibilizar visualizacoes basicas de analise em graficos.

## Funcionalidades

### Modulo de autenticacao

- login e logout com sessao (Django auth);
- protecao de rotas com controle por perfil/grupo.

### Modulo de funcionarios

- cadastro de funcionario;
- listagem com busca por nome, cargo, matricula e CPF;
- filtro por status (ativo/desligado);
- edicao de dados;
- desligamento logico (sem exclusao fisica);
- exibicao de salario na listagem.

### Modulo de departamentos

- cadastro e listagem de departamentos;
- status ativo/inativo.

### Modulo de analises

- grafico de funcionarios por departamento;
- grafico de funcionarios por status;
- grafico de salario por funcionario.

## Stack e arquitetura

- Backend: Django 4.2
- Frontend (SSR): Django Templates
- Interatividade parcial: HTMX
- Graficos: Chart.js
- Banco de dados: SQLite
- Gerenciador de ambiente/dependencias: uv

Padrao arquitetural adotado:

- monolito web (uma aplicacao, um deploy, uma base);
- separacao por apps Django (`core`, `accounts`, `employees`);
- renderizacao server-side com atualizacoes parciais via HTMX.

## Arquitetura detalhada

### Onde o app inicializa

- `manage.py`: ponto de entrada para comandos de desenvolvimento (`runserver`, `migrate`, `test`, etc.).
- `config/settings.py`: configuracoes globais (apps instalados, templates, banco, auth, static).
- `config/urls.py`: roteador principal que inclui as rotas dos apps (`core`, `accounts`, `employees`).
- `config/wsgi.py` e `config/asgi.py`: pontos de entrada para deploy em servidores WSGI/ASGI.

### Como as requisicoes fluem

1. Navegador faz requisicao HTTP.
2. Django resolve a rota em `config/urls.py` e encaminha para o app correto.
3. A view do app processa regras e consulta modelos (`employees/models.py`).
4. A view renderiza template HTML (SSR) e devolve pagina pronta ao cliente.
5. Quando ha HTMX, apenas um fragmento (partial) e atualizado sem recarregar a pagina inteira.

Diagrama do fluxo:

```text
[Browser]
   |
   | HTTP Request
   v
[config/urls.py]
   |
   | resolve rota
   v
[App URLConf]
   |  (core/urls.py, accounts/urls.py, employees/urls.py)
   v
[View]
   |
   | valida permissao + aplica regra de negocio
   v
[Model/ORM]
   |
   | leitura/escrita
   v
[SQLite]
   |
   | dados
   v
[View]
   |
   | render(template, contexto)
   v
[Template SSR]
   |
   | HTML completo ou partial HTMX
   v
[Browser]
```

### Responsabilidade de cada app

- `accounts`: autenticacao (login/logout), controle de acesso por grupos e tags auxiliares de template.
- `core`: dashboard principal com indicadores resumidos.
- `employees`: dominio de RH (funcionarios, departamentos, formularios, CRUD, filtros e analises).

### Camadas internas

- **Models**: definem estrutura e regras de dados (ex.: `Employee`, `Department`).
- **Forms**: validam entrada do usuario (ex.: CPF, matricula unica).
- **Views**: orquestram regras, permissao, consultas e renderizacao.
- **Templates**: composicao visual SSR e parciais HTMX.
- **Admin**: interface operacional para suporte e manutencao de dados.

### Banco de dados e migracoes

- Banco local: SQLite (`db.sqlite3`).
- Evolucao de schema: arquivos em `employees/migrations/`.
- Comandos:
  - `uv run python manage.py makemigrations`
  - `uv run python manage.py migrate`

### Dados iniciais do sistema

- Comando `seed_initial_data` cria:
  - grupos (`admin_rh`, `gerente`, `funcionario`),
  - usuario inicial `admin.rh`,
  - departamentos padrao,
  - funcionarios de exemplo.

Execucao:

```bash
uv run python manage.py seed_initial_data
```

### Frontend no projeto

- Renderizacao principal via Django Templates (SSR).
- HTMX para interacoes parciais (filtros/paginacao/acoes sem reload total).
- Chart.js para graficos da tela de analises.

## Requisitos

- Python 3.10 ou superior
- `uv` instalado no sistema

## Como executar localmente

1. Acesse a pasta do projeto:

```bash
cd "/Users/igortiburciocavalcanti/Projetos/4you"
```

2. Instale dependencias e crie o ambiente virtual:

```bash
uv sync
```

3. Execute migracoes:

```bash
uv run python manage.py migrate
```

4. Popule dados iniciais (usuarios, grupos, departamentos e funcionarios de exemplo):

```bash
uv run python manage.py seed_initial_data
```

5. Inicie o servidor:

```bash
uv run python manage.py runserver
```

6. Abra no navegador:

```text
http://127.0.0.1:8000/accounts/login/
```

## Credenciais iniciais

- Usuario: `admin.rh`
- Senha: `admin1234`

## Comandos uteis

- Rodar testes:

```bash
uv run python manage.py test
```

- Criar migracoes novas:

```bash
uv run python manage.py makemigrations
```

- Criar superusuario manual:

```bash
uv run python manage.py createsuperuser
```

## Estrutura de pastas

```text
4you/
├── accounts/            # login, logout, tags de permissao
├── core/                # dashboard principal
├── employees/           # dominios de RH (funcionarios/departamentos)
├── config/              # settings, urls e bootstrap Django
├── templates/           # templates SSR e parciais HTMX
├── static/              # css e assets locais
├── manage.py
├── pyproject.toml
└── uv.lock
```

## Fluxos principais

### 1) Acesso

- usuario entra em `/accounts/login/`;
- sistema valida credenciais e redireciona para dashboard.

### 2) Operacao de RH

- RH acessa modulo de funcionarios;
- cadastra ou edita dados;
- consulta lista com busca e filtros;
- realiza desligamento quando necessario.

### 3) Analise gerencial

- perfil autorizado acessa tela de analises;
- sistema exibe distribuicao por departamento, status e salarios.

## Permissoes e perfis

Grupos principais:

- `admin_rh`: CRUD completo de funcionarios e departamentos;
- `gerente`: visualizacao e analises;
- `funcionario`: reservado para evolucoes futuras.

Superusuario tambem possui acesso total.

## Testes

O projeto possui testes automatizados para:

- autenticacao e protecao de rotas;
- busca de funcionarios;
- regras de permissao por perfil;
- validacao de CPF duplicado;
- desligamento logico;
- acesso a pagina de analises.

Execucao:

```bash
uv run python manage.py test
```

## Roadmap

- solicitacoes de alteracao de dados por funcionario;
- exportacao de relatorios (CSV/PDF);
- dashboard com filtros por periodo;
- auditoria de operacoes administrativas.
