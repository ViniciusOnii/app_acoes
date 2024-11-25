import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import datetime

# Configurar a página para exibição horizontal
st.set_page_config(page_title="Análise de Ações", layout="wide")

# Função para calcular MACD
def calcular_macd(df):
    rapidaMME = df['Close'].ewm(span=12).mean()
    lentaMME = df['Close'].ewm(span=26).mean()
    MACD = rapidaMME - lentaMME
    sinal = MACD.ewm(span=9).mean()
    return MACD, sinal

# Função para plotar MACD
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
    fig.update_layout(title=f"Gráfico MACD - {acao}")
    st.plotly_chart(fig)

# Função para plotar gráfico de Candlestick
def plotar_candlestick(df, acao):
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name='Candlestick'
    )])
    fig.update_layout(title=f'Gráfico Candlestick - {acao}', xaxis_title='Data', yaxis_title='Preço')
    st.plotly_chart(fig)

# Função para plotar gráfico de Retorno Diário (%)
def plotar_retorno(df, acao):
    df['Retorno (%)'] = df['Close'].pct_change() * 100
    fig = go.Figure(data=[go.Scatter(
        x=df['Date'],
        y=df['Retorno (%)'],
        mode='lines+markers',
        name='Retorno (%)',
        line=dict(color='orange')
    )])
    fig.update_layout(title=f'Retorno Diário (%) - {acao}', xaxis_title='Data', yaxis_title='Retorno (%)')
    st.plotly_chart(fig)

# Função para indicar se o mercado está aberto ou fechado
def mercado_status():
    agora = datetime.datetime.now()
    abertura = datetime.time(10, 0)  # Horário de abertura: 10:00 AM
    fechamento = datetime.time(17, 0)  # Horário de fechamento: 5:00 PM

    if abertura <= agora.time() <= fechamento:
        st.success("Mercado Aberto")
    else:
        st.warning("Mercado Fechado")

# Função para comparar com o fechamento do dia anterior
def comparar_fechamento(df, acao):
    df['Diferença'] = df['Close'].diff()
    df['Sinal'] = df['Diferença'].apply(lambda x: 'Alta' if x > 0 else 'Baixa' if x < 0 else 'Estável')
    fig = go.Figure(data=[go.Bar(
        x=df['Date'],
        y=df['Diferença'],
        name='Variação',
        marker_color=df['Sinal'].map({'Alta': 'green', 'Baixa': 'red', 'Estável': 'gray'})
    )])
    fig.update_layout(title=f'Variação do Fechamento Diário - {acao}', xaxis_title='Data', yaxis_title='Diferença')
    st.plotly_chart(fig)

# Configurar Streamlit
st.title("Análise de Ações")
st.sidebar.header('Parâmetros')

# Input do usuário
acoes = st.sidebar.text_area('Digite os símbolos das ações separados por vírgula (ex: PETR4.SA, VALE3.SA)', 'PETR4.SA, VALE3.SA')
executar = st.sidebar.button('Executar')

# Seleção de gráficos a serem exibidos
mostrar_macd = st.sidebar.checkbox('Exibir MACD', True)
mostrar_candlestick = st.sidebar.checkbox('Exibir Candlestick', True)
mostrar_retorno = st.sidebar.checkbox('Exibir Retorno Diário (%)', True)
mostrar_comparacao = st.sidebar.checkbox('Exibir Comparação com Fechamento Anterior', True)

# Indicar o status do mercado
mercado_status()

if executar:
    acoes = [acao.strip() for acao in acoes.split(',')]  # Processar os símbolos das ações
    for acao in acoes:
        st.header(f"Análise para {acao}")
        try:
            # Obter dados da ação
            ticker = yf.Ticker(acao)
            df = ticker.history(period='1mo').reset_index()

            # Formatar as colunas para exibição
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d/%m/%Y')  # Formatar a data
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]  # Selecionar colunas relevantes

            # Exibir a tabela no Streamlit
            st.subheader(f"Tabela de valores - {acao}")
            st.dataframe(df, use_container_width=True)

            # Plotar gráficos selecionados
            if mostrar_macd:
                df['MACD'], df['sinal'] = calcular_macd(df)
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
                plotar_macd(df, acao)

            if mostrar_candlestick:
                plotar_candlestick(df, acao)

            if mostrar_retorno:
                plotar_retorno(df, acao)

            if mostrar_comparacao:
                comparar_fechamento(df, acao)

            # Mostrar nome da ação
            info = ticker.info
            nome_acao = info.get('shortName', 'Nome da ação não disponível')
            st.subheader(nome_acao)

        except Exception as e:
            st.error(f"Erro ao processar a ação {acao}: {e}")
