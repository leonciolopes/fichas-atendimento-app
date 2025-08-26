import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

# ======================
# CONFIGURAÇÃO DA PÁGINA
# ======================
st.set_page_config(page_title="Fichas de Atendimento", layout="wide")

# ======================
# LOGIN
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
    # CSS EXTRA (responsivo estilo desktop reduzido no mobile)
    # ======================
    st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    header[data-testid="stHeader"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
            
    .header-row {
        display:flex; align-items:center; justify-content:space-between;
        background-color:#004D26; padding:5px; border-radius:8px;
    }
                
    .app-title {
        flex:1; text-align:center; color:#fff; font-weight:800; font-size:40px;
    }

    h2, h3, h4 {
        color:#fff !important; font-weight:800 !important;
    }

    /* ===== Responsividade para celular ===== */
    @media (max-width: 768px) {
        .app-title { font-size: 22px !important; }
        .header-row img { width: 120px !important; }
        h2, h3, h4 { font-size: 16px !important; }  /* subtítulos menores */
        .stDataFrame { font-size: 12px !important; } /* tabela fonte menor */
    }
    </style>
    """, unsafe_allow_html=True)

    # ======================
    # CABEÇALHO
    # ======================
    st.markdown(
        """
        <div class="header-row">
            <div class="app-title">Fichas de Atendimento - Gabinete Vereador Leôncio Lopes</div>
            <img src="https://raw.githubusercontent.com/leonciolopes2528/fichas-atendimento-app/main/Logo-Branca.png" width="250">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ======================
    # CARREGAR PLANILHA
    # ======================
    url = "https://docs.google.com/spreadsheets/d/1TU9o9bgZPfZ-aKrxfgUqG03jTZOM3mWl0CCLn5SfwO0/export?format=csv&gid=0"
    df = pd.read_csv(url)
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

    mapeamento = {
        "Data de Atendimento": "Data de Atendimento",
        "Nome Completo": "Nome",
        "Telefone (31)9xxxx-xxxx": "Telefone",
        "Endereço": "Rua",
        "Unnamed: 9": "Número",
        "Unnamed: 10": "Bairro",
        "Área da Demanda": "Área da Demanda",
        "Resumo da Demanda": "Resumo da Demanda",
        "Servidor Responsável": "Servidor Responsável",
        "Situação da Demanda": "Situação da Demanda",
        "Descrição da Situação": "Descrição da Situação",
        "Data da Atualização": "Data da Atualização"
    }

    existentes = [c for c in mapeamento if c in df.columns]
    df = df[existentes].rename(columns=mapeamento)

    if "Nome" in df.columns:
        df = df[df["Nome"].notna() & (df["Nome"].str.strip() != "")]

    colunas_visiveis = [
        "Nome", "Telefone", "Rua", "Número", "Bairro",
        "Área da Demanda", "Resumo da Demanda", "Servidor Responsável",
        "Situação da Demanda", "Descrição da Situação", "Data da Atualização"
    ]
    df = df[[c for c in colunas_visiveis if c in df.columns]]

    # ======================
    # COLORAÇÃO + CENTRALIZAÇÃO
    # ======================
    def highlight_situacao(val):
        if isinstance(val, str):
            v = val.lower()
            if "prejudicado" in v:   return "background-color:#ff4d4d;color:white;font-weight:bold; text-align:center;"
            if "em andamento" in v:  return "background-color:#ffd633;color:black;font-weight:bold; text-align:center;"
            if "solucionado" in v:   return "background-color:#33cc33;color:white;font-weight:bold; text-align:center;"
        return "text-align:center;"

    def make_styler(df_in: pd.DataFrame):
        sty = df_in.style
        sty = sty.set_properties(**{"text-align": "center"}) \
                 .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        if "Situação da Demanda" in df_in.columns:
            sty = sty.applymap(highlight_situacao, subset=["Situação da Demanda"])
        try:
            sty = sty.hide(axis="index")
        except Exception:
            sty = sty.hide_index()
        return sty

    # ======================
    # EXIBIR TABELA PRINCIPAL
    # ======================
    st.subheader("📌 Fichas de Atendimento")
    st.dataframe(
        make_styler(df),
        use_container_width=True,
        height=400  # 🔹 tabela mais baixa (menos linhas visíveis)
    )

    # ======================
    # FILTROS
    # ======================
    st.subheader("🔎 Filtro de Dados")
    col1, col2 = st.columns([1,2])
    with col1:
        coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)

    valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

    if valor:
        filtrado = df[df[coluna].astype(str).str.contains(valor, case=False, na=False)]
        st.dataframe(
            make_styler(filtrado),
            use_container_width=True,
            height=400  # 🔹 também reduzido
        )

    # Botão de logout
    authenticator.logout("Sair", "sidebar")