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

    /* Radios mais próximos do título */
    div[data-baseweb="radio"] {
        margin-top: -10px !important;
        margin-bottom: -10px !important;
    }

    /* Box dos checkboxes um pouco mais perto do título */
    .stCheckbox { margin-top: -8px !important; }

    /* Títulos nivelados (Análise & Filtros e Situação da Demanda) */
    .titulo-h2 {
        font-size: 26px !important;
        line-height: 1.1 !important;
        margin-top: 6px !important;
        margin-bottom: 8px !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    /* Para centralizar o gráfico no lado direito */
    .center-plot {
        display: flex; 
        justify-content: center; 
        align-items: center;
        width: 100%;
    }

    @media (max-width: 768px) {
        .header-row { flex-direction: column; text-align: center; }
        .app-title { font-size: 22px !important; margin-top: 10px; }
        .header-row img { width: 150px !important; margin-bottom: 5px; }
        h2, h3, h4, .titulo-h2 { font-size: 18px !important; }

        /* filtros em coluna no mobile */
        .filtros-demanda {flex-direction: column !important; gap: 6px;}
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
    # FILTRO DE CATEGORIA
    # ======================
    st.subheader("📑 Selecione a categoria:")
    aba_selecionada = st.radio(
        label="",
        options=["Demandas Gerais", "Demandas Oftalmológicas", "Demandas da Saúde", "Demandas Jurídicas"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # GIDs das abas
    if aba_selecionada == "Demandas Gerais":
        gid = "0"
    elif aba_selecionada == "Demandas Oftalmológicas":
        gid = "1946301846"
    elif aba_selecionada == "Demandas da Saúde":
        gid = "27665281"
    else:
        gid = "1416239426"

    # ======================
    # CARREGAR PLANILHA
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
        # garante string para .str
        df["Nome"] = df["Nome"].astype(str)
        df = df[df["Nome"].notna() & (df["Nome"].str.strip() != "")]

    colunas_visiveis = [
        "Nome", "Telefone", "Rua", "Número", "Bairro",
        "Área da Demanda", "Resumo da Demanda", "Servidor Responsável",
        "Situação da Demanda", "Descrição da Situação", "Data da Atualização"
    ]
    df = df[[c for c in colunas_visiveis if c in df.columns]]

    # ======================
    # FUNÇÕES DE ESTILO DA TABELA
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
    # LAYOUT: FILTROS (ESQ) + GRÁFICO (DIR)
    # ======================
    col_filtros, col_graf = st.columns([7, 5], gap="large")

    # ===== coluna ESQUERDA – filtros e tabela =====
    with col_filtros:
        st.markdown('<div class="titulo-h2">🔎 Análise e Filtros</div>', unsafe_allow_html=True)

        if len(df.columns) == 0:
            st.info("Não há colunas disponíveis nesta aba.")
            df_filtrado = df.copy()
        else:
            # Filtro de texto
            coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)
            valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

            # Título grande para a situação
            st.markdown('<div class="titulo-h2">📊 Situação da Demanda</div>', unsafe_allow_html=True)
            # Checkboxes (em coluna no desktop também fica elegante com o espaçamento reduzido)
            chk_solucionado = st.checkbox("Solucionado")
            chk_andamento = st.checkbox("Em Andamento")
            chk_prejudicado = st.checkbox("Prejudicado")

            df_filtrado = df.copy()
            if valor:
                df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).str.contains(valor, case=False, na=False)]

            filtros = []
            if chk_solucionado: filtros.append("solucionado")
            if chk_andamento:   filtros.append("em andamento")
            if chk_prejudicado: filtros.append("prejudicado")

            if filtros and "Situação da Demanda" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["Situação da Demanda"].str.lower().isin(filtros)]

        st.subheader(f"📌 Fichas de Atendimento - {aba_selecionada}")
        st.dataframe(
            make_styler(df_filtrado),
            use_container_width=True,
            height=500
        )

    # ===== coluna DIREITA – gráfico =====
    with col_graf:
        # Função do gráfico de pizza
        def pie_status(df_source: pd.DataFrame, titulo_legenda: str):
            col_name = "Situação da Demanda"
            if col_name not in df_source.columns or df_source.empty:
                st.info("Sem dados para exibir o gráfico.")
                return

            # Normaliza
            s = df_source[col_name].astype(str).str.strip().str.lower()

            # Classes que queremos contar
            classes = ["solucionado", "em andamento", "prejudicado"]
            counts = {c: 0 for c in classes}
            outros = 0
            for v in s:
                if v in counts:
                    counts[v] += 1
                else:
                    outros += 1

            labels = ["Solucionado", "Em Andamento", "Prejudicado", "Outros"]
            valores = [counts["solucionado"], counts["em andamento"], counts["prejudicado"], outros]

            # Cores personalizadas
            color_map = {
                "Solucionado": "#28a745",     # Verde
                "Em Andamento": "#ffd633",    # Amarelo
                "Prejudicado": "#ff4d4d",     # Vermelho
                "Outros": "#B0B8BF"           # Cinza
            }

            fig = px.pie(
                names=labels,
                values=valores,
                hole=0.55,
                color=labels,
                color_discrete_map=color_map
            )
            # Sem título, tamanho menor e centralização
            fig.update_layout(
                showlegend=True,
                legend_title_text=titulo_legenda,
                width=380, height=380,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            # Envolve numa div para centralizar
            st.markdown('<div class="center-plot">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)

        pie_status(df_filtrado, titulo_legenda=aba_selecionada)

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