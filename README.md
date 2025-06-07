
# Gerenciador Financeiro Pessoal com Agente de IA 

Um projeto que demonstra a construção de um **Agente de Inteligência Artificial** para **Gestão Financeira Pessoal**, utilizando **IA Generativa e Serverless**(ADK, MCP, Gemini, Cloud Run)
. Este sistema permite a interação conversacional para listar, registrar, analisar finanças e receber dicas.

---

## Estrutura do Projeto

Este repositório principal, `ai-agent-finance/`, contém duas pastas-filhas que compõem a arquitetura do agente financeiro:

1.  **`agente-financeiro -> finance_agent/`**: Contém o código do **Agente de IA** desenvolvido com o **Google Agent Development Kit (ADK)**. Este agente usa Gemini pra processar as interações do usuário, interpretar intenções e orquestrar as chamadas para as ferramentas financeiras, além prover dicas.
2.  **`mcp_server/`**: Contém o código do **Model Context Protocol (MCP) Server** implementado com **FastMCP**. Este servidor atua como uma ponte para expor funcionalidades da sua API de backend (`list_expenses_by_user`, `create_expense`) ao Agente de IA.

---

## Tecnologias Utilizadas

* **Google Agent Development Kit (ADK)**: Framework para o desenvolvimento de agentes de IA.
* **FastMCP (Model Context Protocol)**: Biblioteca Python para construir MCP, facilitando a integração e criação de ferramentas, além do uso de transports inerentes ao protocolo.
* **Google Gemini (API / Modelo `gemini-2.0-flash`)**: O modelo de linguagem grande (LLM) que impulsiona as capacidades generativas do agente.
* **Google Cloud Run**: Plataforma de computação serverless que hospeda o Agente de IA e o MCP Server.
* **Python**: Linguagem de programação principal para o desenvolvimento de ambos os componentes.
* **httpx**: Biblioteca HTTP assíncrona utilizada pelo FastMCP para interagir com a API de backend de finanças.
* **API RESTful de Finanças (Backend)**: Um serviço externo (neste caso, hospedado no Render e com o Banco de Dados no MongoDB) que gerencia os dados de despesas e entradas.

---

## Technical Workflow

O sistema opera através da seguinte sequência:

1.  O **Agente de IA** (de `finance_agent/`) recebe a entrada do usuário, tipicamente via ADK Dev UI.
2.  Utilizando **Prompt Engineering** em sua configuração, o modelo **Google Gemini** interpreta a intenção do usuário.
3.  Se uma ação financeira é requerida (ex: listar ou criar uma despesa), o Agente de IA invoca a ferramenta apropriada exposta pelo **MCP Server**.
4.  O **MCP Server** (de `mcp_server/`) processa esta requisição, realiza validações de entrada e faz a chamada correspondente à API RESTful de finanças.
5.  A resposta da API é tratada pelo MCP Server e retransmitida ao Agente de IA(pelo transport neste caso do tipo streamable HTTPs).
6.  O Agente de IA então formata esta informação em uma resposta de linguagem natural para o usuário ou, em caso de erro, comunica o problema com base em suas instruções de sistema.

---

## Configuração e Deploy

Para colocar o projeto em funcionamento no Google Cloud Run, siga os passos abaixo.

### Pré-requisitos

* **Conta Google Cloud:** Com faturamento ativado.
* **Google Cloud SDK (gcloud CLI):** Instalado e configurado.
* **Docker:** Instalado (necessário para construir a imagem do MCP Server).
* **Sua API de Backend de Finanças:** Deve estar deployada e acessível.

### 1. Autenticação e Configuração do Projeto Google Cloud

Primeiro, autentique o `gcloud CLI` e defina seu projeto padrão:

```bash
gcloud auth login
gcloud config set project your-gcp-project-id
gcloud config set run/region us-central1 # Ou sua região preferida, ex: southamerica-east1
```

---

## Projeto MCP Server (`mcp_server/`)

### 1. Preparar o Dockerfile

Crie um arquivo chamado `Dockerfile` na pasta `mcp_server/` com o seguinte conteúdo:

```dockerfile
# Usa uma imagem base Python oficial leve
FROM python:3.10-slim-buster

# Define o diretório de trabalho no container
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da sua aplicação
COPY . .

# Expõe a porta que o FastMCP usará (8080 por padrão, exigido pelo Cloud Run)
EXPOSE 8080

# Comando para iniciar o servidor FastMCP
# FORÇAR HOST '0.0.0.0' É CRUCIAL PARA O CLOUD RUN
# A variável de ambiente PORT será injetada automaticamente pelo Cloud Run 
# Isso será feito direto no run do server
CMD ["python", "my_server.py"]
```

Crie um arquivo `requirements.txt` na pasta `mcp_server/` com as dependências:

```
fastmcp
httpx
```

### 2. Deploy do MCP Server

Na pasta `mcp_server/`, execute os seguintes comandos:

