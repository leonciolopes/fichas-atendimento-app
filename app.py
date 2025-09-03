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
    header[data-testid="stHeader"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 0.5rem !important; }

    .header-row {
        display:flex; align-items:center; justify-content:space-between;
        background-color:#004D26; padding:8px; border-radius:8px;
    }
    .app-title {
        flex:1; text-align:center; color:#fff; font-weight:800; font-size:36px;
    }

    h2, h3, h4 { color:#fff !important; font-weight:800 !important; }

    /* MOBILE */
    @media (max-width: 768px) {
        .header-row { flex-direction: column; text-align: center; }
        .app-title { font-size: 22px !important; margin-top: 10px; }
        .header-row img { width: 150px !important; margin-bottom: 5px; }
        h2, h3, h4 { font-size: 16px !important; }
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
            <img src="https://raw.githubusercontent.com/leonciolopes2528/fichas-atendimento-app/main/Logo-Branca.png" width="220">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ======================
    # FILTRO DE ABA (radio)
    # ======================
    st.subheader("📑 Selecione a categoria:")
    aba_selecionada = st.radio(
        label="",  # remove texto extra
        options=["Atendimento", "Demandas Oftalmológicas"],
        index=0
    )

    # Definir GID conforme aba selecionada
    if aba_selecionada == "Atendimento":
        gid = "0"   # substitua pelo gid real da aba Atendimento
    else:
        gid = "1"   # substitua pelo gid real da aba Demandas Oftalmológicas

    # ======================
    # CARREGAR PLANILHA COM BASE NA ABA
    # ======================
    url = f"https://docs.google.com/spreadsheets/d/1TU9o9bgZPfZ-aKrxfgUqG03jTZOM3mWl0CCLn5SfwO0/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

    # ======================
    # FILTRAR/RENOMEAR COLUNAS
    # ======================
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
    # FUNÇÕES DE ESTILO
    # ======================
    def highlight_situacao(val):
        if isinstance(val, str):
            v = val.lower()
            if "prejudicado" in v:   return "background-color:#ff4d4d;color:white;font-weight:bold; text-align:center;"
            if "em andamento" in v:  return "background-color:#ffd633;color:black;font-weight:bold; text-align:center;"
            if "solucionado" in v:   return "background-color:#33cc33;color:white;font-weight:bold; text-align:center;"
        return "text-align:center;"

    def make_styler(df_in: pd.DataFrame):
        sty = df_in.style.set_properties(**{"text-align": "center"}) \
                         .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        if "Situação da Demanda" in df_in.columns:
            sty = sty.applymap(highlight_situacao, subset=["Situação da Demanda"])
        try:
            sty = sty.hide(axis="index")
        except Exception:
            sty = sty.hide_index()
        return sty

    # ======================
    # FILTRO DE TEXTO
    # ======================
    st.subheader("🔎 Filtro de Dados")
    coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)
    valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

    # ======================
    # FILTRO SITUAÇÃO DA DEMANDA (checkboxes)
    # ======================
    st.subheader("📌 Situação da Demanda")
    chk_solucionado = st.checkbox("Solucionado")
    chk_andamento = st.checkbox("Em Andamento")
    chk_prejudicado = st.checkbox("Prejudicado")

    filtros = []
    if chk_solucionado:
        filtros.append("solucionado")
    if chk_andamento:
        filtros.append("em andamento")
    if chk_prejudicado:
        filtros.append("prejudicado")

    # Aplicar filtros
    if valor:
        df = df[df[coluna].astype(str).str.contains(valor, case=False, na=False)]

    if filtros and "Situação da Demanda" in df.columns:
        df = df[df["Situação da Demanda"].str.lower().isin(filtros)]

    # ======================
    # EXIBIR TABELA
    # ======================
    st.subheader(f"📌 Fichas de Atendimento - {aba_selecionada}")
    st.dataframe(
        make_styler(df),
        use_container_width=True,
        height=500
    )

    # ======================
    # FOOTER
    # ======================
    st.markdown(
        """
        <style>
        .custom-footer {
            position: relative;
            bottom: 0;
            width: 100%;
            background-color: #004D26;
            padding: 15px 0;
            text-align: center;
            color: white;
            font-size: 14px;
            border-top: 2px solid #003300;
        }
        </style>
        <div class="custom-footer">
            © 2025 Gabinete Vereador <b>Leôncio Lopes</b> da Câmara Municipal de Sete Lagoas. <br>
            Todos os direitos reservados. 
        </div>
        """,
        unsafe_allow_html=True
    )

    authenticator.logout("Sair", "sidebar")