# HelpDesk AI Triage API

**API RESTful para gerenciamento de chamados de suporte técnico com triagem inteligente utilizando Google Gemini.**

Desenvolvida com **Python**, **FastAPI**, **SQLAlchemy 2.0** e **Pydantic v2**, a aplicação combina gestão estruturada de chamados, regras de negócio explícitas e inteligência artificial generativa.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-Framework-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white" />
</p>

<p align="center">
  <strong>Arquitetura organizada • Validação rigorosa • IA como apoio à decisão</strong>
</p>

---

## Sumário

- [Visão Geral](#-visão-geral)
- [Arquitetura e Diferenciais](#-arquitetura-e-diferenciais)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Domínio e Estados](#-domínio-e-estados)
- [Endpoints da API](#-endpoints-da-api)
- [Exemplo de Utilização](#-exemplo-de-utilização)
- [Tecnologias](#-tecnologias-utilizadas)
- [Configuração e Execução](#-configuração-e-execução)
- [Testes Automatizados](#-testes-automatizados)

---

## 🎯 Visão Geral

O **HelpDesk AI Triage API** é um projeto de backend voltado à gestão de chamados de suporte técnico, com integração de inteligência artificial para auxiliar na classificação e análise de incidentes.

A aplicação permite registrar, consultar, atualizar e excluir chamados, além de disponibilizar análises técnicas geradas pelo Google Gemini.

A proposta central é utilizar a IA como ferramenta de apoio à equipe de suporte, mantendo o controle operacional e as decisões oficiais sob responsabilidade humana.

## 🏗️ Arquitetura e Diferenciais

O sistema foi desenvolvido considerando separação de responsabilidades, integridade dos dados e resiliência na integração com serviços externos.

### 🤖 Integração com Inteligência Artificial

Na criação de um chamado (`POST /api/v1/tickets`), a aplicação realiza a persistência dos dados antes de solicitar a análise ao Gemini.

A IA pode sugerir:

- Categoria e prioridade do incidente.
- Resumo técnico do problema.
- Possíveis causas.
- Procedimentos recomendados para resolução.

Caso ocorra uma falha na comunicação ou timeout, o chamado permanece registrado normalmente, com os campos de análise da IA não preenchidos.

### 🔒 Separação entre Dados Oficiais e Sugestões da IA

Os dados oficiais do chamado são independentes das sugestões geradas pelo modelo.

| Dados oficiais | Sugestões da IA           |
| -------------- | ------------------------- |
| `category`     | `ai_suggested_category`   |
| `priority`     | `ai_suggested_priority`   |
| `status`       | `ai_technical_summary`    |
| —              | `ai_possible_causes`      |
| —              | `ai_suggested_resolution` |

A inteligência artificial não possui autorização para sobrescrever os dados oficiais.

### 🛡️ Proteção contra Prompt Injection

A construção dos prompts utiliza delimitadores XML específicos (`<untrusted_user_data>`) para isolar as informações fornecidas pelos usuários.

A resposta do modelo também é restringida por meio de **Structured Outputs**, utilizando `response_schema` para estruturar os dados retornados.

### 🔄 Máquina de Estados

O ciclo de vida dos chamados é controlado por transições explícitas.

A aplicação impede alterações cadastrais e novas análises de IA quando um chamado está encerrado (`closed`).

---

## 📁 Estrutura do Projeto

```text
helpdesk-ai-triage/
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/   # Rotas HTTP e tratamento de exceções
│   │
│   ├── core/                # Configurações e variáveis de ambiente
│   ├── db/                  # Engine, sessões e Base declarativa
│   ├── models/              # Entidades ORM e Enums de domínio
│   ├── prompts/             # Engenharia de prompts e sanitização XML
│   ├── schemas/              # Contratos e validações Pydantic
│   ├── services/             # Regras de negócio e integração Gemini
│   │
│   └── main.py               # Inicialização da aplicação
│
├── tests/                    # Testes automatizados com Pytest
│
├── .env.example              # Modelo de variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo Git
└── requirements.txt          # Dependências do projeto
```

---

## 📋 Domínio e Estados

### Categorias

| Valor                       | Descrição                              |
| --------------------------- | -------------------------------------- |
| `hardware`                  | Equipamentos físicos                   |
| `software`                  | Aplicativos e sistemas                 |
| `network`                   | Conectividade e infraestrutura de rede |
| `operating_systems`         | Sistemas operacionais                  |
| `printers_and_peripherals`  | Impressoras e periféricos              |
| `access_and_authentication` | Acesso e autenticação                  |
| `other`                     | Outras ocorrências                     |

**Categoria padrão:** `other`

### Prioridades

| Valor      | Nível   |
| ---------- | ------- |
| `low`      | Baixa   |
| `medium`   | Média   |
| `high`     | Alta    |
| `critical` | Crítica |

**Prioridade padrão:** `medium`

### Status

| Valor         | Descrição    |
| ------------- | ------------ |
| `open`        | Aberto       |
| `in_analysis` | Em análise   |
| `in_progress` | Em andamento |
| `resolved`    | Resolvido    |
| `closed`      | Encerrado    |

**Status padrão:** `open`

### Transições Permitidas

A máquina de estados controla quais alterações são válidas durante o ciclo de vida do chamado.

| Status atual  | Próximos estados permitidos                        |
| ------------- | -------------------------------------------------- |
| `open`        | `in_analysis`, `in_progress`, `resolved`, `closed` |
| `in_analysis` | `in_progress`, `resolved`, `closed`                |
| `in_progress` | `in_analysis`, `resolved`, `closed`                |
| `resolved`    | `in_progress` (reabertura), `closed`               |
| `closed`      | Estado terminal                                    |

**Tratamento de erros:**

- `409 Conflict`: violação de regras de negócio.
- `422 Unprocessable Entity`: dados inválidos, campos vazios após `.strip()` ou valores nulos explícitos.

---

## 🔌 Endpoints da API

A API disponibiliza operações para gerenciamento dos chamados e processamento das análises de inteligência artificial.

| Método   | Endpoint                              | Descrição                               |
| -------- | ------------------------------------- | --------------------------------------- |
| `GET`    | `/health`                             | Verifica a disponibilidade da aplicação |
| `POST`   | `/api/v1/tickets`                     | Cria chamado e realiza triagem inicial  |
| `GET`    | `/api/v1/tickets`                     | Lista chamados com filtros e paginação  |
| `GET`    | `/api/v1/tickets/{ticket_id}`         | Consulta chamado por ID                 |
| `PATCH`  | `/api/v1/tickets/{ticket_id}`         | Atualiza parcialmente um chamado        |
| `POST`   | `/api/v1/tickets/{ticket_id}/analyze` | Solicita nova análise da IA             |
| `DELETE` | `/api/v1/tickets/{ticket_id}`         | Exclui um chamado                       |

### Respostas HTTP

| Endpoint           | Respostas                                |
| ------------------ | ---------------------------------------- |
| Health Check       | `200`                                    |
| Criar chamado      | `201`, `422`                             |
| Listar chamados    | `200`, `422`                             |
| Consultar chamado  | `200`, `404`                             |
| Atualizar chamado  | `200`, `404`, `409`, `422`               |
| Reanalisar chamado | `200`, `404`, `409`, `502`, `503`, `504` |
| Excluir chamado    | `204`, `404`                             |

**Recursos adicionais da listagem:**

- Filtros por `status`, `category` e `priority`.
- Paginação por `skip` e `limit`.

---

## 🧪 Exemplo de Utilização

### Criando um chamado

**Endpoint:** `POST /api/v1/tickets`

**Requisição:**

```json
{
  "title": "Servidor de arquivos inacessível",
  "description": "Ninguém do setor financeiro consegue mapear a pasta compartilhada desde as 8h.",
  "requester_name": "Rhuan"
}
```

**Resposta esperada:** `201 Created`

```json
{
  "id": 1,
  "title": "Servidor de arquivos inacessível",
  "description": "Ninguém do setor financeiro consegue mapear a pasta compartilhada desde as 8h.",
  "requester_name": "Rhuan",
  "category": "other",
  "priority": "medium",
  "status": "open",
  "ai_suggested_category": "network",
  "ai_suggested_priority": "high",
  "ai_technical_summary": "Indisponibilidade de acesso ao servidor de arquivos compartilhados para o setor financeiro, afetando múltiplos usuários desde as 08h.",
  "ai_possible_causes": [
    "Falha na conectividade de rede ou resolução DNS entre a sub-rede do financeiro e o servidor",
    "Serviço SMB/compartilhamento de arquivos interrompido no servidor"
  ],
  "ai_suggested_resolution": [
    "Testar conectividade ICMP e resolução de nomes (DNS) a partir de uma estação do setor financeiro",
    "Verificar o status do serviço de compartilhamento de arquivos e logs de eventos no servidor"
  ],
  "created_at": "2026-11-17T11:20:00Z",
  "updated_at": "2026-11-17T11:20:02Z"
}
```

Observe que a categoria e a prioridade oficiais permanecem com seus valores padrão, enquanto a IA fornece sugestões independentes.

---

## 🧰 Tecnologias Utilizadas

| Tecnologia        | Aplicação                              |
| ----------------- | -------------------------------------- |
| Python            | Linguagem principal                    |
| FastAPI           | Desenvolvimento da API REST            |
| SQLAlchemy 2.0    | Mapeamento objeto-relacional (ORM)     |
| Pydantic v2       | Validação e serialização de dados      |
| Pydantic Settings | Gerenciamento de configurações         |
| Google Gemini     | Análise inteligente dos chamados       |
| Pytest            | Testes automatizados                   |
| SQLite            | Banco de dados local e testes isolados |
| Uvicorn           | Servidor ASGI                          |

---

## ⚙️ Configuração e Execução

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd helpdesk-ai-triage
```

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

Ative o ambiente:

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure as variáveis:

```env
APP_NAME="HelpDesk AI Triage API"
DATABASE_URL="sqlite:///./helpdesk.db"
GEMINI_API_KEY="sua_chave_aqui"
GEMINI_MODEL="gemini-3.8-flash"
GEMINI_TIMEOUT_SECONDS=30
```

**Importante:** obtenha sua chave de API pelo Google AI Studio e mantenha o arquivo `.env` fora do controle de versão.

### 5. Executar a aplicação

```bash
uvicorn app.main:app --reload
```

### Documentação interativa

Após iniciar o servidor, acesse:

| Recurso      | Endereço                                                     |
| ------------ | ------------------------------------------------------------ |
| Swagger UI   | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)     |
| ReDoc        | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)   |
| Health Check | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |

---

## 🧪 Testes Automatizados

O projeto utiliza **Pytest** para validar as operações da API, regras de negócio, tratamento de erros e integração com os serviços.

A suíte de testes utiliza:

- SQLite em memória.
- `StaticPool` para compartilhamento da conexão de teste.
- Fixtures para isolamento e reutilização de dependências.
- Mocks determinísticos para simular respostas do Gemini.
- Testes de validação, CRUD e transições de estado.

Execute a suíte completa:

```bash
pytest -v
```

---

## 📌 Considerações Finais

O HelpDesk AI Triage API foi desenvolvido como projeto de portfólio, com foco em boas práticas de desenvolvimento backend, organização arquitetural, validação de dados, regras de negócio e integração com inteligência artificial.

O projeto demonstra a aplicação de conceitos de engenharia de software em um cenário realista de suporte técnico, utilizando a IA como recurso complementar sem comprometer a integridade e o controle dos dados operacionais.

---

<p align="center">
  <strong>HelpDesk AI Triage API</strong><br>
  Backend • Python • FastAPI • Google Gemini
</p>