```bash
# Define o nome do serviço
export MCP_SERVICE_NAME="meu-mcp" # Nome do seu serviço Cloud Run
export GCP_PROJECT_ID="your-gcp-project-id" # Substitua pelo seu ID de projeto

# Deployar para o Cloud Run usando a flag --source
# O Cloud Run construirá a imagem Docker automaticamente a partir do Dockerfile na pasta atual.
# A opção --allow-unauthenticated é necessária para que o ADK consiga acessá-lo.
# A variável de ambiente PORT será injetada automaticamente pelo Cloud Run e usada pelo seu código.
gcloud run deploy ${MCP_SERVICE_NAME} \
  --source=. \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --project=${GCP_PROJECT_ID} \
  --region=${GOOGLE_CLOUD_LOCATION}

```

Após o deploy, o Cloud Run fornecerá uma **URL do serviço**. Anote-a, pois ela será usada na configuração do seu agente ADK. A URL terá um formato similar a `https://meu-mcp-XXXX.REGION.run.app`. Você deverá obrigatoriamente incluir o path **/mcp/** quando for integrar.

---

## Projeto Agente de IA (`finance_agent/`)

### 1. Preparar Variáveis de Ambiente e Configuração do Agente

Na pasta  (`finance_agent/`), configure os 3 principais arquivos.

```bash
# Navegue para a pasta raiz do projeto se ainda não estiver nela
cd /path/to/your/agente-financeiro

# Seu ID de projeto do Google Cloud
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

# Região onde seus serviços serão deployados (deve ser a mesma do MCP Server)
export GOOGLE_CLOUD_LOCATION="us-central1" # Ou sua região preferida

# Informa ao ADK para usar a Gemini API via Vertex AI
export GOOGLE_GENAI_USE_VERTEXAI=True

# O caminho para o diretório do seu agente ADK
export AGENT_PATH="./finance_agent"

# Nome do serviço Cloud Run para o seu agente
export AGENT_SERVICE_NAME="finance-assistant-agent"

# O ID do usuário fixo para o agente
export FINANCE_AGENT_USER_ID="seu-id" # Substitua pelo seu ID de usuário
```

**Importante:** No seu arquivo `finance_agent/agent.py`, o `USER_ID` deve ser carregado via ambiente. A URL do MCP Toolset está fixada no código conforme sua instrução.

```python
# finance_agent/agent.py (trecho relevante)
import os
from dotenv import load_dotenv # Importar para uso local

# Carrega as variáveis do arquivo .env (apenas para desenvolvimento local)
# Comenta ou remove esta linha se não estiver usando .env localmente
load_dotenv()

# Carrega o USER_ID de uma variável de ambiente
USER_ID = os.environ.get("FINANCE_AGENT_USER_ID")

# ... (restante do código do agente)

    tools=[
        MCPToolset(
            connection_params=StreamableHTTPServerParams(
                url="https://seulinkdocloudrun/mcp/" # URL do MCP fixada
            ),
        )
    ],
# ...
```

### 2. Deploy do Agente ADK

Use o comando `adk deploy cloud_run`. O ADK CLI irá conteinerizar e deployar seu agente.

```bash
# Deploy com a UI de desenvolvimento (recomendado para testes)
# A variável de ambiente FINANCE_AGENT_USER_ID será injetada para a instância do agente no Cloud Run.
adk deploy cloud_run \
  --project=${GOOGLE_CLOUD_PROJECT} \
  --region=${GOOGLE_CLOUD_LOCATION} \
  --service_name=${AGENT_SERVICE_NAME} \
  --with_ui \
  --set-env-vars="FINANCE_AGENT_USER_ID=${FINANCE_AGENT_USER_ID}" \
  ${AGENT_PATH}
```

Após o deploy, o Cloud Run fornecerá uma URL para a interface de desenvolvimento do seu agente. Acesse essa URL no seu navegador para interagir com o agente.

---

## Desenvolvimento Local

Para executar o agente localmente, você pode usar um arquivo `.env` para gerenciar as variáveis de ambiente sem a necessidade de exportá-las manualmente no terminal a cada sessão.

1.  **Instale `python-dotenv`**:
    ```bash
    pip install python-dotenv
    ```
2.  **Crie um arquivo `.env` na pasta `finance_agent/`**:

    ```
    # finance_agent/.env
    FINANCE_AGENT_USER_ID="seu-user"
    # Note: MCP_SERVER_URL não precisa estar aqui se estiver fixado no agent.py para uso local.
    # Adicione outras variáveis de ambiente necessárias para o desenvolvimento local,
    # API Key e VertexAI.
    ```
    **Importante:** Adicione `.env` ao seu `.gitignore` para evitar o commit de informações sensíveis.

3.  **No seu `finance_agent/agent.py`**, certifique-se de que `from dotenv import load_dotenv` e `load_dotenv()` estejam no início do arquivo, como mostrado na seção "Preparar Variáveis de Ambiente e Configuração do Agente" acima.

4.  **Para executar localmente:**
    ```bash
    cd finance_agent/
    adk web
    ```
    Acesse `http://localhost:8000` no seu navegador.

---

## Uso

Uma vez que o Agente de IA e o MCP Server estejam deployados e funcionando, você pode interagir com o agente através da ADK Dev UI.

**Exemplos de Interação:**

* "Hi"
* "Can you list my finances?"
* "I received an extra 500 dollars today."
* "I spent 45 dollars on internet this month."
* "What tips do you have for saving money?"
