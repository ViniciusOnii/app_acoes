import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Configurar a página para exibição horizontal
st.set_page_config(page_title="Análise de Ações", layout="wide")

# Função para calcular MACD
def calcular_macd(df):
    rapidaMME = df['Close'].ewm(span=12).mean()
    lentaMME = df['Close'].ewm(span=26).mean()
    MACD = rapidaMME - lentaMME
    sinal = MACD.ewm(span=9).mean()
    return MACD, sinal


# Função para plotar gráfico
def plotar_macd(df, acao):
    df.index = pd.to_datetime(df['Date'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        name='Preço Fechamento',
        line_color='#FECB52',
        text=df.index.strftime('%d/%m'),
        hovertemplate='%{text}<br>Preço: %{y}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['preço_compra'],
        name='Compra',
        mode='markers',
        marker=dict(color='#00cc96', size=10),
        text=df.index.strftime('%d/%m'),
        hovertemplate='%{text}<br>Preço Compra: %{y}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['preço_venda'],
        name='Venda',
        mode='markers',
        marker=dict(color='#ff4d4d', size=10),
        text=df.index.strftime('%d/%m'),
        hovertemplate='%{text}<br>Preço Venda: %{y}<extra></extra>'
    ))
    st.plotly_chart(fig)

# Configurar Streamlit
st.title("Análise de Ações")
st.sidebar.header('Parâmetros')

# Input do usuário
acao = st.sidebar.text_input('Digite o símbolo da ação (ex: PETR4.SA)', 'PETR4.SA')
analise = st.sidebar.selectbox('Selecione o tipo de análise', ['MACD'])
executar = st.sidebar.button('Executar')

if executar:
    # Obter dados das ações
    ticker = yf.Ticker(acao)
    df = ticker.history(period='1mo').reset_index()

    # Formatar as colunas para exibição
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d/%m/%Y')  # Formatar a data
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]  # Selecionar colunas relevantes

    # Exibir a tabela no Streamlit com mais espaço
    st.subheader(f"Tabela de valores - {acao}")
    st.dataframe(df, use_container_width=True)  # Permitir largura total da página

    # Calcular MACD
    df['MACD'], df['sinal'] = calcular_macd(df)

    # Identificar sinais de compra e venda
    df['flag'] = ''
    df['preço_compra'] = np.nan
    df['preço_venda'] = np.nan

    for i in range(1, len(df)):
        if df['MACD'][i] > df['sinal'][i]:
            if df['flag'][i-1] != 'C':
                df['flag'][i] = 'C'
                df['preço_compra'][i] = df['Close'][i]
            else:
                df['flag'][i] = 'C'
        elif df['MACD'][i] < df['sinal'][i]:
            if df['flag'][i-1] != 'V':
                df['flag'][i] = 'V'
                df['preço_venda'][i] = df['Close'][i]
            else:
                df['flag'][i] = 'V'

    # Plotar gráfico
    plotar_macd(df, acao)

    # Mostrar mensagem final
    ultimo_status = df['flag'].iloc[-1]
    preco_fechamento = round(df['Close'].iloc[-1], 2)
    status_map = {'V': 'VENDA', 'C': 'COMPRA', "": "MANTER"}
    status_texto = status_map.get(ultimo_status, 'INDEFINIDO')
    cor_map = {'VENDA': 'red', 'COMPRA': 'green', 'MANTER': 'yellow'}
    cor = cor_map.get(status_texto, 'black')
    msg = f"{acao}, Operação: <span style='color:{cor}'>{status_texto}</span> - Preço de Fechamento: {preco_fechamento}"

    # Mostrar nome da ação
    info = ticker.info
    nome_acao = info.get('shortName', 'Nome da ação não disponível')
    st.subheader(nome_acao)
    st.markdown(msg, unsafe_allow_html=True)
