import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import datetime
import requests
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Baixar o lexicon para VADER
nltk.download('vader_lexicon')

# Configurar a página para exibição horizontal
st.set_page_config(page_title="Análise de Ações", layout="wide")

# Configuração da API de Notícias
NEWS_API_KEY = "b8cce54e5db84a9f9579dbe7c04ada74"  # Substitua pela sua chave da API

# Função para calcular MACD
def calcular_macd(df):
    rapidaMME = df['Close'].ewm(span=12).mean()
    lentaMME = df['Close'].ewm(span=26).mean()
    MACD = rapidaMME - lentaMME
    sinal = MACD.ewm(span=9).mean()
    return MACD, sinal

# Função para buscar notícias relacionadas à ação
def buscar_noticias(acao):
    """Obtém notícias recentes relacionadas à ação."""
    url = f"https://newsapi.org/v2/everything?q={acao}&apiKey={NEWS_API_KEY}&language=pt"
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        return dados.get("articles", [])
    else:
        st.error("Erro ao buscar notícias.")
        return []

# Função para analisar o sentimento de textos
def analisar_sentimento(texto, metodo="TextBlob"):
    """Analisa o sentimento de um texto."""
    if metodo == "TextBlob":
        sentimento = TextBlob(texto).sentiment.polarity
    else:
        sid = SentimentIntensityAnalyzer()
        sentimento = sid.polarity_scores(texto)['compound']
    
    if sentimento > 0.1:
        return "Positivo", sentimento
    elif sentimento < -0.1:
        return "Negativo", sentimento
    else:
        return "Neutro", sentimento

# Função para exibir notícias e análise de sentimento
def exibir_noticias(acao):
    st.subheader(f"Notícias Recentes - {acao}")
    noticias = buscar_noticias(acao)
    if noticias:
        for noticia in noticias[:5]:  # Limitar a 5 notícias
            titulo = noticia.get("title", "Sem título")
            descricao = noticia.get("description", "Sem descrição")
            url = noticia.get("url", "#")
            
            sentimento, pontuacao = analisar_sentimento(titulo)
            
            st.write(f"**Título**: {titulo}")
            st.write(f"Descrição: {descricao}")
            st.write(f"Sentimento: {sentimento} (Pontuação: {pontuacao:.2f})")
            st.write(f"[Leia mais]({url})")
            st.write("---")
    else:
        st.info("Sem notícias recentes.")

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

# Função para exibir tabela de dados
def plotar_tabela(df, acao):
    """
    Exibe uma tabela formatada no Streamlit com os dados do DataFrame, incluindo a coluna Média.
    """
    # Cálculo da média entre High, Low e Close
    df['Média'] = df[['High', 'Low', 'Close']].mean(axis=1)
    
    # Formatar título e exibição
    st.subheader(f"Tabela de Dados - {acao}")
    
    # Exibir a tabela no Streamlit
    st.dataframe(df, use_container_width=True)


# Função para indicar se o mercado está aberto ou fechado
def mercado_status():
    agora = datetime.datetime.now()
    abertura = datetime.time(10, 0)
    fechamento = datetime.time(17, 0)

    if abertura <= agora.time() <= fechamento:
        st.success("Mercado Aberto")
    else:
        st.warning("Mercado Fechado")
    

# Configurar Streamlit
st.title("Análise de Ações")
st.sidebar.header('Parâmetros')

# Input do usuário
acoes = st.sidebar.text_area('Digite os símbolos das ações separados por vírgula (ex: PETR4.SA, VALE3.SA)', 'PETR4.SA, VALE3.SA')
executar = st.sidebar.button('Executar')

# Seleção de gráficos a serem exibidos
mostrar_macd = st.sidebar.checkbox('Exibir MACD', True)
mostrar_candlestick = st.sidebar.checkbox('Exibir Candlestick', True)
mostrar_tabela = st.sidebar.checkbox('Exibir Tabela de Dados', True)
mostrar_noticias = st.sidebar.checkbox('Exibir Notícias e Sentimento', True)

# Indicar o status do mercado
mercado_status()

if executar:
    acoes = [acao.strip() for acao in acoes.split(',')]
    for acao in acoes:
        st.header(f"Análise para {acao}")
        try:
            ticker = yf.Ticker(acao)
            df = ticker.history(period='1mo').reset_index()
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d/%m/%Y')
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

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
                plotar_macd(df, acao)

            if mostrar_candlestick:
                plotar_candlestick(df, acao)

            if mostrar_tabela:
                plotar_tabela(df, acao)

            if mostrar_noticias:
                exibir_noticias(acao)

        except Exception as e:
            st.error(f"Erro ao processar a ação {acao}: {e}")
