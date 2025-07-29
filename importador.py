# Arquivo: importador.py (ATUALIZADO)

import pandas as pd
import sqlite3
import hashlib

# --- CONFIGURAÇÕES ---
ARQUIVO_CSV = 'extrato.csv'
BANCO_DE_DADOS = 'financas.db'

def categorizar_transacao(row):
    """
    Categoriza as transações com a nova lógica de retirada de sócios.
    """
    desc = row['descricao'].lower()
    valor = row['valor']
    
    # 1. Receitas
    if 'launch pad' in desc and valor > 0:
        return 'Receita Bruta'
        
    # 2. Retirada de Sócios
    if ('karolyne adrielly normanton' in desc or 'fernando henrique dias moreira' in desc) and valor < 0:
        return 'Retirada Sócio (Fernando)'
    # --- ALTERAÇÃO APLICADA AQUI ---
    if 'jhonatan' in desc and valor < 0:
        return 'Retirada Sócio (Jhonatan)'

    # 3. Custos e Despesas Operacionais
    if 'contabilizei' in desc and valor < 0:
        return 'Custo Contábil'
    if 'pix enviado' in desc and valor < 0:
        return 'Despesa Operacional'
        
    # 4. Investimentos
    if 'aplicacao' in desc and 'porquinho' in desc and valor < 0:
        return 'Investimento (Aplicação)'
    if 'resgate' in desc and 'porquinho' in desc and valor > 0:
        return 'Investimento (Resgate)'

    # 5. Outras Entradas
    if valor > 0:
        return 'Outras Entradas'
    
    return 'Indefinido'

def criar_id_transacao(row):
    """Cria um ID único para cada transação."""
    unique_string = f"{row['data']}{row['descricao']}{row['valor']}"
    return hashlib.sha256(unique_string.encode()).hexdigest()

def carregar_dados_para_banco():
    """Lê, categoriza e salva os dados no banco de dados SQLite."""
    try:
        df = pd.read_csv(ARQUIVO_CSV, delimiter=';', skiprows=5, encoding='utf-8')
        df = df[['Data Lançamento', 'Descrição', 'Valor']]
        df.rename(columns={'Data Lançamento': 'data', 'Descrição': 'descricao', 'Valor': 'valor'}, inplace=True)

        df.dropna(subset=['valor', 'descricao'], inplace=True)
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        if df['valor'].dtype == 'object':
            df['valor'] = df['valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=True).astype(float)
        
        df['categoria'] = df.apply(categorizar_transacao, axis=1)
        df['id'] = df.apply(criar_id_transacao, axis=1)

        conexao = sqlite3.connect(BANCO_DE_DADOS)
        df.to_sql('transacoes', conexao, if_exists='replace', index=False)
        print(f"Banco de dados da empresa recriado com sucesso! {len(df)} transações foram categorizadas.")
        conexao.close()

    except FileNotFoundError:
        print(f"Erro: O arquivo '{ARQUIVO_CSV}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    carregar_dados_para_banco()