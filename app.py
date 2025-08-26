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
        "leoncio": {
            "name": "Leôncio Lopes",
            "password": st.secrets["passwords"]["leoncio"],
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
    .header-row { display:flex; align-items:center; justify-content:space-between; }
    .app-title { flex:1; text-align:center; color:#fff; font-weight:800; font-size:30px; }
    h2, h3, h4 { color:#fff !important; font-weight:800 !important; }
    table { border-collapse: collapse !important; width: 100% !important; }
    th, td { border: 1px solid #1f1f1f !important; padding: 6px 8px !important; }
    th { background:#e6e6e6 !important; color:#000 !important; font-weight:800 !important; }
    [data-baseweb="select"] div, .stTextInput input { color:#111 !important; }
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
            <img src="https://drive.google.com/uc?export=view&id=1-2-Ke-C2t8QLyRBpCYPsE8kKvgrVcc6h" width="110">
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
    # EXIBIR TABELA
    # ======================
    st.subheader("📌 Dados atualizados diretamente da nuvem")
    st.dataframe(df, use_container_width=True)

    with st.expander("Ver tabela com bordas escuras e cabeçalhos em negrito (estática)"):
        st.table(
            df.style
              .hide(axis="index")
              .set_table_styles([
                  {"selector": "th, td", "props": [("border", "1px solid #1f1f1f")]},
                  {"selector": "th", "props": [("font-weight", "800"), ("background-color", "#e6e6e6"), ("color", "#000")]}
              ])
        )

    # ======================
    # FILTROS
    # ======================
    st.subheader("🔎 Filtro de Dados")

    coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)

    # Dicas automáticas
    if any(x in coluna.lower() for x in ["data"]):
        dica = "📅 Digite a data no formato **DD/MM/AAAA** (ex.: 25/08/2025)."
    elif any(x in coluna.lower() for x in ["telefone", "cpf", "identidade"]):
        dica = "🔢 Digite **números** ou parte do número."
    elif "sexo" in coluna.lower():
        dica = "⚧ Digite **Masculino** ou **Feminino**."
    elif any(x in coluna.lower() for x in ["estado civil", "profissão", "bairro", "área da demanda", "servidor"]):
        dica = "✏️ Digite **parte do texto** (não precisa ser completo)."
    else:
        dica = "✏️ Digite **texto ou número** presente na coluna escolhida."

    st.caption(dica)
    valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

    if valor:
        filtrado = df[df[coluna].astype(str).str.contains(valor, case=False, na=False)]
        st.dataframe(filtrado, use_container_width=True)

    # Botão de logout
    authenticator.logout("Sair", "sidebar")
