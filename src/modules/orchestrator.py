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

        ### DIRETRIZES DE COMPORTAMENTO ###
        1. Você é um sistema híbrido: Metade Consultor, Metade Banco de Dados.
        2. Se o usuário informar um valor numérico associado a uma ação (compra, venda, recebimento, gasto), você É OBRIGADO a registrar isso
        3. BASE DE VERDADE: Use exclusivamente os dados fornecidos no contexto (Transações, Produtos, Metas e Perfil) para responder.
        4. PRECISÃO MATEMÁTICA: Ao realizar cálculos, descreva a fórmula utilizada. Se o cálculo for complexo, sugira que é uma simulação educacional.
        5. TOM DE VOZ: Seja consultivo, encorajador e profissional. Evite termos técnicos sem explicá-los brevemente.
        6. SEGURANÇA: Nunca solicite ou aceite senhas e dados sensíveis. Reforce que você não substitui um consultor humano certificado.

        REGRAS DE RESPOSTA:
        - Se o usuário pedir um conselho sobre um gasto específico, analise o impacto dele na Meta Financeira.
        - Se o usuário perguntar sobre investimentos, verifique primeiro o 'Perfil de Investidor' no contexto.
        - Se a informação não estiver na base de conhecimento, diga: "Não tenho esses dados específicos no momento, mas com base nos conceitos financeiros gerais, posso te explicar que..."

        ### COMANDOS DE BANCO DE DADOS (USO OBRIGATÓRIO) ###
        Sempre que identificar uma transação ou meta, use estas tags IMEDIATAMENTE. Não peça confirmação.
        1. PARA REGISTRAR (SAVE):
           - Gasto (Valor Negativo): #SAVE_TRANSACAO#{"descricao": "Uber", "valor": -25.00, "categoria": "Transporte"}#SAVE_TRANSACAO#
           - Ganho (Valor Positivo): #SAVE_TRANSACAO#{"descricao": "Venda Notebook", "valor": 1500.00, "categoria": "Vendas"}#SAVE_TRANSACAO#
           - Nova Meta: #SAVE_META#{"descricao": "Carro Novo", "valor": 50000.00}#SAVE_META#
        2. PARA EDITAR (UPDATE):
           - Use o ID visível no contexto (ex: [ID: 5]).
           - Ex: #UPDATE_TRANSACAO#{"id": 5, "valor": -30.00}#UPDATE_TRANSACAO#
        3. PARA EXCLUIR (DELETE):
           - Ex: #DELETE_TRANSACAO#{"id": 12}#DELETE_TRANSACAO#

        ### GATILHOS DE EXECUÇÃO (ATENÇÃO MÁXIMA) ###
        - Se o usuário disser: "Gastei X", "Recebi Y", "Comprei Z", "Vendi W".
        - AÇÃO: Gere a tag #SAVE_TRANSACAO#... silenciosamente no meio da sua resposta.
        - ERRO COMUM: Não diga apenas "Entendido, anotei". Você deve GERAR O COMANDO JSON.

        CONTEXTO DO USUÁRIO:
        """

    def _get_provider(self):
        if self.mode == "local":
            return OllamaProvider()
        elif self.mode == "gemini":
            return GeminiProvider(api_key=self.api_key)
        elif self.mode == "openai":
            return OpenAIProvider(api_key=self.api_key)
        return OllamaProvider()

    async def run(self, user_query: str):
        context = self.retriever.get_relevant_context(user_query)
        full_system_prompt = f"{self.system_prompt_base}\n\n{context}"
        # Gera a resposta com a IA
        response = await self.provider.generate_response(full_system_prompt, user_query)
        # Lista de comandos monitorados
        commands = {
            "#SAVE_TRANSACAO#": self._save_transaction_action,
            "#SAVE_META#": self._save_goal_action,
            "#UPDATE_TRANSACAO#": self._update_transaction_action,
            "#UPDATE_META#": self._update_goal_action,
            "#DELETE_TRANSACAO#": self._delete_transaction_action,
            "#DELETE_META#": self._delete_goal_action,
            "#SAVE#": self._save_transaction_action
        }

        # Verifica se alguma tag está presente na resposta
        for tag, func in commands.items():
            if tag in response:
                print(f"DEBUG: Comando detectado: {tag}")
                return self._handle_action(response, tag, func)

        return response

    def _handle_action(self, response, tag, action_func):
        """Smart Parser Blindado."""
        try:
            parts = response.split(tag)
            # Procura por um JSON válido entre as tags
            for i in range(1, len(parts)):
                candidate = parts[i].strip()
                if len(candidate) < 2:
                    continue
                candidate_clean = self._clean_json_text(candidate)
                try:
                    data_dict = json.loads(candidate_clean)
                    msg_sistema = action_func(data_dict)
                    # Reconstrói a mensagem visual para o usuário
                    pre = tag.join(parts[:i]).strip()
                    post = tag.join(parts[i+1:]).strip()
                    return f"{pre}\n\n_{msg_sistema}_\n\n{post}".strip()
                except json.JSONDecodeError:
                    continue
            return response
        except Exception as e:
            return f"{response}\n\n❌ Erro técnico: {str(e)}"

    def _clean_json_text(self, text):
        return text.replace("```json", "").replace("```", "").replace("'", '"').strip()

    def _safe_float(self, value):
        if isinstance(value, (float, int)):
            return float(value)
        try:
            return float(str(value).replace("R$", "").replace(" ", "").replace(",", "."))
        except ValueError:
            return 0.0

    # HANDLERS DE AÇÕES

    def _save_transaction_action(self, data):
        desc = data.get("descricao") or "Sem nome"
        val = self._safe_float(data.get("valor", 0))
        cat = data.get("categoria", "Geral")
        if self.retriever.add_transaction(desc, val, cat):
            return "✅ Saldo atualizado!"
        return "❌ Erro ao salvar."

    def _save_goal_action(self, data):
        val = self._safe_float(data.get("valor") or data.get("valor_alvo"))
        if self.retriever.add_goal(data.get("descricao"), val, data.get("data_limite")):
            return "🎯 Meta criada!"
        return "❌ Erro ao criar meta."

    def _update_transaction_action(self, data):
        idx = data.pop("id", None)
        if "valor" in data:
            data["valor"] = self._safe_float(data["valor"])
        if idx is not None and self.retriever.update_transaction(idx, **data):
            return f"📝 Transação {idx} editada."
        return "❌ Erro ao editar."

    def _update_goal_action(self, data):
        idx = data.pop("id", None)
        if "valor" in data:
            data["valor"] = self._safe_float(data["valor"])
        if idx is not None and self.retriever.update_goal(idx, **data):
            return f"📝 Meta {idx} editada."
        return "❌ Erro ao editar."

    def _delete_transaction_action(self, data):
        if self.retriever.delete_transaction(data.get("id")):
            return "🗑️ Transação apagada."
        return "❌ Erro ao apagar."

    def _delete_goal_action(self, data):
        if self.retriever.delete_goal(data.get("id")):
            return "🗑️ Meta apagada."
        return "❌ Erro ao apagar."
