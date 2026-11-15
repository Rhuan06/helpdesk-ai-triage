
# HelpDesk AI Triage

## Sistema Inteligente de Triagem de Chamados de Suporte Técnico

**Projeto de Engenharia de Software com Inteligência Artificial**

---

## 1. Visão Geral

O HelpDesk AI Triage é um sistema inteligente de gerenciamento e triagem de chamados de suporte técnico, utilizando Inteligência Artificial Generativa para interpretar incidentes, identificar categorias, classificar prioridades e sugerir procedimentos de resolução.

O objetivo é desenvolver uma aplicação backend profissional, utilizando Python, FastAPI e integração com a Gemini API.

O projeto será desenvolvido progressivamente, seguindo boas práticas de Engenharia de Software, organização arquitetural, validação de dados, testes automatizados e documentação técnica.

### Objetivos principais

- Receber chamados escritos em linguagem natural.
- Identificar automaticamente a categoria do incidente.
- Classificar a prioridade do chamado.
- Gerar resumos técnicos.
- Identificar possíveis causas dos problemas.
- Sugerir procedimentos de resolução.
- Armazenar os chamados em banco de dados.
- Permitir consultar, atualizar e acompanhar chamados.

---

## 2. Stack Tecnológica

| Tecnologia | Responsabilidade |
|---|---|
| Python 3.12+ | Linguagem principal |
| FastAPI | Construção da API REST |
| Pydantic | Validação e estruturação de dados |
| SQLAlchemy | ORM e persistência |
| SQLite | Banco de dados inicial |
| Gemini API | Inteligência Artificial Generativa |
| Pytest | Testes automatizados |
| HTTPX | Testes da API |
| Git | Controle de versão |
| GitHub | Hospedagem do projeto |

### Justificativa tecnológica

O SQLite será utilizado inicialmente por ser leve e suficiente para o MVP.

O PostgreSQL poderá ser introduzido em uma evolução futura.

A aplicação será desenvolvida inicialmente como backend, sem adicionar frontend desnecessariamente.

---

## 3. Funcionalidades do Sistema

### 3.1. Gerenciamento de chamados

- Criar chamados.
- Listar chamados.
- Consultar chamado individualmente.
- Atualizar informações.
- Alterar status.
- Excluir chamados.

### 3.2. Análise inteligente

A integração com Gemini deverá:

1. Interpretar a descrição do incidente.
2. Identificar a categoria.
3. Determinar a prioridade sugerida.
4. Produzir um resumo técnico.
5. Identificar possíveis causas.
6. Sugerir procedimentos de resolução.

### 3.3. Categorias iniciais

- Hardware.
- Software.
- Rede.
- Sistemas operacionais.
- Impressoras e periféricos.
- Acesso e autenticação.
- Outros.

### 3.4. Níveis de prioridade

- Baixa.
- Média.
- Alta.
- Crítica.

### 3.5. Status dos chamados

- Aberto.
- Em análise.
- Em atendimento.
- Resolvido.
- Fechado.

A classificação produzida pela IA será uma sugestão e deverá passar por validação das regras de negócio.

---

## 4. Arquitetura da Aplicação

A aplicação utilizará uma arquitetura em camadas, separando responsabilidades.

```text
                 CLIENTE / USUÁRIO
                         |
                         v
                    FASTAPI REST
                         |
                +--------+--------+
                |                 |
                v                 v
          TICKET SERVICE      AI SERVICE
                |                 |
                |                 v
                |             GEMINI API
                |                 |
                |<----------------+
                |
                v
             SQLALCHEMY
                |
                v
               SQLITE
```

### Responsabilidades

**API Layer**
- Receber requisições HTTP.
- Validar entradas.
- Retornar respostas.

**Service Layer**
- Implementar regras de negócio.
- Gerenciar operações dos chamados.
- Coordenar a análise com IA.

**AI Service**
- Integrar com Gemini.
- Gerenciar prompts.
- Interpretar respostas.
- Tratar erros da integração.

**Database Layer**
- Configurar conexão.
- Gerenciar sessões.
- Persistir informações.

---

## 5. Estrutura de Diretórios

Estrutura planejada para o projeto:

```text
helpdesk-ai-triage/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── tickets.py
│   │
│   ├── models/
│   │   └── ticket.py
│   │
│   ├── schemas/
│   │   └── ticket.py
│   │
│   ├── services/
│   │   ├── ai_classifier.py
│   │   └── ticket_service.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   └── prompts/
│       └── ticket_analysis.py
│
├── tests/
│   ├── test_tickets.py
│   └── test_ai_classifier.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── PLANO_DO_PROJETO.md
```

A estrutura será criada progressivamente, conforme as necessidades de cada etapa.

---

## 6. Etapas de Desenvolvimento

### ETAPA 1 — Inicialização

Objetivo: preparar o ambiente e criar a aplicação inicial.

Atividades:

