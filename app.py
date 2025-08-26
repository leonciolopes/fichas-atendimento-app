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
    /* Footer */
    .footer { 
        text-align:center; color:white; padding:12px; margin-top:30px; 
        background-color:#002d17; border-radius:8px; font-size:14px;
    }
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

    # normaliza nomes de colunas
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
        # "Data da Atualização" já está correto no CSV
    }

    existentes = [c for c in mapeamento if c in df.columns]
    if "Data da Atualização" in df.columns:
        existentes.append("Data da Atualização")

    df = df[existentes].rename(columns=mapeamento)

    ordem = [
        "Nome", "Telefone", "Rua", "Número", "Bairro",
        "Área da Demanda", "Resumo da Demanda", "Servidor Responsável",
        "Situação da Demanda", "Descrição da Situação", "Data da Atualização"
    ]
    df = df[[c for c in ordem if c in df.columns]]

    if "Data da Atualização" in df.columns:
        df["Data da Atualização"] = pd.to_datetime(df["Data da Atualização"], errors="coerce", dayfirst=True)
        df = df.sort_values("Data da Atualização", ascending=False)

    # ======================
    # COLORAÇÃO DA SITUAÇÃO + CENTRALIZAÇÃO
    # ======================
    def highlight_situacao(val):
        if isinstance(val, str):
            v = val.lower()
            if "prejudicado" in v:   return "background-color:#ff4d4d;color:white;font-weight:bold; text-align:center;"
            if "em andamento" in v:  return "background-color:#ffd633;color:black;font-weight:bold; text-align:center;"
            if "solucionado" in v:   return "background-color:#33cc33;color:white;font-weight:bold; text-align:center;"
        return "text-align:center;"

    if "Situação da Demanda" in df.columns:
        styled_df = (
            df.style
              .applymap(highlight_situacao, subset=["Situação da Demanda"])
              .set_properties(**{"text-align": "center"})  # centraliza células
              .set_table_styles([{"selector":"th","props":[("text-align","center")]}])  # centraliza cabeçalho
        )
    else:
        styled_df = (
            df.style
              .set_properties(**{"text-align": "center"})
              .set_table_styles([{"selector":"th","props":[("text-align","center")]}])
        )

    # ======================
    # EXIBIR TABELA (largura fixa + rolagem horizontal + ocultar índice)
    # ======================
    st.subheader("📌 Fichas de Atendimento (simplificado)")
    st.dataframe(
        styled_df,
        use_container_width=False,
        width=1200,
        height=600,
        hide_index=True  # 🔒 esconde a coluna do índice ("linha 0")
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
        if "Situação da Demanda" in filtrado.columns:
            styled_filtrado = (
                filtrado.style
                    .applymap(highlight_situacao, subset=["Situação da Demanda"])
                    .set_properties(**{"text-align": "center"})
                    .set_table_styles([{"selector":"th","props":[("text-align","center")]}])
            )
        else:
            styled_filtrado = (
                filtrado.style
                    .set_properties(**{"text-align": "center"})
                    .set_table_styles([{"selector":"th","props":[("text-align","center")]}])
            )

        st.dataframe(
            styled_filtrado,
            use_container_width=False,
            width=1200,
            height=600,
            hide_index=True  # 🔒 esconde índice também na tabela filtrada
        )

    # ======================
    # FOOTER PROFISSIONAL
    # ======================
    st.markdown(
        "<div class='footer'>📌 Desenvolvido para o Gabinete Vereador Leôncio Lopes — Todos os direitos reservados</div>",
        unsafe_allow_html=True
    )

    # Botão de logout
    authenticator.logout("Sair", "sidebar")
