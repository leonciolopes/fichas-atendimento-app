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
    /* Cabeçalho */
    .header-row {
        display:flex; align-items:center; justify-content:space-between;
        background-color:#004D26; padding:15px; border-radius:8px;
    }
    .app-title {
        flex:1; text-align:center; color:#fff; font-weight:800; font-size:28px;
    }
    h2, h3, h4 { color:#fff !important; font-weight:800 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ======================
    # CABEÇALHO (logo no canto superior direito)
    # ======================
    st.markdown(
        """
        <div class="header-row">
            <div></div>
            <div class="app-title">Fichas de Atendimento - Gabinete Vereador Leôncio Lopes</div>
            <img src="Logo-Branca.png" width="90">
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

    # ======================
    # ORDENAR PELA DATA DE ATENDIMENTO
    # ======================
    if "Data de Atendimento" in df.columns:
        df["Data de Atendimento"] = pd.to_datetime(df["Data de Atendimento"], errors="coerce", dayfirst=True)
        df = df.sort_values("Data de Atendimento", ascending=True)

    # Colunas visíveis (sem Data de Atendimento)
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
            sty = sty.hide(axis="index")  # pandas >= 1.4
        except Exception:
            sty = sty.hide_index()
        return sty

    # ======================
    # EXIBIR TABELA PRINCIPAL
    # ======================
    st.subheader("Fichas de Atendimento")
    st.dataframe(
        make_styler(df),
        use_container_width=True,
        height=600
    )

    # ======================
    # FILTROS
    # ======================
    st.subheader("🔎 Filtro de Dados")
    col1, col2 = st.columns([1,2])
    with col1:
        coluna = st.selectbox("Selecione uma coluna para filtrar:", df.columns, index=0)

    with col2:
        if any(x in coluna.lower() for x in ["data"]):
            dica = "📅 Digite a data no formato DD/MM/AAAA."
        elif any(x in coluna.lower() for x in ["telefone", "cpf", "identidade"]):
            dica = "🔢 Digite números ou parte do número."
        elif "sexo" in coluna.lower():
            dica = "⚧ Digite Masculino ou Feminino."
        elif any(x in coluna.lower() for x in ["estado civil", "profissão", "bairro", "área da demanda", "servidor"]):
            dica = "✏️ Digite parte do texto."
        else:
            dica = "✏️ Digite texto ou número presente na coluna."
        st.caption(dica)

    valor = st.text_input(f"Digite um valor para filtrar em **{coluna}**:")

    if valor:
        filtrado = df[df[coluna].astype(str).str.contains(valor, case=False, na=False)]
        st.dataframe(
            make_styler(filtrado),
            use_container_width=True,
            height=600
        )

    # ======================
    # FOOTER PROFISSIONAL ESTILO INSTITUCIONAL
    # ======================
    st.markdown(
        """
        <style>
        .custom-footer {
            position: relative;
            bottom: 0;
            width: 100%;
            background-color: #003366; /* azul escuro */
            padding: 15px 0;
            text-align: center;
            color: white;
            font-size: 14px;
            border-top: 2px solid #002244;
        }
        .custom-footer a {
            color: #66b2ff; /* azul claro para links */
            text-decoration: none;
            font-weight: bold;
        }
        .custom-footer a:hover {
            text-decoration: underline;
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