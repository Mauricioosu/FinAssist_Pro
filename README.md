# FinAssist Pro - Seu Mentor Financeiro com IA

![Status](https://img.shields.io/badge/Status-Concluído-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

# ⚠️ PROJETO DESCONTINUADO

> **ATENÇÃO:** Este repositório representa uma versão legada (v1) e **não está mais sendo mantida**.

O projeto evoluiu para uma arquitetura completa de Agente de IA Financeiro, focado em privacidade e performance.

## 🚀 Acesse a Nova Versão: FinAssist Pro 2.0

🔗 **[CLIQUE AQUI PARA VER O PROJETO ATUAL (V2)](https://github.com/Mauricioosu/FinAssist_Pro_2)**

O **FinAssist Pro** é um assistente financeiro inteligente que utiliza **RAG (Retrieval-Augmented Generation)** para fornecer consultoria personalizada. Diferente de chatbots comuns, ele possui **memória persistente** e capacidade de **agir** sobre os dados, registrando transações e metas financeiras em arquivos locais.

## Funcionalidades Principais

* **💬 Chat Consultivo:** Tire dúvidas sobre investimentos, economia e planejamento.
* **📝 Registro Automático:** Diga *"Gastei 50 no almoço"* e ele salvará no CSV e atualizará seu saldo.
* **🎯 Gestão de Metas:** Diga *"Quero juntar 5 mil para viajar"* e ele criará um plano de metas no JSON.
* **🔒 Privacidade Total:** Roda 100% local (via Ollama) ou híbrido (via API Gemini), mantendo seus dados financeiros na sua máquina.
* **📊 Análise de Perfil:** As respostas são adaptadas ao seu perfil de investidor (Conservador, Moderado, Arrojado).

##  Tecnologias Utilizadas

* **Python 3:** Linguagem base.
* **Chainlit:** Interface de chat moderna e responsiva.
* **LangChain / Logic:** Orquestração de prompts e contexto.
* **Ollama (Llama 3):** Inteligência Artificial local (Offline).
* **Google Gemini:** Inteligência Artificial em nuvem (Opcional).
* **Pandas:** Manipulação de dados (CSV/JSON).


## Como Rodar o Projeto
Pré-requisitos

    Python 3.10 ou superior

    Ollama instalado (para modo local)

### Passo a passo

 1. Clone o repositorio:
```bash
git clone [https://github.com/Mauricioosu/FinAssist_Pro.git](https://github.com/Mauricioosu/FinAssist_Pro.git)
cd FinAssist_Pro
```

 2. Crie o ambiente virtual e instale as depencias:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

 3. Baixe o modelo de IA (Para local):
```bash
ollama pull llama3
```
 4. execute o assistente:
```bash
chainlit run src/app.py -w
```

## Exemplos de Uso

1. Registrando um Gasto:

    Usuário: "Paguei 120 reais na conta de luz."

    FinAssist: "Entendido! Registrei o gasto de R$ 120,00 na categoria 'Utilidades'. Seu saldo foi atualizado."

2. Criando uma Meta:

    Usuário: "Quero criar uma meta de comprar um notebook gamer, valor 5000."

    FinAssist: "Ótimo objetivo! Meta 'Comprar Notebook Gamer' criada com sucesso. Vamos planejar como chegar lá!"

3. Consultoria:

    Usuário: "Com meu saldo atual, qual a melhor forma de investir para curto prazo?"

    FinAssist: (Analisa seu saldo no JSON e seu perfil) "Considerando seu perfil Moderado e o saldo de R$ X..."