- Criar repositório no GitHub.
- Criar projeto no Cursor.
- Configurar ambiente virtual Python.
- Instalar dependências.
- Criar estrutura inicial.
- Implementar aplicação FastAPI.
- Configurar variáveis de ambiente.
- Criar endpoint GET `/api/v1/health`.
- Criar `.gitignore`.

Entrega esperada:

API inicial funcionando e ambiente configurado.

### ETAPA 2 — Modelagem e Banco de Dados

Objetivo: estruturar os chamados e implementar persistência.

Atividades:

- Criar entidade Ticket.
- Definir campos e tipos.
- Criar enums de categoria, prioridade e status.
- Configurar SQLAlchemy.
- Configurar SQLite.
- Implementar operações básicas de persistência.

Entrega esperada:

Chamados armazenados corretamente no banco de dados.

### ETAPA 3 — API REST

Objetivo: implementar os endpoints de gerenciamento.

Endpoints planejados:

| Método | Endpoint | Responsabilidade |
|---|---|---|
| POST | /api/v1/tickets | Criar chamado |
| GET | /api/v1/tickets | Listar chamados |
| GET | /api/v1/tickets/{ticket_id} | Consultar chamado |
| PATCH | /api/v1/tickets/{ticket_id} | Atualizar chamado |
| DELETE | /api/v1/tickets/{ticket_id} | Excluir chamado |

Entrega esperada:

API REST funcional para gerenciamento dos chamados.

### ETAPA 4 — Integração com Gemini

Objetivo: implementar inteligência artificial para análise dos incidentes.

Atividades:

- Configurar cliente Gemini.
- Criar serviço de integração.
- Desenvolver prompts estruturados.
- Implementar classificação inteligente.
- Gerar resumo técnico.
- Identificar possíveis causas.
- Sugerir procedimentos de resolução.
- Validar respostas com Pydantic.
- Tratar erros e timeouts.

Entrega esperada:

Sistema capaz de analisar chamados utilizando IA.

### ETAPA 5 — Regras de Negócio

Objetivo: garantir consistência nas operações.

Atividades:

- Definir transições válidas de status.
- Validar categorias e prioridades.
- Separar análise da IA das decisões do sistema.
- Registrar resultados das análises.
- Tratar inconsistências.

Entrega esperada:

Fluxo de gerenciamento de chamados consistente.

### ETAPA 6 — Testes Automatizados

Objetivo: verificar a qualidade e confiabilidade da aplicação.

Atividades:

- Testar endpoints.
- Testar validações Pydantic.
- Testar regras de negócio.
- Testar persistência.
- Simular respostas do Gemini utilizando mocks.
- Testar falhas de integração.

Ferramentas:

- Pytest.
- HTTPX.
- unittest.mock ou pytest-mock.

Entrega esperada:

Suíte de testes automatizados funcionando.

### ETAPA 7 — Qualidade e Segurança

Objetivo: preparar a aplicação para apresentação profissional.

Atividades:

- Revisar tratamento de exceções.
- Proteger credenciais da API.
- Evitar exposição de dados sensíveis.
- Revisar logs.
- Validar respostas externas.
- Revisar documentação OpenAPI.
- Verificar configurações de ambiente.

Entrega esperada:

Aplicação revisada, documentada e consistente.

### ETAPA 8 — GitHub e Documentação

Objetivo: publicar o projeto no GitHub.

Atividades:

- Criar README profissional.
- Documentar arquitetura.
- Adicionar diagrama do sistema.
- Documentar instalação.
- Documentar endpoints.
- Adicionar exemplos de requisições.
- Registrar tecnologias utilizadas.
- Organizar histórico de commits.

Entrega esperada:

Projeto publicado e pronto para apresentação em entrevistas técnicas.

---

## 7. Metodologia de Desenvolvimento

O projeto será desenvolvido com apoio de três ferramentas e participação ativa do desenvolvedor.

### Você — Desenvolvedor

Responsabilidades:

- Tomar decisões técnicas.
- Implementar as funcionalidades.
- Executar os testes.
- Entender o código.
- Revisar sugestões das ferramentas.
- Realizar commits.

### Gemini — Orientação de Implementação

Responsabilidades:

- Ajudar a planejar funcionalidades.
- Sugerir implementações.
- Explicar conceitos.
- Auxiliar na identificação de erros.
- Orientar o desenvolvimento dentro do Cursor.

### Cursor — Ambiente de Desenvolvimento

Responsabilidades:

- Editar arquivos.
- Auxiliar na implementação.
- Executar comandos.
- Analisar código.
- Ajudar na correção de problemas.

### ChatGPT — Revisão Técnica

Responsabilidades:

- Revisar arquitetura.
- Analisar código.
- Identificar problemas técnicos.
- Verificar boas práticas.
- Corrigir implementações.
- Explicar conceitos.
- Avaliar segurança.
- Revisar decisões arquiteturais.

### Fluxo de trabalho

1. Definir o objetivo da etapa.
2. Solicitar ao Gemini um planejamento.
3. Implementar no Cursor.
4. Executar a aplicação e os testes.
5. Enviar o código e os resultados ao ChatGPT.
6. Realizar revisão técnica.
7. Aplicar correções.
8. Registrar commit.
9. Avançar para a próxima etapa.

