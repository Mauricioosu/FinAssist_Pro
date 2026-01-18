import httpx
import openai
import google.generativeai as genai
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, system_prompt: str, user_query: str):
        pass

# MODO LOCAL: OLLAMA (llama3)
class OllamaProvider(LLMProvider):
    def __init__(self, model="llama3:8b"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"
        self.options = {
            "temperature": 0.2, # maior precisão em dados financeiros
            "num_predict": 500  # Limite para respostas diretas e rápidas
        }

    async def generate_response(self, system_prompt, user_query):
        # Implementação de Privacidade Total e Segurança de Dados
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nUsuário: {user_query}",
            "stream": False
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, json=payload, timeout=300.0)
            return response.json().get("response", "Erro ao conectar ao Ollama.")

# MODO NUVEM: GEMINI (Google)
class GeminiProvider(LLMProvider):
    def __init__(self, api_key):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    async def generate_response(self, system_prompt, user_query):
        if not self.model:
            return "Erro: Chave API do Gemini não configurada. Verifique as configurações no navegador."
        
        try:
            full_prompt = f"{system_prompt}\n\nPergunta: {user_query}"
            response = await self.model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            return f"Erro ao processar com Gemini: {str(e)}"

# MODO NUVEM: OPENAI (GPT-4o)
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key):
        self.client = openai.AsyncOpenAI(api_key=api_key) if api_key else None

async def generate_response(self, system_prompt, user_query):
        if not self.client:
            return "Erro: Chave OpenAI não encontrada. Insira-a nas configurações."
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )
        except Exception as e:
            return f"Erro ao processar com OpenAI: {str(e)}"
        return response.choices[0].message.content