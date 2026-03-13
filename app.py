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

    /* Radios mais próximos do título */
    div[data-baseweb="radio"] {
        margin-top: -10px !important;
        margin-bottom: -10px !important;
    }

    .filtros-demanda { display: flex; gap: 20px; }
    @media (max-width: 768px) {
        .header-row { flex-direction: column; text-align: center; }
        .app-title { font-size: 22px !important; margin-top: 10px; }
        .header-row img { width: 150px !important; margin-bottom: 5px; }
        h2, h3, h4 { font-size: 16px !important; }
        .filtros-demanda { flex-direction: column; gap: 6px; }
    }
    </style>
    """, unsafe_allow_html=True)

    # ======================
    # CABEÇALHO (logo local base64 + fallback GitHub)
    # ======================
    def _img_b64(path: str) -> str:
        p = Path(path)
        with p.open("rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    try:
        # usa o arquivo local
        LOGO_SRC = f"data:image/png;base64,{_img_b64('Logo-Branca.png')}"
    except Exception:
        # fallback para o raw do GitHub (ajuste aqui se mudar repo/usuário/arquivo)
        LOGO_SRC = "https://raw.githubusercontent.com/leonciolopes/fichas-atendimento-app/main/Logo-Branca.png"

    st.markdown(
        f"""
        <div class="header-row">
            <div></div>
            <div class="app-title">Fichas de Atendimento - Gabinete Vereador Leôncio Lopes</div>
            <img src="{LOGO_SRC}" width="220" />
        </div>
        """,
        unsafe_allow_html=True
    )

    # ======================
    # MAPA DE CATEGORIAS
    # ======================
    CATEGORIAS = {
        "Demandas Gerais": "0",
        "Demandas Oftalmológicas": "1946301846",
        "Demandas da Saúde": "27665281",
        "Demandas Jurídicas": "1416239426",
    }
    BASE_URL = "https://docs.google.com/spreadsheets/d/1TU9o9bgZPfZ-aKrxfgUqG03jTZOM3mWl0CCLn5SfwO0/export?format=csv&gid={gid}"

    # ======================
    # FUNÇÕES AUXILIARES
    # ======================
    @st.cache_data(show_spinner=False)
    def carregar_df(gid: str) -> pd.DataFrame:
        url = BASE_URL.format(gid=gid)
        df = pd.read_csv(url)
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()
        return df

    def preparar_df_bruto(df_raw: pd.DataFrame) -> pd.DataFrame:
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
        existentes = [c for c in mapeamento if c in df_raw.columns]
        df = df_raw[existentes].rename(columns=mapeamento)

        if "Nome" in df.columns:
            df = df[df["Nome"].notna()]
            df["Nome"] = df["Nome"].astype(str)
            df = df[df["Nome"].str.strip() != ""]

        colunas_visiveis = [
            "Data de Atendimento", "Nome", "Telefone", "Rua", "Número", "Bairro",
            "Área da Demanda", "Resumo da Demanda", "Servidor Responsável",
            "Situação da Demanda", "Descrição da Situação", "Data da Atualização"
        ]
        colunas = [c for c in colunas_visiveis if c in df.columns]
        return df[colunas].copy()

    def highlight_situacao(val):
        if isinstance(val, str):
            v = val.lower()
            if "prejudicado" in v:
                return "background-color:#ff4d4d;color:white;font-weight:bold; text-align:center;"
            if "em andamento" in v:
                return "background-color:#ffd633;color:black;font-weight:bold; text-align:center;"
            if "solucionado" in v:
                return "background-color:#33cc33;color:white;font-weight:bold; text-align:center;"
        return "text-align:center;"

    def make_styler(df_in: pd.DataFrame):
        sty = (df_in.style
               .set_properties(**{"text-align": "center"})
               .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}]))
        if "Situação da Demanda" in df_in.columns:
            sty = sty.applymap(highlight_situacao, subset=["Situação da Demanda"])
        try:
            sty = sty.hide(axis="index")
        except Exception:
            sty = sty.hide_index()
        return sty

    # ---- Gráfico de pizza (com cores personalizadas)
    def pie_status(df: pd.DataFrame, key: str):
        col = "Situação da Demanda"
        if col not in df.columns or df.empty:
            st.info("Sem dados para o gráfico nesta seleção.")
            return

        s = (df[col].fillna("")
                .astype(str)
                .str.strip()
                .str.lower())

        mapa = {
            "solucionado": "Solucionado",
            "em andamento": "Em Andamento",
            "prejudicado": "Prejudicado",
        }
        s = s.map(mapa).fillna("Outros")

        ordem = ["Solucionado", "Em Andamento", "Prejudicado", "Outros"]
        contagem = (s.value_counts().reindex(ordem, fill_value=0).reset_index())
        contagem.columns = ["Situação", "Quantidade"]

        # Paleta personalizada
        cores = {
            "Solucionado": "#33cc33",   # Verde
            "Em Andamento": "#ffd633",  # Amarelo
            "Prejudicado": "#ff4d4d",   # Vermelho
            "Outros": "#a6a6a6"         # Cinza
        }

        fig = px.pie(
            contagem,
            names="Situação",
            values="Quantidade",
            title=None,
            hole=0.35,
            color="Situação",
            color_discrete_map=cores
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            width=420, height=420,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=False, key=key)

    # ======================
    # FILTRO DE CATEGORIA
    # ======================
    st.subheader("📑 Selecione a categoria:")
    aba_selecionada = st.radio(
        label="",
        options=list(CATEGORIAS.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )
    gid = CATEGORIAS[aba_selecionada]

    # ======================
    # CARREGAR + PREPARAR DF
    # ======================
    df_raw = carregar_df(gid)
    df = preparar_df_bruto(df_raw)

    # ======================
    # FILTROS + GRÁFICO LADO A LADO
    # ======================
    st.subheader("🔎 Análise e Filtros")

    col_filtros, col_grafico = st.columns([1, 1])

    with col_filtros:
        if len(df.columns) == 0:
            st.info("Não há colunas disponíveis nesta aba.")
            df_filtrado = df.copy()
        else:
            coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)
            valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

            st.subheader("📊 Situação da Demanda")

            st.markdown('<div class="filtros-demanda">', unsafe_allow_html=True)
            chk_solucionado = st.checkbox("Solucionado")
            chk_andamento = st.checkbox("Em Andamento")
            chk_prejudicado = st.checkbox("Prejudicado")
            st.markdown('</div>', unsafe_allow_html=True)

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
            if filtros and "Situação da Demanda" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["Situação da Demanda"].astype(str).str.lower().isin(filtros)]

    with col_grafico:
        g1, g2, g3 = st.columns([1, 2, 1])
        with g2:
            pie_status(df_filtrado, key=f"pie_lado_{gid}")

    # ======================
    # TABELA
    # ======================
    st.subheader(f"📌 Fichas de Atendimento - {aba_selecionada}")
    st.dataframe(
        make_styler(df_filtrado),
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

    # Botão de logout
    authenticator.logout("Sair", "sidebar")
