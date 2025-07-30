# Arquivo: importador.py (ATUALIZADO PARA ADICIONAR DADOS)

import pandas as pd
import sqlite3
import hashlib

# --- CONFIGURAÇÕES ---
ARQUIVO_CSV = 'extrato.csv' # O script vai procurar este arquivo
BANCO_DE_DADOS = 'financas.db'

def categorizar_transacao(row):
    """
    Categoriza as transações com a lógica de negócio atual.
    """
    desc = row['descricao'].lower()
    valor = row['valor']
    
    if 'launch pad' in desc and valor > 0:
        return 'Receita Bruta'
    if ('karolyne adrielly normanton' in desc or 'fernando henrique dias moreira' in desc) and valor < 0:
        return 'Retirada Sócio (Fernando)'
    if 'jhonatan' in desc and valor < 0:
        return 'Retirada Sócio (Jhonatan)'
    if 'contabilizei' in desc and valor < 0:
        return 'Custo Contábil'
    if 'pix enviado' in desc and valor < 0:
        return 'Despesa Operacional'
    if 'aplicacao' in desc and 'porquinho' in desc and valor < 0:
        return 'Investimento (Aplicação)'
    if 'resgate' in desc and 'porquinho' in desc and valor > 0:
        return 'Investimento (Resgate)'
    if valor > 0:
        return 'Outras Entradas'
    
    return 'Indefinido'

def criar_id_transacao(row):
    """Cria um ID único para cada transação para evitar duplicatas."""
    unique_string = f"{row['data']}{row['descricao']}{row['valor']}"
    return hashlib.sha256(unique_string.encode()).hexdigest()

def carregar_dados_para_banco():
    """
    Lê um novo CSV, compara com os dados existentes e adiciona apenas as novas transações.
    """
    try:
        # Lê e processa o NOVO arquivo CSV
        df_novo = pd.read_csv(ARQUIVO_CSV, delimiter=';', skiprows=5, encoding='utf-8')
        df_novo = df_novo[['Data Lançamento', 'Descrição', 'Valor']]
        df_novo.rename(columns={'Data Lançamento': 'data', 'Descrição': 'descricao', 'Valor': 'valor'}, inplace=True)

        df_novo.dropna(subset=['valor', 'descricao'], inplace=True)
        df_novo['data'] = pd.to_datetime(df_novo['data'], format='%d/%m/%Y')
        if df_novo['valor'].dtype == 'object':
            df_novo['valor'] = df_novo['valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=True).astype(float)
        
        df_novo['categoria'] = df_novo.apply(categorizar_transacao, axis=1)
        df_novo['id'] = df_novo.apply(criar_id_transacao, axis=1)

        # --- LÓGICA DE ATUALIZAÇÃO INTELIGENTE ---
        conexao = sqlite3.connect(BANCO_DE_DADOS)
        cursor = conexao.cursor()
        
        # Garante que a tabela 'transacoes' exista
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id TEXT PRIMARY KEY, data TEXT, descricao TEXT, valor REAL, categoria TEXT
        )
        """)
        
        # Busca os IDs de todas as transações que já estão no banco de dados
        try:
            ids_existentes = pd.read_sql_query("SELECT id FROM transacoes", conexao)['id'].tolist()
        except pd.io.sql.DatabaseError:
            ids_existentes = [] # A tabela existe, mas está vazia

        # Filtra o dataframe, mantendo apenas as transações que NÃO estão no banco
        df_para_adicionar = df_novo[~df_novo['id'].isin(ids_existentes)]
        
        # Adiciona as novas transações ao banco
        if not df_para_adicionar.empty:
            df_para_adicionar.to_sql('transacoes', conexao, if_exists='append', index=False)
            print(f"Sucesso! {len(df_para_adicionar)} nova(s) transação(ões) foram importadas.")
        else:
            print("Nenhuma nova transação encontrada para importar. Seus dados já estão atualizados.")

        conexao.close()

    except FileNotFoundError:
        print(f"Erro: O arquivo '{ARQUIVO_CSV}' não foi encontrado na pasta do projeto.")
    except Exception as e:
        print(f"Ocorreu um erro durante a importação: {e}")

if __name__ == "__main__":
    carregar_dados_para_banco()