import os
import chainlit as cl
from abc import ABC, abstractmethod
import pandas as pd
import json
from modules.retriever import FinancialRetriever
from modules.providers import OllamaProvider, OpenAIProvider, GeminiProvider

class FinAssistOrchestrator:
    def __init__(self, mode="local", data=None,api_key=None): 
        self.mode = mode
        self.api_key = api_key
        self.data = data # Armazena a "Base de Verdade"
        self.provider = self._get_provider()
        
        self.retriever = FinancialRetriever(data=self.data)
        
        self.system_prompt_base = """
        Você é o FinAssist Pro, um mentor financeiro inteligente, ético e educativo. 
        Seu objetivo é ajudar os usuários a organizarem suas finanças e entenderem o mercado financeiro de forma didática.

        DIRETRIZES DE COMPORTAMENTO:
        1. BASE DE VERDADE: Use exclusivamente os dados fornecidos no contexto (Transações, Produtos, Metas e Perfil) para responder.
        2. PRECISÃO MATEMÁTICA: Ao realizar cálculos, descreva a fórmula utilizada.
        3. TOM DE VOZ: Seja consultivo, encorajador e profissional.
        4. SEGURANÇA: Nunca solicite ou aceite senhas e dados sensíveis.
        """

    def _get_provider(self):
        """Seleciona o provedor de LLM baseado no modo (Local vs Cloud)."""
        if self.mode == "local":
            return OllamaProvider()
        elif self.mode == "gemini":
            return GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))
        return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, user_query: str):
        """Executa o fluxo principal: RAG + LLM."""
        context = self.retriever.get_relevant_context(user_query)
        
        full_system_prompt = f"{self.system_prompt_base}\n\n### CONTEXTO DE VERDADE ###\n{context}"
        
        return await self.provider.generate_response(full_system_prompt, user_query)
    
class LLMFactory:
    @staticmethod
    def get_model(mode="online"):
        if mode == "offline":
            # Configuração para Ollama + llama3
            return "ollama/llama3"
        else:
            # Configuração para GPT-4o ou Gemini 1.5 Pro
            return "openai/gpt-4o"

# Uso no fluxo do Orquestrador
model_choice = LLMFactory.get_model(mode="online")