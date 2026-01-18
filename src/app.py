import os
import json
import pandas as pd
import chainlit as cl
from chainlit.input_widget import Select, TextInput
from modules.orchestrator import FinAssistOrchestrator

DATA_PATH = "../data/"

# --- FUNÇÕES DE APOIO ---

async def ensure_data_directory():
    """Garante que a pasta de dados exista para persistência local."""
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

def load_json(filename):
    """Carrega arquivos JSON com suporte a caracteres especiais."""
    path = os.path.join(DATA_PATH, filename)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Erro ao carregar JSON {filename}: {e}")
        return None

def load_csv(filename):
    """Carrega CSV como DataFrame para permitir cálculos matemáticos."""
    path = os.path.join(DATA_PATH, filename)
    try:
        if os.path.exists(path):
            return pd.read_csv(path)
        return None
    except Exception as e:
        print(f"Erro ao carregar CSV {filename}: {e}")
        return None

async def run_onboarding():
    await cl.Message(content="👋 Olá! Sou o FinAssist Pro. Vamos configurar sua base financeira.").send()
    
    # Coleta Nome
    res_nome = await cl.AskUserMessage(content="Qual é o seu nome?", timeout=120).send()

    if res_nome is None:
        await cl.Message(content="⚠️ O tempo de resposta expirou. Reinicie o chat para configurar.").send()
        return

    nome_usuario = res_nome.get('output', "Usuário")

    # Coleta Perfil com Validação
    perfil_escolhido = None
    opcoes_validas = ["conservador", "moderado", "arrojado"]
    
    while not perfil_escolhido:
        res_perfil = await cl.AskUserMessage(
            content=f"{nome_usuario}, qual seu perfil de investidor? (Conservador, Moderado ou Arrojado). Se não souber a diferença, pode me perguntar!", 
            timeout=90
        ).send()
        
        resposta = res_perfil['output'].lower().strip()
        
        if resposta in opcoes_validas:
            perfil_escolhido = resposta.capitalize()
        else:
            # resposta inválida, o bot explica
            await cl.Message(content=(
                "💡 **Dica do FinAssist Pro:**\n"
                "- **Conservador:** Prioriza segurança e quer evitar perdas a todo custo.\n"
                "- **Moderado:** Aceita um pouco de risco para ganhar mais que a poupança.\n"
                "- **Arrojado:** Foca em longo prazo e aceita oscilações para buscar altos retornos."
            )).send()
    
    # Coleta Saldo
    saldo_final = 0.0
    while True:
        res_saldo = await cl.AskUserMessage(content="Qual seu saldo atual em conta? (Ex: 1250.00)", timeout=60).send()
        try:
            saldo_final = float(res_saldo['output'].replace(',', '.'))
            break
        except ValueError:
            await cl.Message(content="⚠️ Por favor, digite apenas números para o saldo.").send()

    # Salva os dados validados
    perfil_data = {
        "nome": nome_usuario,
        "perfil": perfil_escolhido,
        "saldo_atual": saldo_final
    }
    
    with open(f"{DATA_PATH}perfil_investidor.json", "w", encoding='utf-8') as f:
        json.dump(perfil_data, f, ensure_ascii=False, indent=4)
    
    # Inicializa arquivos restantes
    pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'prioridade']).to_csv(f"{DATA_PATH}transacoes.csv", index=False)
    with open(f"{DATA_PATH}objetivos_financeiros.json", "w", encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

    await cl.Message(content=f"✅ Tudo pronto, **{nome_usuario}**! Perfil **{perfil_escolhido}** configurado.").send()
    
# --- FLUXO PRINCIPAL DO CHAINLIT ---

@cl.on_chat_start
async def start():
    await ensure_data_directory() # Garante a pasta
    
    # Validação de existência de dados reais
    perfil_path = os.path.join(DATA_PATH, "perfil_investidor.json")
    
    if not os.path.exists(perfil_path):
        await run_onboarding()
    
    data = {
        "perfil_investidor": load_json("perfil_investidor.json"),
        "produtos_financeiros": load_json("produtos_financeiros.json") or [],
        "transacoes": load_csv("transacoes.csv"),
        "objetivos_financeiros": load_json("objetivos_financeiros.json") or []
    }
    
    cl.user_session.set("financial_data", data)
    
    orchestrator = FinAssistOrchestrator(mode="local")
    cl.user_session.set("orchestrator", orchestrator)
    
    await cl.Message(content=f"Bem-vindo de volta, {data['perfil_investidor']['nome']}!").send()

@cl.on_settings_update
async def setup_agent(settings):
    """Atualiza o provedor de IA dinamicamente pelo navegador."""
    mode = settings["ModelMode"]
    api_key = settings["GeminiKey"] if mode == "gemini" else settings["OpenAIKey"]

    orchestrator = FinAssistOrchestrator(mode=mode, api_key=api_key)
    cl.user_session.set("orchestrator", orchestrator)
    
    await cl.Message(content=f"⚙️ Sistema atualizado para o modo: **{mode.upper()}**").send()

@cl.on_message
async def main(message: cl.Message):
    """Processamento de mensagens com RAG."""
    orchestrator = cl.user_session.get("orchestrator")
    
    if not orchestrator:
        await cl.Message(content="Erro: Orquestrador não inicializado.").send()
        return

    response = await orchestrator.run(message.content)
    await cl.Message(content=response).send()