import json

class FinancialRetriever:
    def __init__(self, data):
        # Garante que data seja ao menos um dicionário vazio para evitar erros de inicialização
        self.data = data if data is not None else {}

    def get_relevant_context(self, query: str):
        context_parts = []
        query_lower = query.lower()

        # Metas
        if any(word in query_lower for word in ["meta", "objetivo", "viagem", "reserva"]):
            metas = self.data.get('objetivos_financeiros')
            if metas:
                context_parts.append(f"### METAS ATIVAS ###\n{json.dumps(metas, indent=2)}")

        # Transações e Gastos
        if any(word in query_lower for word in ["gasto", "comprar", "extrato", "caro"]):
            transacoes = self.data.get('transacoes')
            if transacoes is not None:
                context_parts.append(f"### ÚLTIMAS TRANSAÇÕES ###\n{transacoes.tail(10).to_csv(index=False)}")

        # Perfil e Produtos
        if any(word in query_lower for word in ["investir", "dinheiro", "aplicar", "rendimento"]):
            perfil = self.data.get('perfil_investidor')
            produtos = self.data.get('produtos_financeiros')
            if perfil:
                context_parts.append(f"### PERFIL DO INVESTIDOR ###\n{json.dumps(perfil, indent=2)}")
            if produtos:
                context_parts.append(f"### PRODUTOS DISPONÍVEIS ###\n{json.dumps(produtos, indent=2)}")

        return "\n\n".join(context_parts) if context_parts else "Forneça uma visão geral baseada no saldo disponível."