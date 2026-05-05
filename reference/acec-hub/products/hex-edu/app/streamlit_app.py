"""HEX-EDU — App Streamlit (placeholder).

Uso:
    streamlit run products/hex-edu/app/streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from acec.ingest import ArcGISHubClient

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "manifest.json"


st.set_page_config(
    page_title="HEX-EDU — Inequidade Educacional Carioca em H3",
    layout="wide",
)

st.title("HEX-EDU — Mapa H3 de Inequidade Educacional Carioca")
st.caption(
    "MVP-1 do ACEC-Hub · Decomposição Theil multi-escala · Dados: data.rio (IPP)"
)

# --- Sidebar -----------------------------------------------------------------
with st.sidebar:
    st.header("Controles")
    h3_resolution = st.slider(
        "Resolução H3",
        min_value=5,
        max_value=10,
        value=8,
        help="Resoluções menores = células maiores. Res 8 ≈ 0,7 km².",
    )
    year = st.selectbox("Ano de referência", options=[2010, 2022], index=1)
    indicator = st.selectbox(
        "Indicador",
        options=["IDEB Anos Iniciais", "IDEB Anos Finais", "Taxa de Alfabetização"],
    )

# --- Status do manifest ------------------------------------------------------
st.subheader("Status do pipeline")

col1, col2 = st.columns(2)

with col1:
    if MANIFEST_PATH.exists():
        meta, items = ArcGISHubClient.load_manifest(MANIFEST_PATH)
        st.metric("Itens no manifest", meta.get("total_items", 0))
        st.caption(f"Atualizado: {meta.get('fetched_at')}")
    else:
        st.error("Manifest ausente. Rode `acec manifest refresh`.")

with col2:
    st.info(
        "**MVP em construção** — esta é uma estrutura inicial.\n\n"
        "Próximos passos: ingestão dos itens-base (IDEB por bairro, "
        "alfabetização, escolas municipais) e implementação da decomposição "
        "Theil em `acec.transform.inequality`."
    )

# --- Placeholder da visualização ---------------------------------------------
st.subheader(f"Mapa H3 (res {h3_resolution}) — {indicator} · {year}")
st.warning("Visualização em desenvolvimento.")

st.markdown(
    """
    ### O que esta visualização irá mostrar
    - Mapa de calor H3 do indicador selecionado
    - Decomposição Theil between/within em painel lateral
    - Comparação com unidades administrativas (bairro, RA, CRE)
    - Sensibilidade ao MAUP via curva de inequidade × resolução
    """
)
