import base64
from pathlib import Path
import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import plotly.express as px

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

name, auth_status, username = authenticator.login(location="sidebar")

# ======================
# VERIFICAÇÃO LOGIN
# ======================
if auth_status is False:
    st.error("Usuário ou senha incorretos ❌")

elif auth_status is None:
    st.warning("Digite usuário e senha para continuar 🔑")

else:

    # ======================
    # BOTÃO ATUALIZAR
    # ======================
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

    # ======================
    # CSS
    # ======================
    st.markdown("""
    <style>
    header[data-testid="stHeader"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .header-row {
        display:flex;
        align-items:center;
        justify-content:space-between;
        background-color:#004D26;
        padding:8px;
        border-radius:8px;
    }

    .app-title{
        flex:1;
        text-align:center;
        color:white;
        font-size:36px;
        font-weight:800;
    }

    .filtros-demanda{display:flex;gap:20px;}

    @media (max-width:768px){
        .header-row{flex-direction:column;}
        .app-title{font-size:22px;}
    }
    </style>
    """, unsafe_allow_html=True)

    # ======================
    # LOGO
    # ======================
    def _img_b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    try:
        LOGO = f"data:image/png;base64,{_img_b64('Logo-Branca.png')}"
    except:
        LOGO = "https://raw.githubusercontent.com/leonciolopes/fichas-atendimento-app/main/Logo-Branca.png"

    st.markdown(f"""
    <div class="header-row">
        <div></div>
        <div class="app-title">Fichas de Atendimento - Gabinete Vereador Leôncio Lopes</div>
        <img src="{LOGO}" width="220">
    </div>
    """, unsafe_allow_html=True)

    # ======================
    # CATEGORIAS
    # ======================
    CATEGORIAS = {
        "Demandas Gerais": "0",
        "Demandas Oftalmológicas": "1946301846",
        "Demandas da Saúde": "27665281",
        "Demandas Jurídicas": "1416239426",
    }

    BASE_URL = "https://docs.google.com/spreadsheets/d/1TU9o9bgZPfZ-aKrxfgUqG03jTZOM3mWl0CCLn5SfwO0/export?format=csv&gid={gid}"

    # ======================
    # CARREGAR PLANILHA
    # ======================
    @st.cache_data(ttl=10)
    def carregar_df(gid):

        url = BASE_URL.format(gid=gid)

        df = pd.read_csv(url)

        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

        return df

    # ======================
    # PREPARAR DATAFRAME
    # ======================
    def preparar_df_bruto(df_raw):

        mapeamento = {
            "Data de Atendimento": "Data de Atendimento",
            "Nome Completo": "Nome",
            "Telefone": "Telefone",
            "Endereço": "Rua",
            "Unnamed: 10": "Número",
            "Unnamed: 11": "Bairro",
            "Área da Demanda": "Área da Demanda",
            "Resumo da Demanda": "Resumo da Demanda",
            "Servidor Responsável": "Servidor Responsável",
            "Situação da Demanda": "Situação da Demanda",
            "Descrição da Situação": "Descrição da Situação",
            "Data da Atualização": "Data da Atualização",
        }

        colunas_existentes = [c for c in mapeamento if c in df_raw.columns]

        df = df_raw[colunas_existentes].rename(columns=mapeamento)

        if "Nome" in df.columns:
            df = df[df["Nome"].notna()]
            df = df[df["Nome"].astype(str).str.strip() != ""]

        ordem = [
            "Data de Atendimento",
            "Nome",
            "Telefone",
            "Rua",
            "Número",
            "Bairro",
            "Área da Demanda",
            "Resumo da Demanda",
            "Servidor Responsável",
            "Situação da Demanda",
            "Descrição da Situação",
            "Data da Atualização",
        ]

        ordem = [c for c in ordem if c in df.columns]

        return df[ordem].copy()

    # ======================
    # ESTILO SITUAÇÃO
    # ======================
    def highlight_situacao(val):

        if isinstance(val, str):

            v = val.lower()

            if "solucionado" in v:
                return "background-color:#33cc33;color:white;font-weight:bold;text-align:center"

            if "em andamento" in v:
                return "background-color:#ffd633;color:black;font-weight:bold;text-align:center"

            if "prejudicado" in v:
                return "background-color:#ff4d4d;color:white;font-weight:bold;text-align:center"

        return "text-align:center"

    def make_styler(df):

        sty = df.style.set_properties(**{"text-align": "center"})

        if "Situação da Demanda" in df.columns:
            sty = sty.applymap(highlight_situacao, subset=["Situação da Demanda"])

        try:
            sty = sty.hide(axis="index")
        except:
            sty = sty.hide_index()

        return sty

    # ======================
    # GRÁFICO
    # ======================
    def pie_status(df):

        if "Situação da Demanda" not in df.columns:
            return

        s = df["Situação da Demanda"].fillna("").str.lower()

        mapa = {
            "solucionado": "Solucionado",
            "em andamento": "Em Andamento",
            "prejudicado": "Prejudicado",
        }

        s = s.map(mapa).fillna("Outros")

        contagem = s.value_counts().reset_index()

        contagem.columns = ["Situação", "Quantidade"]

        cores = {
            "Solucionado": "#33cc33",
            "Em Andamento": "#ffd633",
            "Prejudicado": "#ff4d4d",
            "Outros": "#a6a6a6",
        }

        fig = px.pie(
            contagem,
            names="Situação",
            values="Quantidade",
            hole=0.35,
            color="Situação",
            color_discrete_map=cores
        )

        fig.update_layout(width=420, height=420, margin=dict(t=0,b=0,l=0,r=0))

        st.plotly_chart(fig)

    # ======================
    # SELEÇÃO CATEGORIA
    # ======================
    st.subheader("📑 Selecione a categoria:")

    aba = st.radio(
        "",
        options=list(CATEGORIAS.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )

    gid = CATEGORIAS[aba]

    # ======================
    # CARREGAR DADOS
    # ======================
    df_raw = carregar_df(gid)

    df = preparar_df_bruto(df_raw)

    # ======================
    # FILTROS + GRÁFICO
    # ======================
    st.subheader("🔎 Análise e Filtros")

    col1, col2 = st.columns([1,1])

    with col1:

        coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns)

        valor = st.text_input("Digite um valor para filtrar:")

        st.subheader("📊 Situação da Demanda")

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

        df_filtrado = df.copy()

        if valor:
            df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).str.contains(valor, case=False, na=False)]

        if filtros:
            df_filtrado = df_filtrado[df_filtrado["Situação da Demanda"].str.lower().isin(filtros)]

    with col2:

        pie_status(df_filtrado)

    # ======================
    # TABELA
    # ======================
    st.subheader(f"📌 Fichas de Atendimento - {aba}")

    st.dataframe(
        make_styler(df_filtrado),
        use_container_width=True,
        height=500
    )

    # ======================
    # FOOTER
    # ======================
    st.markdown("""
    <div style='text-align:center;padding:15px;background:#004D26;color:white'>
    © 2025 Gabinete Vereador Leôncio Lopes
    </div>
    """, unsafe_allow_html=True)

    authenticator.logout("Sair", "sidebar")
