import os
import json
from modules.retriever import FinancialRetriever
from modules.providers import OllamaProvider, OpenAIProvider, GeminiProvider

class FinAssistOrchestrator:
    def __init__(self, mode="local", data=None, api_key=None): 
        self.mode = mode
        self.api_key = api_key
        self.data = data 
        self.provider = self._get_provider()
        self.retriever = FinancialRetriever(data=self.data)
        
        # PROMPT BASE
        self.system_prompt_base = """
                Você é o FinAssist Pro, um mentor financeiro inteligente.

                DIRETRIZES GERAIS:
                1. BASE DE VERDADE: Use SOMENTE os dados do contexto (Perfil, Metas, Transações).
                2. SEGURANÇA: Não peça senhas.
                3. DADOS: NUNCA invente dados financeiros para completar o contexto se necessário pergunte os dados que precise.
                4. NÃO realiza transações bancárias ou movimentações de dinheiro.
                5. NÃO solicita senhas, tokens ou dados sensíveis (LGPD Compliance).
                6. As cotações de mercado no modo offline dependem da última atualização da base de conhecimento fornecida.
                7. NÃO fornece recomendações personalizadas de compra/venda de ações específicas.
                8. Não substitui um consultor financeiro certificado (CFA/CNPI)
                
                ### REGRA MESTRA DE REGISTROS (LEITURA VS ESCRITA) ###
                
                CASO 1: LEITURA (O usuário pergunta saldo, extrato ou metas)
                - Apenas responda a pergunta com base no contexto.
                - PROIBIDO usar a tag #SAVE# neste caso.
                
                CASO 2: ESCRITA (O usuário pede para CRIAR, ADICIONAR ou REGISTRAR algo novo)
                - Identifique se é TRANSAÇÃO ou META.
                - OBRIGATORIAMENTE use o formato JSON no final:

                A) Se for Gasto/Ganho:
                #SAVE#{"tipo": "transacao", "descricao": "Item", "valor": -100.00, "categoria": "Lazer"}#SAVE#
                (Lembre-se: Gastos são negativos, Ganhos positivos)

                B) Se for Nova Meta:
                #SAVE#{"tipo": "meta", "descricao": "Nome da Meta", "valor": 5000.00, "data_limite": "Dez/2026"}#SAVE#
                
                IMPORTANTE: Nunca use #SAVE# se o valor for desconhecido ou null.

                
        """

    def _get_provider(self):
        if self.mode == "local": return OllamaProvider()
        elif self.mode == "gemini": return GeminiProvider(api_key=self.api_key)
        elif self.mode == "openai": return OpenAIProvider(api_key=self.api_key)
        return OllamaProvider()

    async def run(self, user_query: str):
        context = self.retriever.get_relevant_context(user_query)
        full_system_prompt = f"{self.system_prompt_base}\n\n### CONTEXTO ###\n{context}"
        
        response = await self.provider.generate_response(full_system_prompt, user_query)
        
        # LÓGICA DE ROTEAMENTO
        if "#SAVE#" in response:
            try:
                clean_response = response.split("#SAVE#")[0].strip()
                json_str = response.split("#SAVE#")[1]
                data_to_save = json.loads(json_str)
                
                tipo_acao = data_to_save.get("tipo")
                sucesso = False
            
                if tipo_acao == "transacao":
                    sucesso = self.retriever.add_transaction(
                        descricao=data_to_save["descricao"],
                        valor=data_to_save["valor"],
                        categoria=data_to_save.get("categoria", "Geral")
                    )
                    msg_confirmacao = "\n\n✅ *Transação registrada e saldo atualizado!*"
                
                elif tipo_acao == "meta":
                    sucesso = self.retriever.add_goal(
                        descricao=data_to_save["descricao"],
                        valor_alvo=data_to_save["valor"],
                        data_limite=data_to_save.get("data_limite")
                    )
                    msg_confirmacao = "\n\n🎯 *Nova meta definida com sucesso!*"

                if sucesso:
                    return f"{clean_response}{msg_confirmacao}"
                else:
                    return f"{clean_response}\n\n❌ *Erro ao salvar no disco.*"

            except Exception as e:
                print(f"Erro no Router de salvamento: {e}")
        
        return response