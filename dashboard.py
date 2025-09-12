# Arquivo: dashboard.py (ATUALIZADO E SIMPLIFICADO)

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- FUNÇÃO DE VERIFICAÇÃO DE SENHA ---
def check_password():
    """Retorna True se a senha estiver correta, False caso contrário."""
    
    # Usa st.secrets para buscar as senhas de forma segura
    correct_password_fernando = st.secrets["passwords"]["fernando"]
    correct_password_jhonatan = st.secrets["passwords"]["jhonatan"]

    # Pede a senha para o usuário
    password = st.text_input("Digite a senha para acessar:", type="password")

    # Verifica se a senha digitada corresponde a alguma das senhas corretas
    if password == correct_password_fernando or password == correct_password_jhonatan:
        return True
    elif password: # Se o usuário digitou algo, mas está incorreto
        st.error("Senha incorreta. Por favor, tente novamente.")
        return False
    else: # Se o campo de senha está vazio
        return False

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Dashboard da Empresa", layout="wide")

# Chamada da função de senha para proteger o acesso ao dashboard
if not check_password():
    st.stop()  # Para a execução do app se a senha estiver incorreta ou não for inserida

# --- FUNÇÃO PARA CARREGAR OS DADOS ---
@st.cache_data
def carregar_dados():
    try:
        conexao = sqlite3.connect('financas.db')
        df = pd.read_sql_query("SELECT * FROM transacoes", conexao, parse_dates=['data'])
        conexao.close()
        df['data'] = df['data'].dt.tz_localize(None)
        return df
    except Exception as e:
        return pd.DataFrame()

