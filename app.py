import streamlit as st
import pandas as pd
import plotly.express as px
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

    /* Aproxima o radio do título */
    div[data-baseweb="radio"] { margin-top: -10px !important; margin-bottom: -10px !important; }

    /* Situação da Demanda responsiva */
    .filtros-demanda { display: flex; gap: 20px; }
    @media (max-width: 768px) {
        .header-row { flex-direction: column; text-align: center; }
        .app-title { font-size: 22px !important; margin-top: 10px; }
        .header-row img { width: 150px !important; margin-bottom: 5px; }
        h2, h3, h4 { font-size: 16px !important; }
        .filtros-demanda {flex-direction: column; gap: 5px;}
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

    # ----------------------
    # utilitários
    # ----------------------
    GIDS = {
        "Demandas Gerais": "0",
        "Demandas Oftalmológicas": "1946301846",
        "Demandas da Saúde": "27665281",
        "Demandas Jurídicas": "1416239426",
    }

    COL_MAP = {
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
        "Data da Atualização": "Data da Atualização",
    }

    SHOW_COLS = [
        "Nome", "Telefone", "Rua", "Número", "Bairro",
        "Área da Demanda", "Resumo da Demanda", "Servidor Responsável",
        "Situação da Demanda", "Descrição da Situação", "Data da Atualização"
    ]

    def load_sheet(gid: str) -> pd.DataFrame:
        url = f"https://docs.google.com/spreadsheets/d/1TU9o9bgZPfZ-aKrxfgUqG03jTZOM3mWl0CCLn5SfwO0/export?format=csv&gid={gid}"
        df_ = pd.read_csv(url)
        df_.columns = df_.columns.str.replace(r"\s+", " ", regex=True).str.strip()
        ok_cols = [c for c in COL_MAP if c in df_.columns]
        df_ = df_[ok_cols].rename(columns=COL_MAP)
        if "Nome" in df_.columns:
            # garante string para .str
            df_["Nome"] = df_["Nome"].astype(str)
            df_ = df_[df_["Nome"].notna() & (df_["Nome"].str.strip() != "")]
        df_ = df_[[c for c in SHOW_COLS if c in df_.columns]]
        return df_

    def normalize_status(s: pd.Series) -> pd.Series:
        s = s.fillna("").astype(str).str.lower()
        # Mapeamento por “contenção” para pegar variações
        out = []
        for v in s:
            if "solucion" in v:
                out.append("Solucionado")
            elif "andament" in v:
                out.append("Em Andamento")
            elif "prejudic" in v:
                out.append("Prejudicado")
            else:
                out.append("Não informado")
        return pd.Series(out, index=s.index)

    def status_counts(df_: pd.DataFrame) -> pd.DataFrame:
        if "Situação da Demanda" not in df_.columns:
            return pd.DataFrame({"Situação": [], "Quantidade": []})
        st_norm = normalize_status(df_["Situação da Demanda"])
        cnt = st_norm.value_counts().reindex(
            ["Solucionado", "Em Andamento", "Prejudicado", "Não informado"],
            fill_value=0
        )
        return pd.DataFrame({"Situação": cnt.index, "Quantidade": cnt.values})

    COLOR_MAP = {
        "Solucionado": "#33cc33",     # verde
        "Em Andamento": "#ffd633",    # amarelo
        "Prejudicado": "#ff4d4d",     # vermelho
        "Não informado": "#9e9e9e",   # cinza
    }

    def pie_status(df_: pd.DataFrame, titulo: str):
        data = status_counts(df_)
        if data["Quantidade"].sum() == 0:
            st.info("Sem dados de situação nesta categoria.")
            return
        fig = px.pie(
            data,
            values="Quantidade",
            names="Situação",
            title=titulo,
            hole=0.35,
            color="Situação",
            color_discrete_map=COLOR_MAP
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # ======================
    # FILTRO DE CATEGORIA
    # ======================
    st.subheader("📑 Selecione a categoria:")
    aba_selecionada = st.radio(
        label="",
        options=list(GIDS.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )
    df = load_sheet(GIDS[aba_selecionada])

    # ======================
    # GRÁFICO – CATEGORIA ATUAL
    # ======================
    st.subheader("📊 Status das demandas (categoria selecionada)")
    pie_status(df, f"{aba_selecionada}")

    # (Opcional) visão geral com todas as categorias
    with st.expander("📈 Ver comparação entre todas as categorias"):
        cols = st.columns(2)
        all_items = list(GIDS.items())
        for i, (nome, gid) in enumerate(all_items):
            with cols[i % 2]:
                df_tmp = load_sheet(gid)
                pie_status(df_tmp, nome)

    # ======================
    # FUNÇÕES DE ESTILO DA TABELA
    # ======================
    def highlight_situacao_cell(val):
        if isinstance(val, str):
            l = val.lower()
            if "prejudic" in l:
                return "background-color:#ff4d4d;color:white;font-weight:bold; text-align:center;"
            if "andament" in l:
                return "background-color:#ffd633;color:black;font-weight:bold; text-align:center;"
            if "solucion" in l:
                return "background-color:#33cc33;color:white;font-weight:bold; text-align:center;"
        return "text-align:center;"

    def make_styler(df_in: pd.DataFrame):
        sty = df_in.style.set_properties(**{"text-align": "center"}) \
                         .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        if "Situação da Demanda" in df_in.columns:
            sty = sty.applymap(highlight_situacao_cell, subset=["Situação da Demanda"])
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
    # FILTRO SITUAÇÃO DA DEMANDA
    # ======================
    st.subheader("ℹ️ Situação da Demanda")
    st.markdown('<div class="filtros-demanda">', unsafe_allow_html=True)
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

    # Aplicação dos filtros
    df_filtrado = df.copy()
    if valor:
        df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).str.contains(valor, case=False, na=False)]
    if filtros and "Situação da Demanda" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Situação da Demanda"].str.lower().str.contains("|".join(filtros))]

    # ======================
    # EXIBIR TABELA
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