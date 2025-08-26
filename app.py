import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

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
            <img src="https://raw.githubusercontent.com/leonciolopes2528/fichas-atendimento-app/main/Logo-Branca.png" width="300">
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

    # 🔹 Remover linhas sem Nome preenchido
    if "Nome" in df.columns:
        df = df[df["Nome"].notna() & (df["Nome"].str.strip() != "")]

    # Colunas visíveis (sem Data de Atendimento)
    colunas_visiveis = [
        "Nome", "Telefone", "Rua", "Número", "Bairro",
        "Área da Demanda", "Resumo da Demanda", "Servidor Responsável",
        "Situação da Demanda", "Descrição da Situação", "Data da Atualização"
    ]
    df = df[[c for c in colunas_visiveis if c in df.columns]]

    # ======================
    # GRIDOPTIONS DO AGGRID
    # ======================
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=15)  # paginação
    gb.configure_default_column(cellStyle={'textAlign': 'center'})  # centralizar
    gb.configure_grid_options(domLayout='normal')  # scroll

    # Coloração condicional da coluna Situação da Demanda
    cellsytle_jscode = JsCode("""
    function(params) {
        if (params.value && params.colDef.field === 'Situação da Demanda') {
            let v = params.value.toLowerCase();
            if (v.includes('prejudicado')) {
                return { 'color': 'white', 'backgroundColor': '#ff4d4d', 'fontWeight': 'bold', 'textAlign': 'center'};
            }
            if (v.includes('em andamento')) {
                return { 'color': 'black', 'backgroundColor': '#ffd633', 'fontWeight': 'bold', 'textAlign': 'center'};
            }
            if (v.includes('solucionado')) {
                return { 'color': 'white', 'backgroundColor': '#33cc33', 'fontWeight': 'bold', 'textAlign': 'center'};
            }
        }
        return {'textAlign': 'center'};
    }
    """)
    gb.configure_column("Situação da Demanda", cellStyle=cellsytle_jscode)

    grid_options = gb.build()

    # ======================
    # EXIBIR TABELA PRINCIPAL
    # ======================
    st.subheader("📌 Fichas de Atendimento")
    AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=True,
        theme="streamlit",  # "streamlit", "light", "dark", "blue", "fresh"
        height=600
    )

    # ======================
    # FILTROS
    # ======================
    st.subheader("🔎 Filtro de Dados")
    coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)
    valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

    if valor:
        filtrado = df[df[coluna].astype(str).str.contains(valor, case=False, na=False)]
        AgGrid(
            filtrado,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            height=600
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
            background-color: #004D26; /* verde escuro */
            padding: 15px 0;
            text-align: center;
            color: white;
            font-size: 14px;
            border-top: 2px solid #002214;
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