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
            "objetivos_financeiros": os.path.join(self.data_path, "objetivos_financeiros.json")
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

        return data

    def get_relevant_context(self, query: str):
            """Filtra o contexto relevante: Perfil, Metas e Transações."""
            context = []
            
            # Garante que os dados estejam no disco
            try:
                path_metas = os.path.join(self.data_path, "objetivos_financeiros.json")
                if os.path.exists(path_metas):
                    with open(path_metas, 'r', encoding='utf-8') as f:
                        # Atualiza a memória interna antes de ler
                        self.data["objetivos_financeiros"] = json.load(f)
            except Exception as e:
                print(f"Aviso: Não foi possível recarregar metas: {e}")

            # INJEÇÃO DO PERFIL
            perfil = self.data.get("perfil_investidor")
            if perfil:
                nome = perfil.get('nome', 'Usuário')
                tipo = perfil.get('perfil', 'Não definido')
                saldo = perfil.get('saldo_atual', 0.0)
                context.append(f"DADOS DO CLIENTE:\n- Nome: {nome}\n- Perfil: {tipo}\n- Saldo Atual: R$ {saldo:.2f}")

            # INJEÇÃO DE METAS
            metas = self.data.get("objetivos_financeiros", [])
            if metas:
                txt_metas = "OBJETIVOS FINANCEIROS:\n"
                for m in metas:
                    status = m.get('status', 'Em andamento')
                    txt_metas += f"- {m['descricao']}: Alvo R$ {m['valor_alvo']} (Limite: {m.get('data_limite', 'N/A')}) - {status}\n"
                context.append(txt_metas)

            # INJEÇÃO DE TRANSAÇÕES
            keywords_transacoes = ["gasto", "compra", "ganhei", "salário", "extrato", "transação", "pagar", "receber"]
            if any(word in query.lower() for word in keywords_transacoes):
                df = self.data.get("transacoes")
                
                if df is not None and not df.empty:
                    ultimas = df.tail(5).to_string(index=False)
                    context.append(f"ÚLTIMAS TRANSAÇÕES:\n{ultimas}")

            return "\n\n".join(context) if context else "Nenhum contexto financeiro disponível."

    
    def add_transaction(self, descricao, valor, categoria="Geral", prioridade="Média"):
            transacoes_path = os.path.join(self.data_path, "transacoes.csv")
            perfil_path = os.path.join(self.data_path, "perfil_investidor.json")
            
            nova_linha = {
                "data": pd.Timestamp.now().strftime("%d/%m/%Y"),
                "descricao": str(descricao),
                "valor": float(valor),
                "categoria": str(categoria),
                "prioridade": str(prioridade)
            }
            
            try:
                # 1. Carrega ou cria o DataFrame com colunas explícitas
                if os.path.exists(transacoes_path) and os.path.getsize(transacoes_path) > 0:
                    df = pd.read_csv(transacoes_path)
                else:
                    # Se o arquivo não existe ou está vazio, cria com a estrutura correta
                    df = pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'prioridade'])

                # 2. Concatenação segura
                df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                df.to_csv(transacoes_path, index=False)
                
                return True
            except Exception as e:
                print(f"Erro na operação de escrita: {e}")
                return False
            
    def add_goal(self, descricao, valor_alvo, data_limite=None):
        """Grava um novo objetivo financeiro no arquivo JSON."""
        path = os.path.join(self.data_path, "objetivos_financeiros.json")
        
        novo_objetivo = {
            "descricao": descricao,
            "valor_alvo": float(valor_alvo),
            "valor_guardado": 0.0,
            "data_criacao": pd.Timestamp.now().strftime("%d/%m/%Y"),
            "data_limite": data_limite or "Indefinido",
            "status": "Em andamento"
        }
        
        try:
            metas = []
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        metas = json.load(f)
                    except json.JSONDecodeError:
                        metas = []
            
            metas.append(novo_objetivo)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(metas, f, ensure_ascii=False, indent=4)
                
            # Atualiza memória
            self.data["objetivos_financeiros"] = metas
            return True
        except Exception as e:
            print(f"Erro ao salvar meta: {e}")
            return False