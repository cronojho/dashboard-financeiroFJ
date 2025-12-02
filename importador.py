# Arquivo: importador.py (ATUALIZADO E CORRIGIDO)

import pandas as pd
import sqlite3
import hashlib

# --- CONFIGURAÇÕES ---
ARQUIVO_CSV = 'extrato.csv'
BANCO_DE_DADOS = 'financas.db'

def categorizar_transacao(row):
    """
    Categoriza as transações com a lógica correta, sem a categoria 'Movimentação Interna'.
    """
    desc = row['descricao'].lower()
    valor = row['valor']
    
    # 1. Regra de Estorno (PRIORIDADE MÁXIMA)
    if 'estorno' in desc:
        return 'Estorno'
        
    # 2. Receitas
    if 'launch pad' in desc and valor > 0:
        return 'Receita Bruta'
        
    # 3. Retirada de Sócios
    if ('karolyne adrielly normanton' in desc or 'fernando henrique dias moreira' in desc) and valor < 0:
        return 'Retirada Sócio (Fernando)'
    if 'jhonatan' in desc and valor < 0:
        return 'Retirada Sócio (Jhonatan)'

    # 4. Custos e Despesas Operacionais
    if 'contabilizei' in desc and valor < 0:
        return 'Custo Contábil'
    # Esta regra precisa vir DEPOIS das retiradas e investimentos para não classificar tudo como despesa
    if 'pix enviado' in desc and valor < 0:
        return 'Despesa Operacional'
        
    # 5. Investimentos
    if 'aplicacao' in desc and 'porquinho' in desc or 'cdb' in desc and valor < 0:
        return 'Investimento (Aplicação)'
    if 'resgate' in desc and 'porquinho' in desc or 'cdb' in desc and valor > 0:
        return 'Investimento (Resgate)'

    # 6. Outras Entradas
    if valor > 0:
        return 'Outras Entradas'
    
    return 'Indefinido'

def criar_id_transacao(row):
    unique_string = f"{row['data']}{row['descricao']}{row['valor']}"
    return hashlib.sha256(unique_string.encode()).hexdigest()

def carregar_dados_para_banco():
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
        try:
            cursor = conexao.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS transacoes (id TEXT PRIMARY KEY, data TEXT, descricao TEXT, valor REAL, categoria TEXT)""")
            ids_existentes = pd.read_sql_query("SELECT id FROM transacoes", conexao)['id'].tolist()
            df_para_adicionar = df[~df['id'].isin(ids_existentes)]
        except:
            df_para_adicionar = df
        
        if not df_para_adicionar.empty:
            df_para_adicionar.to_sql('transacoes', conexao, if_exists='append', index=False)
            print(f"Sucesso! {len(df_para_adicionar)} transação(ões) foram importadas com a categorização correta.")
        else:
            print("Nenhuma nova transação encontrada para importar.")
        conexao.close()
    except FileNotFoundError:
        print(f"Erro: O arquivo '{ARQUIVO_CSV}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    carregar_dados_para_banco()