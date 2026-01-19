import os
import json
import pandas as pd


class FinancialRetriever:
    def __init__(self, data=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.abspath(os.path.join(current_dir, "..", "..", "data"))
        self.data = data if data else self._load_all_data()

    def _load_all_data(self):
        """Carrega a base de verdade de forma robusta e absoluta."""
        data = {}
        paths = {
            "perfil_investidor": os.path.join(self.data_path, "perfil_investidor.json"),
            "transacoes": os.path.join(self.data_path, "transacoes.csv"),
            "objetivos_financeiros": os.path.join(self.data_path, "objetivos_financeiros.json"),
            "produtos_financeiros": os.path.join(self.data_path, "produtos_financeiros.json")
        }

        # Carregar Perfil
        if os.path.exists(paths["perfil_investidor"]):
            try:
                with open(paths["perfil_investidor"], 'r', encoding='utf-8') as f:
                    data["perfil_investidor"] = json.load(f)
            except Exception as e:
                print(f"Erro ao ler perfil: {e}")

        # Carregar Transações
        if os.path.exists(paths["transacoes"]):
            try:
                data["transacoes"] = pd.read_csv(paths["transacoes"])
            except Exception as e:
                print(f"Erro ao ler transações: {e}")
                data["transacoes"] = pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'prioridade'])
        else:
            data["transacoes"] = pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'prioridade'])

        # Carregar Metas
        if os.path.exists(paths["objetivos_financeiros"]):
            try:
                with open(paths["objetivos_financeiros"], 'r', encoding='utf-8') as f:
                    data["objetivos_financeiros"] = json.load(f)
            except Exception:
                data["objetivos_financeiros"] = []
        else:
            data["objetivos_financeiros"] = []
        # Carregar Produtos (Somente Leitura)
        if os.path.exists(paths["produtos_financeiros"]):
            try:
                with open(paths["produtos_financeiros"], 'r', encoding='utf-8') as f:
                    data["produtos_financeiros"] = json.load(f)
            except Exception:
                data["produtos_financeiros"] = []
        else:
            data["produtos_financeiros"] = []

        return data

    def _save_csv(self, df):
        path = os.path.join(self.data_path, "transacoes.csv")
        df.to_csv(path, index=False)
        self.data["transacoes"] = df

    def _save_goals(self, goals_list):
        path = os.path.join(self.data_path, "objetivos_financeiros.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(goals_list, f, ensure_ascii=False, indent=4)
        self.data["objetivos_financeiros"] = goals_list

    def _update_balance_file(self, valor_delta):
        path = os.path.join(self.data_path, "perfil_investidor.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                perfil = json.load(f)
            perfil["saldo_atual"] = perfil.get("saldo_atual", 0.0) + valor_delta
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(perfil, f, ensure_ascii=False, indent=4)
            if "perfil_investidor" in self.data:
                self.data["perfil_investidor"]["saldo_atual"] = perfil["saldo_atual"]

    def get_relevant_context(self, query: str):
        context = []
        self.data["objetivos_financeiros"] = self._load_all_data().get("objetivos_financeiros", [])

        perfil = self.data.get("perfil_investidor")
        if perfil:
            nome = perfil.get('nome', 'Usuário')
            saldo = perfil.get('saldo_atual', 0.0)
            context.append(f"DADOS DO CLIENTE:\n- Nome: {nome}\n- Saldo Atual: R$ {saldo:.2f}")

        metas = self.data.get("objetivos_financeiros", [])
        if metas:
            txt_metas = "OBJETIVOS FINANCEIROS (Use o ID para alterar/excluir):\n"
            for idx, m in enumerate(metas):
                status = m.get('status', 'Em andamento')
                txt_metas += f"[ID: {idx}] {m['descricao']}: Alvo R$ {m['valor_alvo']} - {status}\n"
            context.append(txt_metas)

        # Contexto de Investimentos
        keywords_invest = ["investir", "rendimento", "aplicar", "onde colocar", "recomendação", "cdb", "tesouro"]
        if any(k in query.lower() for k in keywords_invest):
            produtos = self.data.get("produtos_financeiros", [])
            if produtos:
                txt_prod = "PRODUTOS FINANCEIROS DISPONÍVEIS (Apenas Leitura):\n"
                for p in produtos:
                    txt_prod += f"- {p.get('nome')} ({p.get('tipo')}): Rentabilidade {p.get('rentabilidade')} | Risco {p.get('risco')}\n"
                context.append(txt_prod)

        # Contexto de Transações (CRUD)
        keywords_crud = ["editar", "mudar", "alterar", "corrigir", "gasto", "compra", "ganhei", "transação", "remover", "deletar"]
        if any(word in query.lower() for word in keywords_crud):
            df = self.data.get("transacoes")
            if df is not None and not df.empty:
                ultimas = df.tail(8).reset_index()
                txt_transacoes = "ÚLTIMAS TRANSAÇÕES (Use o ID para editar/excluir):\n"
                txt_transacoes += ultimas[['index', 'data', 'descricao', 'valor', 'categoria']].to_string(index=False)
                context.append(txt_transacoes)

        return "\n\n".join(context) if context else "Nenhum contexto financeiro disponível."

    # --- CRUD OPERATIONS ---

    def add_transaction(self, descricao, valor, categoria="Geral", prioridade="Média"):
        df = self.data.get("transacoes")
        if df is None:
            df = pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'prioridade'])

        nova_linha = {
            "data": pd.Timestamp.now().strftime("%d/%m/%Y"),
            "descricao": str(descricao),
            "valor": float(valor),
            "categoria": str(categoria),
            "prioridade": str(prioridade)
        }
        try:
            # Concatenação segura
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
            self._save_csv(df)
            self._update_balance_file(float(valor))
            print(f"DEBUG: Transação salva com sucesso! Novo total de linhas: {len(df)}")
            return True
        except Exception as e:
            print(f"Erro CRÍTICO no add_transaction: {e}")
            return False

    def update_transaction(self, idx, **kwargs):
        df = self.data.get("transacoes")
        if df is None or df.empty:
            return False
        try:
            idx = int(idx)
            if idx not in df.index:
                return False
            valor_antigo = df.loc[idx, 'valor']
            novo_valor = kwargs.get('valor', valor_antigo)
            for key, val in kwargs.items():
                if key in df.columns:
                    df.at[idx, key] = val

            self._save_csv(df)
            if novo_valor != valor_antigo:
                delta = float(novo_valor) - float(valor_antigo)
                self._update_balance_file(delta)
            return True
        except Exception as e:
            print(f"Erro UPDATE Transacao: {e}")
            return False

    def delete_transaction(self, transaction_index):
        df = self.data.get("transacoes")
        if df is None or df.empty:
            return False
        try:
            idx = int(transaction_index)
            if idx in df.index:
                valor_removido = df.loc[idx, 'valor']
                df = df.drop(idx)
                self._save_csv(df)
                self._update_balance_file(-valor_removido)
                return True
        except Exception as e:
            print(f"Erro DELETE: {e}")
        return False

    def add_goal(self, descricao, valor_alvo, data_limite=None):
        metas = self.data.get("objetivos_financeiros", [])
        novo_objetivo = {
            "descricao": descricao,
            "valor_alvo": float(valor_alvo),
            "valor_guardado": 0.0,
            "data_criacao": pd.Timestamp.now().strftime("%d/%m/%Y"),
            "data_limite": data_limite or "Indefinido",
            "status": "Em andamento"
        }
        metas.append(novo_objetivo)
        self._save_goals(metas)
        return True

    def update_goal(self, idx, **kwargs):
        metas = self.data.get("objetivos_financeiros", [])
        try:
            idx = int(idx)
            if 0 <= idx < len(metas):
                meta = metas[idx]
                for key, val in kwargs.items():
                    if key in meta:
                        meta[key] = val
                metas[idx] = meta
                self._save_goals(metas)
                return True
        except Exception as e:
            print(f"Erro UPDATE Meta: {e}")
        return False

    def delete_goal(self, goal_index):
        metas = self.data.get("objetivos_financeiros", [])
        try:
            idx = int(goal_index)
            if 0 <= idx < len(metas):
                metas.pop(idx)
                self._save_goals(metas)
                return True
        except Exception as e:
            print(f"Erro DELETE Meta: {e}")
        return False
