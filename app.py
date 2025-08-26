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

    # normaliza nomes de colunas (remove espaços extras invisíveis)
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

    # ======================
    # FILTRAR/RENOMEAR COLUNAS
    # ======================
    mapeamento = {
        "Nome Completo": "Nome",
        "Telefone (31)9xxxx-xxxx": "Telefone",
        "Endereço": "Rua",
        "Unnamed: 9": "Número",
        "Unnamed: 10": "Bairro",
        "Área da Demanda": "Área da Demanda",
        "Resumo da Demanda": "Resumo da Demanda",
        "Servidor Responsável": "Servidor Responsável",
        "Situação da Demanda": "Situação da Demanda",
        "Descrição da Situação": "Descrição da Situação"
        # "Data da Atualização" já está correto
    }

    # Seleciona apenas colunas existentes
    existentes = [c for c in mapeamento if c in df.columns]
    if "Data da Atualização" in df.columns:
        existentes.append("Data da Atualização")

    df = df[existentes].rename(columns=mapeamento)

    # Ordem final das colunas
    ordem = [
        "Nome", "Telefone", "Rua", "Número", "Bairro",
        "Área da Demanda", "Resumo da Demanda", "Servidor Responsável",
        "Situação da Demanda", "Descrição da Situação", "Data da Atualização"
    ]
    df = df[[c for c in ordem if c in df.columns]]

    # Converter e ordenar pela Data da Atualização
    if "Data da Atualização" in df.columns:
        df["Data da Atualização"] = pd.to_datetime(df["Data da Atualização"], errors="coerce", dayfirst=True)
        df = df.sort_values("Data da Atualização", ascending=False)

    # ======================
    # COLORAÇÃO DA SITUAÇÃO
    # ======================
    def highlight_situacao(val):
        if isinstance(val, str):
            v = val.lower()
            if "prejudicado" in v:   return "background-color:#ff4d4d;color:white;font-weight:bold;"
            if "em andamento" in v:  return "background-color:#ffd633;color:black;font-weight:bold;"
            if "solucionado" in v:   return "background-color:#33cc33;color:white;font-weight:bold;"
        return ""

    styled_df = (
        df.style.applymap(highlight_situacao, subset=["Situação da Demanda"])
        if "Situação da Demanda" in df.columns else df
    )

    # ======================
    # EXIBIR TABELA
    # ======================
    st.subheader("📌 Fichas de Atendimento (simplificado)")
    st.dataframe(
        styled_df,
        use_container_width=False,  # largura fixa
        width=1200,                 # ajuste conforme a tela
        height=600                  # altura fixa → rolagem aparece
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
