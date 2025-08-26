import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

# ======================
# CONFIGURAÇÃO DA PÁGINA
# ======================
st.set_page_config(page_title="Fichas de Atendimento", layout="wide")

# ======================
# LOGIN (usa os Secrets do Streamlit Cloud)
# ======================
credentials = {
    "usernames": {
        "admin": {
            "name": "Admin",
            "password": st.secrets["passwords"]["admin"],
        },
        "gabinete": {
            "name": "Gabinete Vereador",
            "password": st.secrets["passwords"]["gabinete"],
        },
    }
}

authenticator = stauth.Authenticate(
    credentials,
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"],
    cookie_expiry_days=st.secrets["cookie"]["expiry_days"]
)

# Tela de login na sidebar
name, auth_status, username = authenticator.login(location="sidebar")

# ======================
# VERIFICAÇÃO DE LOGIN
# ======================
if auth_status is False:
    st.error("Usuário ou senha incorretos ❌")

elif auth_status is None:
    st.warning("Digite usuário e senha para continuar 🔑")

else:
    # ======================
    # CSS EXTRA
    # ======================
    st.markdown("""
    <style>
    .header-row { 
        display:flex; align-items:center; justify-content:space-between; 
        background-color:#004D26; padding:15px; border-radius:8px;
    }
    .app-title { 
        flex:1; text-align:center; color:#fff; font-weight:800; font-size:28px; 
    }
    h2, h3, h4 { color:#fff !important; font-weight:800 !important; }
    .footer { 
        text-align:center; color:white; padding:10px; margin-top:30px; 
        background-color:#004D26; border-radius:8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ======================
    # CABEÇALHO
    # ======================
    st.markdown(
        """
        <div class="header-row">
            <div></div>
            <div class="app-title">Fichas de Atendimento - Gabinete Vereador Leôncio Lopes</div>
            <img src="https://drive.google.com/uc?export=view&id=1-2-Ke-C2t8QLyRBpCYPsE8kKvgrVcc6h" width="90">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ======================
    # CARREGAR PLANILHA
    # ======================
    url = "https://docs.google.com/spreadsheets/d/1TU9o9bgZPfZ-aKrxfgUqG03jTZOM3mWl0CCLn5SfwO0/export?format=csv&gid=0"
    df = pd.read_csv(url)

    # ======================
    # FILTRAR COLUNAS DE INTERESSE
    # ======================
    colunas_desejadas = [
        "Nome",
        "Telefone",
        "Rua",
        "Número",
        "Bairro",
        "Área da demanda",
        "Resumo da Demanda",
        "Servidor Responsável",
        "Situação da Demanda",
        "Descrição da Situação",
        "Data da Atualização"
    ]
    df = df[[c for c in colunas_desejadas if c in df.columns]]  # garante que só pega colunas que existem

    # ======================
    # COLORAÇÃO DA SITUAÇÃO
    # ======================
    def highlight_situacao(val):
        if isinstance(val, str):
            if "prejudicado" in val.lower():
                return "background-color: #ff4d4d; color: white; font-weight: bold;"  # vermelho
            elif "em andamento" in val.lower():
                return "background-color: #ffd633; color: black; font-weight: bold;"  # amarelo
            elif "solucionado" in val.lower():
                return "background-color: #33cc33; color: white; font-weight: bold;"  # verde
        return ""

    styled_df = df.style.applymap(highlight_situacao, subset=["Situação da Demanda"])

    # ======================
    # EXIBIR TABELA SIMPLIFICADA
    # ======================
    st.subheader("📌 Fichas de Atendimento")
    st.dataframe(styled_df, use_container_width=True)

    # ======================
    # FILTROS
    # ======================
    st.subheader("🔎 Filtro de Dados")

    col1, col2 = st.columns([1,2])
    with col1:
        coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)

    with col2:
        if any(x in coluna.lower() for x in ["data"]):
            dica = "📅 Digite a data no formato **DD/MM/AAAA**."
        elif any(x in coluna.lower() for x in ["telefone", "cpf", "identidade"]):
            dica = "🔢 Digite números ou parte do número."
        elif "sexo" in coluna.lower():
            dica = "⚧ Digite Masculino ou Feminino."
        elif any(x in coluna.lower() for x in ["estado civil", "profissão", "bairro", "área da demanda", "servidor"]):
            dica = "✏️ Digite parte do texto (não precisa ser completo)."
        else:
            dica = "✏️ Digite texto ou número presente na coluna escolhida."
        st.caption(dica)

    valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

    if valor:
        filtrado = df[df[coluna].astype(str).str.contains(valor, case=False, na=False)]
        st.dataframe(
            filtrado.style.applymap(highlight_situacao, subset=["Situação da Demanda"]),
            use_container_width=True
        )

    # ======================
    # FOOTER
    # ======================
    st.markdown(
        "<div class='footer'>📌 Desenvolvido para o Gabinete Vereador Leôncio Lopes</div>",
        unsafe_allow_html=True
    )

    # Botão de logout
    authenticator.logout("Sair", "sidebar")