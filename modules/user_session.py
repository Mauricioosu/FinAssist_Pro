import pandas as pd
import json
import chainlit as cl

@cl.on_chat_start
async def start():
    try:
        perfil = json.load(open("perfil_investidor.json"))
        produtos = json.load(open("produtos_financeiros.json"))
        transacoes = pd.read_csv("transacoes.csv")
        
        # Armazenamento em sessão para acesso rápido
        cl.user_session.set("perfil", perfil)
        cl.user_session.set("produtos", produtos)
        cl.user_session.set("transacoes", transacoes)
        
        await cl.Message(content="Sistema FinAssist Pro inicializado com sucesso.").send()
    except Exception as e:
        await cl.Message(content=f"Erro ao carregar base de conhecimento: {e}").send()