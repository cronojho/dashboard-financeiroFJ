# Arquivo: importador_investimentos.py

from ofxparse import OfxParser
import sqlite3
import pandas as pd

# --- CONFIGURAÇÕES ---
ARQUIVO_OFX = 'extrato-movimentacao-renda-fixa.ofx'
BANCO_DE_DADOS = 'financas.db'

def importar_extrato_ofx():
    """
    Lê um arquivo OFX de investimentos, processa os dados e salva em uma
    nova tabela no banco de dados, evitando duplicatas.
    """
    try:
        # Abre e "lê" o arquivo OFX
        with open(ARQUIVO_OFX, 'rb') as fileobj:
            ofx = OfxParser.parse(fileobj)

        # Acessa a conta de investimento dentro do arquivo
        conta_investimento = ofx.account

        # Extrai as transações
        transacoes = conta_investimento.statement.transactions
        
        # Cria uma lista para armazenar os dados processados
        dados_processados = []
        for t in transacoes:
            dados_processados.append({
                'id_transacao': t.id,
                'data': t.date,
                'descricao': t.memo,
                'valor': float(t.amount),
                'tipo': t.type.lower() # ex: 'credit', 'debit'
            })
        
        if not dados_processados:
            print("Nenhuma transação encontrada no arquivo OFX.")
            return

        df_novo = pd.DataFrame(dados_processados)

        # --- LÓGICA DE ATUALIZAÇÃO INTELIGENTE ---
        conexao = sqlite3.connect(BANCO_DE_DADOS)
        cursor = conexao.cursor()
        
        # Cria uma nova tabela para os dados de investimento, se não existir
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes_investimentos (
            id_transacao TEXT PRIMARY KEY,
            data TEXT,
            descricao TEXT,
            valor REAL,
            tipo TEXT
        )
        """)

        # Busca os IDs de todas as transações que já estão no banco
        try:
            ids_existentes = pd.read_sql_query("SELECT id_transacao FROM transacoes_investimentos", conexao)['id_transacao'].tolist()
        except pd.io.sql.DatabaseError:
            ids_existentes = []

        # Filtra para adicionar apenas as transações novas
        df_para_adicionar = df_novo[~df_novo['id_transacao'].isin(ids_existentes)]
        
        if not df_para_adicionar.empty:
            df_para_adicionar.to_sql('transacoes_investimentos', conexao, if_exists='append', index=False)
            print(f"Sucesso! {len(df_para_adicionar)} nova(s) transação(ões) de investimento foram importadas.")
        else:
            print("Nenhuma nova transação de investimento encontrada para importar.")

        conexao.close()

    except FileNotFoundError:
        print(f"Erro: O arquivo '{ARQUIVO_OFX}' não foi encontrado na pasta do projeto.")
    except Exception as e:
        print(f"Ocorreu um erro durante a importação do OFX: {e}")

if __name__ == "__main__":
    importar_extrato_ofx()