# --- CARREGAR DADOS ---
df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado. Apague financas.db e execute o importador.py primeiro.")
else:
    st.title("Dashboard Financeiro da Empresa 📈")
    st.markdown("---")

    # --- BARRA LATERAL ---
    st.sidebar.header("Filtros de Data")
    min_date = df['data'].min()
    max_date = df['data'].max()
    tipo_filtro = st.sidebar.radio( "Como você quer filtrar o período?", ["Tudo", "Seleção Rápida por Mês", "Período Customizado"])
    
    if tipo_filtro == "Tudo":
        df_filtrado = df.copy()
        periodo_texto = "Todo o Período"
    elif tipo_filtro == "Seleção Rápida por Mês":
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
        ano_selecionado = st.sidebar.selectbox("Ano", anos_disponiveis)
        meses_disponiveis = sorted(df[df['ano'] == ano_selecionado]['mes'].unique())
        mes_selecionado = st.sidebar.selectbox("Mês", meses_disponiveis, format_func=lambda x: f'{x:02d}')
        df_filtrado = df[(df['ano'] == ano_selecionado) & (df['mes'] == mes_selecionado)].copy()
        periodo_texto = f"{mes_selecionado:02d}/{ano_selecionado}"
    else: # Período Customizado
        data_inicio = st.sidebar.date_input('Data de Início', min_date, min_value=min_date, max_value=max_date)
        data_fim = st.sidebar.date_input('Data de Fim', max_date, min_value=min_date, max_value=max_date)
        if data_inicio > data_fim:
            st.sidebar.error('Erro: A data de início não pode ser posterior à data de fim.')
            df_filtrado = pd.DataFrame()
        else:
            start_datetime = pd.to_datetime(data_inicio)
            end_datetime = pd.to_datetime(data_fim)
            df_filtrado = df[(df['data'] >= start_datetime) & (df['data'] <= end_datetime)].copy()
            periodo_texto = f"de {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"

    # --- ANÁLISE DO PERÍODO FILTRADO ---
    if df_filtrado.empty:
        st.info(f"Nenhuma transação encontrada para o período selecionado.")
    else:
        # Cria um DataFrame para os cálculos de PERFORMANCE, ignorando o que não deve ser contado.
        categorias_para_ignorar = ['Movimentação Interna', 'Estorno']
        df_performance = df_filtrado[~df_filtrado['categoria'].isin(categorias_para_ignorar)]

        # --- CÁLCULOS DE PERFORMANCE ---
        receita_bruta = df_performance[df_performance['categoria'] == 'Receita Bruta']['valor'].sum()
        custos_df = df_performance[df_performance['categoria'].isin(['Custo Contábil', 'Despesa Operacional'])]
        total_custos_operacionais = abs(custos_df['valor'].sum())
        lucro_operacional = receita_bruta - total_custos_operacionais
        
        # --- QUADRO: DEMONSTRATIVO DE RESULTADOS ---
        st.header(f"Demonstrativo de Resultados ({periodo_texto})")
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Receita Bruta", f"R$ {receita_bruta:,.2f}")
        col2.metric("💳 Custos Operacionais", f"R$ {total_custos_operacionais:,.2f}")
        col3.metric("📊 Lucro Operacional", f"R$ {lucro_operacional:,.2f}")
        st.markdown("---")

        # --- QUADRO: DISTRIBUIÇÃO DE LUCRO AOS SÓCIOS ---
        st.header(f"Distribuição de Lucro aos Sócios ({periodo_texto})")
        df_fernando = df_performance[df_performance['categoria'] == 'Retirada Sócio (Fernando)']
        retirada_fernando = abs(df_fernando['valor'].sum())
        contagem_fernando = len(df_fernando)
        percentual_fernando = (retirada_fernando / lucro_operacional * 100) if lucro_operacional > 0 else 0
        df_jhonatan = df_performance[df_performance['categoria'] == 'Retirada Sócio (Jhonatan)']
        retirada_jhonatan = abs(df_jhonatan['valor'].sum())
        contagem_jhonatan = len(df_jhonatan)
        percentual_jhonatan = (retirada_jhonatan / lucro_operacional * 100) if lucro_operacional > 0 else 0
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("Sócio: Fernando H. D. Moreira")
            st.metric("Valor Total Retirado", f"R$ {retirada_fernando:,.2f}")
            st.metric("Quantidade de Retiradas", f"{contagem_fernando} transação(ões)")
            st.metric("% sobre o Lucro Operacional", f"{percentual_fernando:.2f}%")
        with col_s2:
            st.subheader("Sócio: Jhonatan W. Gonzales")
            st.metric("Valor Total Retirado", f"R$ {retirada_jhonatan:,.2f}")
            st.metric("Quantidade de Retiradas", f"{contagem_jhonatan} transação(ões)")
            st.metric("% sobre o Lucro Operacional", f"{percentual_jhonatan:.2f}%")
        st.markdown("---")

        # --- QUADRO: SALDOS DE CAIXA E INVESTIMENTOS ---
        st.header(f"Saldos de Caixa e Investimentos ({periodo_texto})")
        
        # Cálculo do Saldo do Porquinho (Líquido e Positivo)
        df_porquinho = df_filtrado[df_filtrado['descricao'].str.contains("CDB PORQUINHO", case=False)]
        saldo_porquinho_liquido = df_porquinho['valor'].sum()
        saldo_porquinho_positivo = saldo_porquinho_liquido * -1
        
        # Saldo final da conta
        saldo_conta = df_filtrado['valor'].sum()

        col_saldos1, col_saldos2 = st.columns(2)
        col_saldos1.metric("🐷 Saldo Porquinho (Líquido)", f"R$ {saldo_porquinho_positivo:,.2f}")
        col_saldos2.metric("🏦 Saldo Final em Conta", f"R$ {saldo_conta:,.2f}")
        
        st.markdown("---")

        # --- TABELA DE TRANSAÇÕES ---
        st.subheader("Extrato Detalhado do Período")
        st.dataframe(
            df_filtrado[['data', 'descricao', 'valor', 'categoria']].sort_values('data', ascending=False),
            use_container_width=True,
            column_config={ "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f") }
        )