Regra fundamental:

Não aceitar automaticamente todo código gerado por IA. Cada implementação deverá ser compreendida, revisada e testada.

---

## 8. Padrão de Versionamento Git

Será utilizado o padrão Conventional Commits.

Exemplos:

```bash
feat: cria estrutura inicial da aplicação

feat(db): implementa persistência de chamados

feat(api): adiciona endpoints de chamados

feat(ai): integra classificação com Gemini

feat(core): implementa regras de negócio

test: adiciona testes automatizados

docs: documenta instalação e arquitetura

fix: corrige validação de chamados
```

### Arquivos que não devem ser enviados ao GitHub

- `.env`
- `venv/`
- `__pycache__/`
- `.pytest_cache/`
- Arquivos temporários.
- Banco de desenvolvimento local, salvo se houver uma razão documentada para versioná-lo.

O arquivo `.env.example` deverá conter apenas nomes de variáveis e valores fictícios.

---

## 9. Evoluções Futuras

As funcionalidades abaixo não fazem parte do MVP inicial.

Poderão ser implementadas posteriormente:

| Tecnologia | Evolução |
|---|---|
| PostgreSQL | Banco de dados mais robusto |
| React / Next.js | Interface web |
| Docker | Containerização |
| Redis | Cache e processamento assíncrono |
| JWT | Autenticação e autorização |
| RAG | Base de conhecimento técnico |
| MLOps | Monitoramento e avaliação de modelos |
| Dashboard | Indicadores e métricas |

Essas evoluções deverão ser implementadas somente quando houver necessidade técnica.

---

## 10. Critérios de Conclusão

O MVP será considerado concluído quando:

- [ ] Ambiente configurado.
- [ ] API FastAPI funcionando.
- [ ] Modelagem dos chamados implementada.
- [ ] Banco SQLite funcionando.
- [ ] Endpoints REST implementados.
- [ ] Integração real com Gemini funcionando.
- [ ] Classificação inteligente implementada.
- [ ] Validação das respostas da IA.
- [ ] Regras de negócio implementadas.
- [ ] Testes automatizados funcionando.
- [ ] Tratamento de exceções implementado.
- [ ] Segurança das credenciais revisada.
- [ ] README profissional.
- [ ] Documentação técnica.
- [ ] Repositório público no GitHub.

---

## 11. Primeiro Prompt — Iniciar no Cursor

Utilizar este prompt com o Gemini para iniciar a primeira etapa.

```text
Estou iniciando um projeto chamado HelpDesk AI Triage,
um sistema inteligente de triagem de chamados de suporte
técnico.

O projeto utilizará:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Gemini API
- Pytest

Quero desenvolver o projeto progressivamente, seguindo
boas práticas de Engenharia de Software.

Nesta primeira etapa, quero apenas:

1. Analisar os requisitos iniciais.
2. Definir as dependências necessárias.
3. Configurar o ambiente virtual Python.
4. Criar a estrutura inicial mínima.
5. Implementar uma aplicação FastAPI funcional.
6. Configurar variáveis de ambiente utilizando
   python-dotenv.
7. Criar um endpoint GET /api/v1/health.
8. Criar um .gitignore adequado.

Não implemente ainda integração com Gemini,
banco de dados ou funcionalidades de chamados.

Antes de escrever qualquer código, apresente
o planejamento técnico e explique as decisões
arquiteturais.

Não invente funcionalidades e não crie arquivos
desnecessários.

Quero entender cada implementação.
```

---

## 12. Diretrizes Gerais

1. Desenvolver uma etapa por vez.
2. Não antecipar funcionalidades sem necessidade.
3. Evitar complexidade desnecessária.
4. Priorizar código legível e organizado.
5. Utilizar tipagem sempre que apropriado.
6. Validar entradas e saídas.
7. Tratar falhas de integração.
8. Manter documentação atualizada.
9. Escrever testes para as funcionalidades.
10. Compreender o código antes de avançar.

---

## 13. Objetivo Profissional

O HelpDesk AI Triage será desenvolvido como projeto de portfólio, com foco em demonstrar conhecimentos práticos em:

- Engenharia de Software.
- Desenvolvimento Backend com Python.
- Construção de APIs REST.
- Integração com Inteligência Artificial Generativa.
- Engenharia de Prompts.
- Validação de dados.
- Persistência de dados.
- Testes automatizados.
- Arquitetura de aplicações.
- Versionamento e documentação.

O objetivo não é apenas construir um sistema que utiliza IA, mas demonstrar capacidade de projetar, implementar, testar e documentar uma aplicação de software que incorpora Inteligência Artificial de maneira estruturada.

---

**Projeto:** HelpDesk AI Triage  
**Área:** Engenharia de Software com Inteligência Artificial  
**Linguagem principal:** Python  
**Backend:** FastAPI  
**Modelo de IA:** Gemini  
**Status:** Planejamento definido — aguardando início da Etapa 1.
