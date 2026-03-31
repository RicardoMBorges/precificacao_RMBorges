import io
import re
import unicodedata
from typing import Dict, Tuple, Optional
from pathlib import Path

import pandas as pd
import streamlit as st


# -------------------------
# Formatting / parsing
# -------------------------
def br_money(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def to_float(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return None
    s = s.replace("R$", "").strip()
    # Convert 1.234,56 -> 1234.56
    if "," in s and re.search(r"\d", s):
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def norm_key(s: str) -> str:
    s = "" if s is None else str(s)
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\([^)]*\)", "", s)   # remove (MeOH)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# -------------------------
# DEFAULT reference tables (pre-loaded)
# -------------------------
def default_consumables_ref() -> pd.DataFrame:
    """
    Custo_unitario = custo por unidade "operacional" definida por você:
      - solventes: R$/mL
      - plásticos/vidros: R$/unidade
      - colunas: R$/corrida (ou R$/amostra se preferir; aqui está por corrida)
      - padrões: R$/unidade (1 kit, 1 frasco)
    """
    rows = [
        # Solventes (R$/mL)
        {"Categoria": "Solventes", "Item": "Água ultrapura", "Fonte": "local", "Formato": 1000, "Preco_unitario": 100.00, "Unidades_por_formato": 1000, "Custo_unitario": 0.18, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "Metanol", "Fonte": "sigmaaldrich", "Formato": 1000, "Preco_unitario": 183.35, "Unidades_por_formato": 1000, "Custo_unitario": 0.18, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "Acetonitrila", "Fonte": "sigmaaldrich", "Formato": 1000, "Preco_unitario": 419.90, "Unidades_por_formato": 1000, "Custo_unitario": 0.42, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "Isopropanol", "Fonte": "sigmaaldrich", "Formato": 1000, "Preco_unitario": 215.65, "Unidades_por_formato": 1000, "Custo_unitario": 0.22, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "MTBE", "Fonte": "sigmaaldrich", "Formato": 1000, "Preco_unitario": 782.80, "Unidades_por_formato": 1000, "Custo_unitario": 0.78, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "Acetato de Etila", "Fonte": "sigmaaldrich", "Formato": 1000, "Preco_unitario": 576.65, "Unidades_por_formato": 1000, "Custo_unitario": 0.58, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "Hexano", "Fonte": "sigmaaldrich", "Formato": 1000, "Preco_unitario": 638.40, "Unidades_por_formato": 1000, "Custo_unitario": 0.64, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "DicloroMetano", "Fonte": "sigmaaldrich", "Formato": 1000, "Preco_unitario": 470.25, "Unidades_por_formato": 1000, "Custo_unitario": 0.47, "Unidade_operacional": "mL"},
        {"Categoria": "Solventes", "Item": "Ácido Fórmico", "Fonte": "sigmaaldrich", "Formato": 50, "Preco_unitario": 1789.80, "Unidades_por_formato": 50, "Custo_unitario": 35.80, "Unidade_operacional": "mL"},
        # Não informado — mas já pré-cadastrado (você atualiza quando quiser)
        {"Categoria": "Solventes", "Item": "Acetato de amônio", "Fonte": "", "Formato": None, "Preco_unitario": None, "Unidades_por_formato": None, "Custo_unitario": None, "Unidade_operacional": "mL"},

        # Plásticos (R$/unidade) — aqui seus “custos por mL” funcionam como “R$/unidade” pois Formato=1000 un
        {"Categoria": "Plásticos", "Item": "Microtubos de 2 mL", "Fonte": "eppendorf", "Formato": 1000, "Preco_unitario": 657.87, "Unidades_por_formato": 1000, "Custo_unitario": 0.66, "Unidade_operacional": "un"},
        {"Categoria": "Plásticos", "Item": "Microtubos de 1.5 mL", "Fonte": "eppendorf", "Formato": 1000, "Preco_unitario": 481.68, "Unidades_por_formato": 1000, "Custo_unitario": 0.48, "Unidade_operacional": "un"},
        {"Categoria": "Plásticos", "Item": "Ponteiras de 1000uL", "Fonte": "eppendorf", "Formato": 1000, "Preco_unitario": 395.59, "Unidades_por_formato": 1000, "Custo_unitario": 0.40, "Unidade_operacional": "un"},
        {"Categoria": "Plásticos", "Item": "Ponteiras de 200uL", "Fonte": "eppendorf", "Formato": 1000, "Preco_unitario": 395.59, "Unidades_por_formato": 1000, "Custo_unitario": 0.40, "Unidade_operacional": "un"},
        {"Categoria": "Plásticos", "Item": "Filtros de seringa (0.45 µm PTFE / PVDF)", "Fonte": "", "Formato": None, "Preco_unitario": None, "Unidades_por_formato": None, "Custo_unitario": None, "Unidade_operacional": "un"},

        # Vidros (R$/unidade)
        {"Categoria": "Vidros", "Item": "vials de 1.5 mL", "Fonte": "BioSci (Thermo Sci)", "Formato": 100, "Preco_unitario": 100.00, "Unidades_por_formato": 100, "Custo_unitario": 1.00, "Unidade_operacional": "un"},
        {"Categoria": "Vidros", "Item": "Insert de 150uL", "Fonte": "sigmaaldrich", "Formato": 100, "Preco_unitario": 627.00, "Unidades_por_formato": 100, "Custo_unitario": 6.27, "Unidade_operacional": "un"},

        # Padrões e Controles (R$/unidade de kit/frasco)
        {"Categoria": "Padrões e Controles", "Item": "GIGA KIT Whishart quantitative metabolomics", "Fonte": "WHISHART", "Formato": 1, "Preco_unitario": 300.00, "Unidades_por_formato": 1, "Custo_unitario": 620.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "GIGA KIT (less samples) Whishart quantitative metabolomics", "Fonte": "WHISHART", "Formato": 1, "Preco_unitario": 300.00, "Unidades_por_formato": 1, "Custo_unitario": 1300.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "PRIME KIT Whishart quantitative metabolomics", "Fonte": "WHISHART", "Formato": 1, "Preco_unitario": 250.00, "Unidades_por_formato": 1, "Custo_unitario": 620.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "Fatty Acid Methyl Esters Standard Mixture", "Fonte": "SMB00937-1ML", "Formato": 1, "Preco_unitario": 1801.00, "Unidades_por_formato": 1, "Custo_unitario": 1801.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "Supelco 37 Component FAME Mix", "Fonte": "CRM47885", "Formato": 1, "Preco_unitario": 665.00, "Unidades_por_formato": 1, "Custo_unitario": 665.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "MEGA KIT Whishart quantitative metabolomics", "Fonte": "WHISHART", "Formato": 1, "Preco_unitario": 0.00, "Unidades_por_formato": 1, "Custo_unitario": 0.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "Mass Spectrometry Metabolite Library (MSMLS-1EA)", "Fonte": "Sigma (IROA)", "Formato": 1, "Preco_unitario": 58030.00, "Unidades_por_formato": 1, "Custo_unitario": 58030.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "TCA Cycle Metabolite Library (ML0010-1KT)", "Fonte": "Sigma", "Formato": 1, "Preco_unitario": 6929.00, "Unidades_por_formato": 1, "Custo_unitario": 6929.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "Aspartate Metabolite Library (ML0015-1KT)", "Fonte": "Sigma", "Formato": 1, "Preco_unitario": 5198.00, "Unidades_por_formato": 1, "Custo_unitario": 5198.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "Polar Metabolites QC Mix (SBR00055-0.2ML)", "Fonte": "Sigma", "Formato": 1, "Preco_unitario": 2213.00, "Unidades_por_formato": 1, "Custo_unitario": 2213.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "Bile Acids Standard Mixture (SMB00967-1ML)", "Fonte": "Sigma", "Formato": 1, "Preco_unitario": 1409.00, "Unidades_por_formato": 1, "Custo_unitario": 1409.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "13C-Short Chain Fatty Acids Plasma Mixture (SBR00034-1ML)", "Fonte": "Sigma", "Formato": 1, "Preco_unitario": 2098.00, "Unidades_por_formato": 1, "Custo_unitario": 2098.00, "Unidade_operacional": "un"},
        {"Categoria": "Padrões e Controles", "Item": "Deuterated Amino Acid Standard Mixture (SMB00917-10ML)", "Fonte": "Sigma", "Formato": 1, "Preco_unitario": 2301.00, "Unidades_por_formato": 1, "Custo_unitario": 2301.00, "Unidade_operacional": "un"},

        # Colunas HPLC (R$/corrida)
        {"Categoria": "Colunas HPLC", "Item": "ACQUITY UPLC HSS T3 Column, 2.1 mm X 50 mm", "Fonte": "Waters", "Formato": 800, "Preco_unitario": 8000.00, "Unidades_por_formato": 800, "Custo_unitario": 10.00, "Unidade_operacional": "corrida"},
        {"Categoria": "Colunas HPLC", "Item": "ACQUITY UPLC HSS T3 Column, 2.1 mm X 150 mm", "Fonte": "Waters", "Formato": 800, "Preco_unitario": 8690.00, "Unidades_por_formato": 800, "Custo_unitario": 10.86, "Unidade_operacional": "corrida"},
        {"Categoria": "Colunas HPLC", "Item": "ACQUITY UPLC BEH HILIC Column, 1 mm X 50 mm", "Fonte": "Waters", "Formato": 800, "Preco_unitario": 8000.00, "Unidades_por_formato": 800, "Custo_unitario": 10.00, "Unidade_operacional": "corrida"},
        {"Categoria": "Colunas HPLC", "Item": "ACQUITY UPLC BEH HILIC Column, 2.1 mm X 150 mm", "Fonte": "Waters", "Formato": 800, "Preco_unitario": 8690.00, "Unidades_por_formato": 800, "Custo_unitario": 10.86, "Unidade_operacional": "corrida"},
        {"Categoria": "Colunas HPLC", "Item": "ACQUITY UPLC CSH C18 Column, 2.1 mm X 100 mm", "Fonte": "Waters", "Formato": 800, "Preco_unitario": 8690.00, "Unidades_por_formato": 800, "Custo_unitario": 10.86, "Unidade_operacional": "corrida"},

        # Colunas GC (0 por enquanto)
        {"Categoria": "Colunas GC", "Item": "COLUNA GC DB-5MS ULTRA INERTE 30M X 0,25MM X 0,25UM", "Fonte": "Hexis", "Formato": 800, "Preco_unitario": 0.00, "Unidades_por_formato": 800, "Custo_unitario": 0.00, "Unidade_operacional": "corrida"},
        {"Categoria": "Colunas GC", "Item": "COLUNA GC CARBOWAX 20M 30M X 0,25MM X 0,25UM", "Fonte": "Hexis", "Formato": 800, "Preco_unitario": 0.00, "Unidades_por_formato": 800, "Custo_unitario": 0.00, "Unidade_operacional": "corrida"},
    ]
    return pd.DataFrame(rows)


def default_instrument_ref() -> pd.DataFrame:
    rows = [
        {"Categoria": "Aquisição LC–MS/MS (terceirizado)", "Servico": "CEMBIO", "Formato": 40, "Preco_unitario_60min": 100.00, "Custo_por_amostra": 66.67},
        {"Categoria": "Aquisição LC–QQQ (terceirizado)", "Servico": "FIRJAN", "Formato": 40, "Preco_unitario_60min": 130.00, "Custo_por_amostra": 86.66}
    ]
    return pd.DataFrame(rows)

# -------------------------
# Help texts / explainers
# -------------------------

HELP_TEXTS = {
    "n_samples": """
Número de amostras biológicas reais do estudo.
Essas amostras normalmente correspondem às amostras experimentais principais
que serão preparadas, injetadas e cobradas.
""",

    "n_qc": """
Número de amostras de controle de qualidade (QC) incluídas no estudo.
Esses QCs entram no total de preparações/injeções e, portanto, também entram
no cálculo de consumo e de custo quando o parâmetro estiver definido por amostra.
""",

    "n_blank": """
Número de blanks analíticos.
Blanks também podem consumir solventes, plásticos, tempo de instrumento e corridas,
dependendo da estratégia analítica adotada. Por isso, neste app eles também entram
no total de amostras/injeções a cobrar.
""",

    "solventes": """
Nesta seção você informa os solventes usados no estudo.

**Como preencher:**
- Escolha o solvente na lista de referência.
- Defina se a quantidade será informada como:
  - **mL por amostra**: o volume será multiplicado pelo número total de amostras/injeções.
  - **mL total**: o volume será usado diretamente, sem multiplicação.

**Como o custo é calculado:**
1. O app busca o custo de referência do solvente.
2. Esse custo é obtido a partir de:
   **Preço_unitario / Formato**
   Ex.: frasco de R$ 420,00 com 1000 mL → custo de referência = R$ 0,42/mL
3. Depois:
   - se o modo for **mL por amostra**:
     **custo = (mL por amostra × total de amostras) × custo por mL**
   - se o modo for **mL total**:
     **custo = mL total × custo por mL**
""",

    "plasticos": """
Nesta seção você informa consumíveis plásticos, como microtubos, ponteiras e filtros.

**Como preencher:**
- Escolha o item.
- Defina se a quantidade será:
  - **unidades por amostra**
  - **unidades total**

**Como o custo é calculado:**
1. O custo unitário de referência é calculado como:
   **Preço_unitario / Formato**
   Ex.: caixa com 1000 ponteiras por R$ 395,59 → custo = R$ 0,39559 por unidade
2. Depois:
   - **unidades por amostra**:
     **custo = (unidades por amostra × total de amostras) × custo por unidade**
   - **unidades total**:
     **custo = unidades totais × custo por unidade**
""",

    "vidros": """
Nesta seção você informa vials, inserts e outros itens de vidro.

**Como o custo é calculado:**
A lógica é a mesma dos plásticos:
- custo unitário de referência = **Preço_unitario / Formato**
- depois o valor total depende se você informou:
  - **unidades por amostra**
  - **unidades total**
""",

    "padroes": """
Nesta seção você informa padrões, controles e kits.

**Como preencher:**
- Em geral, esses itens são melhor representados como **unidades total**
  (por exemplo, 1 kit ou 1 frasco para o estudo inteiro).
- Mas o app também permite **unidades por amostra**, se isso fizer sentido
  para a sua lógica de cobrança.

**Como o custo é calculado:**
- custo unitário de referência = **Preço_unitario / Formato**
- depois:
  - **unidades total**:
    **custo = quantidade total × custo por unidade**
  - **unidades por amostra**:
    **custo = (quantidade por amostra × total de amostras) × custo por unidade**
""",

    "colunas": """
Nesta seção você informa o uso de colunas cromatográficas.

**Como preencher:**
- O modo mais comum é **corridas total**.
- Isso é útil quando o custo da coluna foi convertido para custo por corrida.

**Como o custo é calculado:**
1. O custo de referência normalmente vem de:
   **Preço_unitario / Formato**
2. Nesse caso, o campo `Formato` representa a vida útil estimada em corridas.
   Ex.: coluna de R$ 8.000,00 com vida útil estimada em 800 corridas
   → custo de referência = R$ 10,00 por corrida
3. Depois:
   - **corridas total**:
     **custo = número de corridas × custo por corrida**
   - **unidades total**:
     **custo = unidades × custo de referência**
""",

    "instrumentacao": """
Nesta seção você informa serviços de instrumentação cobrados por amostra.

**Como o custo é calculado:**
- O app usa diretamente o campo **Custo_por_amostra** da tabela de referência.
- Depois multiplica pelo número total de amostras/injeções.

**Fórmula:**
**custo = total de amostras × custo por amostra do serviço**

Exemplo:
- custo por amostra = R$ 66,67
- total de amostras = 96
- custo total = 96 × 66,67
""",

    "orcamento_manual": """
Na aba de orçamento, o campo **Custo (manual)** substitui o custo calculado automaticamente.
Isso é útil quando você quer:
- arredondar valores
- corrigir um valor específico
- aplicar uma lógica comercial diferente do custo técnico puro
"""
}

# -------------------------
# Dictionary builder
# -------------------------
def build_price_dict(cons_ref: pd.DataFrame, inst_ref: pd.DataFrame):
    """
    Regra:
      Custo_unitario = Preco_unitario / Formato
    (se ambos existirem). Caso contrário, tenta usar Custo_unitario como fallback.
    """
    cons = {}

    for _, r in cons_ref.iterrows():
        item = norm_key(r.get("Item"))
        if not item:
            continue

        preco = to_float(r.get("Preco_unitario"))
        unidades = to_float(r.get("Formato"))
        custo = to_float(r.get("Custo_unitario"))

        # regra principal
        if preco is not None and unidades is not None and unidades != 0:
            cons[item] = float(preco) / float(unidades)
        # fallback (caso você deixe alguns campos vazios)
        elif custo is not None:
            cons[item] = float(custo)
        # senão: fica ausente (None) e o orçamento mostrará em branco

    inst = {}
    for _, r in inst_ref.iterrows():
        svc = norm_key(r.get("Servico"))
        if not svc:
            continue

        val = to_float(r.get("Custo_por_amostra"))
        if val is not None:
            inst[svc] = float(val)

    return cons, inst


# -------------------------
# App
# -------------------------
st.set_page_config(page_title="Precificação - Central Analítica", layout="wide")
st.title("Precificação — Referências pré-carregadas + parâmetros + orçamento")

# Initialize session defaults once
if "cons_ref" not in st.session_state:
    st.session_state.cons_ref = default_consumables_ref()
if "inst_ref" not in st.session_state:
    st.session_state.inst_ref = default_instrument_ref()

# Sidebar: LOGOs (optional)
STATIC_DIR = Path(__file__).parent / "static"
for logo_name in ["LAABio.png"]: #"logo_massQL.png", 
    p = STATIC_DIR / logo_name
    try:
        from PIL import Image
        st.sidebar.image(Image.open(p), use_container_width=True)
    except Exception:
        pass


# Sidebar: optional upload to update references
st.sidebar.header("Atualizar referências (opcional)")
uploaded = st.sidebar.file_uploader("Enviar Excel para atualizar referências (se necessário)", type=["xlsx"])
if st.sidebar.button("Resetar para defaults"):
    st.session_state.cons_ref = default_consumables_ref()
    st.session_state.inst_ref = default_instrument_ref()
    st.sidebar.success("Defaults restaurados.")

st.sidebar.caption("Se você não fizer upload, o app usa os valores pré-carregados.")

tabs = st.tabs(["Parâmetros do estudo", "Orçamento", "Exportar", "Preços de referência"])

with tabs[3]:
    st.subheader("Preços de referência (já pré-carregados — edite apenas se necessário)")

    st.markdown("### Consumíveis")
    st.session_state.cons_ref = st.data_editor(
        st.session_state.cons_ref,
        use_container_width=True,
        num_rows="dynamic",
        key="cons_ref_editor"
    )

    st.markdown("### Instrumentação (custo por amostra)")
    st.session_state.inst_ref = st.data_editor(
        st.session_state.inst_ref,
        use_container_width=True,
        num_rows="dynamic",
        key="inst_ref_editor"
    )

    st.info(
        "O campo **Custo_unitario** em Consumíveis é o valor operacional usado no cálculo:\n"
        "- Solventes: R$/mL\n"
        "- Plásticos/Vidros: R$/unidade\n"
        "- Colunas: R$/corrida\n"
        "- Padrões: R$/kit (1 un)\n"
        "Você pode ajustar isso conforme sua lógica interna."
    )


with tabs[0]:
    st.subheader("Parâmetros do estudo")

    with st.expander("Guia rápido de preenchimento desta aba", expanded=True):
        st.markdown("""
    Preencha esta aba para definir **como o estudo consome recursos**.
    
    A lógica do app é:
    
    1. Você define o número total de amostras/injeções:
       **amostras biológicas + QCs + blanks**
    2. Você informa o consumo de cada categoria:
       - solventes
       - plásticos
       - vidros
       - padrões/controles
       - colunas
       - instrumentação
    3. O app transforma os preços de referência em custo operacional:
       - consumíveis: geralmente **Preço_unitario / Formato**
       - instrumentação: **Custo_por_amostra**
    4. O orçamento final é calculado automaticamente.
    
    Use os expanders de cada seção para entender a lógica de cálculo de cada parâmetro.
    """)
    
    c1, c2, c3 = st.columns(3)

    with c1:
        n_samples = st.number_input(
            "Número de amostras (biológicas)",
            min_value=0,
            value=80,
            step=1,
            key="n_samples",
            help=HELP_TEXTS["n_samples"],
        )

    with c2:
        n_qc = st.number_input(
            "Número de QCs (somar)",
            min_value=0,
            value=0,
            step=1,
            key="n_qc",
            help=HELP_TEXTS["n_qc"],
        )

    with c3:
        n_blank = st.number_input(
            "Número de blanks (opcional)",
            min_value=0,
            value=0,
            step=1,
            key="n_blank",
            help=HELP_TEXTS["n_blank"],
        )

    n_total = int(n_samples + n_qc + n_blank)
    st.metric("Total de injeções/amostras a cobrar", n_total)

    # ---------- build selectable lists from reference tables ----------
    cons_ref_df = st.session_state.cons_ref.copy()
    inst_ref_df = st.session_state.inst_ref.copy()

    # Safety: guarantee Categoria exists
    if "Categoria" not in cons_ref_df.columns:
        cons_ref_df["Categoria"] = ""

    # Normalized category helper
    cat_norm = cons_ref_df["Categoria"].astype(str).str.strip().str.lower()

    def items_by_category(cat_name: str):
        mask = cat_norm.eq(cat_name.strip().lower())
        return sorted(
            [x for x in cons_ref_df.loc[mask, "Item"].dropna().astype(str).str.strip().unique().tolist() if x]
        )

    # Category options
    solvent_options = items_by_category("Solventes")
    plastic_options = items_by_category("Plásticos")
    glass_options = items_by_category("Vidros")
    standards_options = items_by_category("Padrões e Controles")

    # Colunas = juntar HPLC + GC
    hplc_cols = items_by_category("Colunas HPLC")
    gc_cols = items_by_category("Colunas GC")
    columns_options = sorted(list(dict.fromkeys(hplc_cols + gc_cols)))  # unique preserving order-ish

    # Fallback: all items
    cons_options_all = sorted(
        [x for x in cons_ref_df.get("Item", pd.Series(dtype=str)).dropna().astype(str).str.strip().unique().tolist() if x]
    )

    # Instrumentation services options
    inst_options = sorted(
        [x for x in inst_ref_df.get("Servico", pd.Series(dtype=str)).dropna().astype(str).str.strip().unique().tolist() if x]
    )

    # ---------- ensure parameter tables exist ----------
    if "solv_table" not in st.session_state:
        st.session_state.solv_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])

    if "plast_table" not in st.session_state:
        st.session_state.plast_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])

    if "glass_table" not in st.session_state:
        st.session_state.glass_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])

    if "std_table" not in st.session_state:
        st.session_state.std_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])

    if "col_table" not in st.session_state:
        st.session_state.col_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])

    if "inst_table" not in st.session_state:
        st.session_state.inst_table = pd.DataFrame(columns=["Servico", "Incluir", "Observacao"])

    # ==========================================================
    # 1) SOLVENTES (como está)
    # ==========================================================
    st.markdown("### Solventes e volumes")
    st.caption("Escolha itens a partir da tabela de referência. Use 'mL por amostra' ou 'mL total'.")

    add1, add2, add3, add4 = st.columns([3, 2, 2, 1])
    with add1:
        sel_solvent = st.selectbox(
            "Adicionar solvente",
            options=solvent_options if solvent_options else cons_options_all,
            index=0 if (solvent_options or cons_options_all) else None,
            key="sel_solvent_item",
        )
    with add2:
        sel_solvent_mode = st.selectbox(
            "Modo",
            options=["mL por amostra", "mL total"],
            index=0,
            key="sel_solvent_mode",
        )
    with add3:
        sel_solvent_qty = st.number_input(
            "Quantidade (mL)",
            min_value=0.0,
            value=0.0,
            step=0.1,
            key="sel_solvent_qty",
        )
    with add4:
        if st.button("Adicionar", key="btn_add_solvent"):
            if sel_solvent:
                st.session_state.solv_table = pd.concat(
                    [
                        st.session_state.solv_table,
                        pd.DataFrame([{"Item": sel_solvent, "Modo": sel_solvent_mode, "Quantidade": float(sel_solvent_qty)}]),
                    ],
                    ignore_index=True,
                )

    st.session_state.solv_table = st.data_editor(
        st.session_state.solv_table,
        use_container_width=True,
        num_rows="dynamic",
        key="solv_table_editor",
    )

    # Clear button
    if st.button("Limpar lista de solventes", key="clear_solv"):
        st.session_state.solv_table = st.session_state.solv_table.iloc[0:0].copy()

    st.divider()

    # ==========================================================
    # 2) PLÁSTICOS
    # ==========================================================
    st.markdown("### Plásticos")
    st.caption("Modo: unidades por amostra ou unidades total.")
    with st.expander("Como preencher plásticos e como o custo é calculado"):
        st.markdown(HELP_TEXTS["plasticos"])

    p1, p2, p3, p4 = st.columns([3, 2, 2, 1])
    with p1:
        sel_plast = st.selectbox(
            "Adicionar plástico",
            options=plastic_options if plastic_options else cons_options_all,
            index=0 if (plastic_options or cons_options_all) else None,
            key="sel_plast_item",
        )
    with p2:
        sel_plast_mode = st.selectbox(
            "Modo",
            options=["unidades por amostra", "unidades total"],
            index=0,
            key="sel_plast_mode",
        )
    with p3:
        sel_plast_qty = st.number_input(
            "Quantidade",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="sel_plast_qty",
        )
    with p4:
        if st.button("Adicionar", key="btn_add_plast"):
            if sel_plast:
                st.session_state.plast_table = pd.concat(
                    [
                        st.session_state.plast_table,
                        pd.DataFrame([{"Item": sel_plast, "Modo": sel_plast_mode, "Quantidade": float(sel_plast_qty)}]),
                    ],
                    ignore_index=True,
                )

    st.session_state.plast_table = st.data_editor(
        st.session_state.plast_table,
        use_container_width=True,
        num_rows="dynamic",
        key="plast_table_editor",
    )

    if st.button("Limpar lista de plásticos", key="clear_plast"):
        st.session_state.plast_table = st.session_state.plast_table.iloc[0:0].copy()

    st.divider()

    # ==========================================================
    # 3) VIDROS
    # ==========================================================
    st.markdown("### Vidros")
    st.caption("Modo: unidades por amostra ou unidades total.")
    with st.expander("Como preencher vidros e como o custo é calculado"):
        st.markdown(HELP_TEXTS["vidros"])
        
    g1, g2, g3, g4 = st.columns([3, 2, 2, 1])
    with g1:
        sel_glass = st.selectbox(
            "Adicionar vidro",
            options=glass_options if glass_options else cons_options_all,
            index=0 if (glass_options or cons_options_all) else None,
            key="sel_glass_item",
        )
    with g2:
        sel_glass_mode = st.selectbox(
            "Modo",
            options=["unidades por amostra", "unidades total"],
            index=0,
            key="sel_glass_mode",
        )
    with g3:
        sel_glass_qty = st.number_input(
            "Quantidade",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="sel_glass_qty",
        )
    with g4:
        if st.button("Adicionar", key="btn_add_glass"):
            if sel_glass:
                st.session_state.glass_table = pd.concat(
                    [
                        st.session_state.glass_table,
                        pd.DataFrame([{"Item": sel_glass, "Modo": sel_glass_mode, "Quantidade": float(sel_glass_qty)}]),
                    ],
                    ignore_index=True,
                )

    st.session_state.glass_table = st.data_editor(
        st.session_state.glass_table,
        use_container_width=True,
        num_rows="dynamic",
        key="glass_table_editor",
    )

    if st.button("Limpar lista de vidros", key="clear_glass"):
        st.session_state.glass_table = st.session_state.glass_table.iloc[0:0].copy()

    st.divider()

    # ==========================================================
    # 4) PADRÕES E CONTROLES
    # ==========================================================
    st.markdown("### Padrões e Controles")
    st.caption("Modo típico: unidades total (kits/frasco). Se quiser por amostra, também pode.")
    with st.expander("Como preencher padrões/controles e como o custo é calculado"):
        st.markdown(HELP_TEXTS["padroes"])
    s1, s2, s3, s4 = st.columns([3, 2, 2, 1])
    with s1:
        sel_std = st.selectbox(
            "Adicionar padrão/controle",
            options=standards_options if standards_options else cons_options_all,
            index=0 if (standards_options or cons_options_all) else None,
            key="sel_std_item",
        )
    with s2:
        sel_std_mode = st.selectbox(
            "Modo",
            options=["unidades total", "unidades por amostra"],
            index=0,
            key="sel_std_mode",
        )
    with s3:
        sel_std_qty = st.number_input(
            "Quantidade",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="sel_std_qty",
        )
    with s4:
        if st.button("Adicionar", key="btn_add_std"):
            if sel_std:
                st.session_state.std_table = pd.concat(
                    [
                        st.session_state.std_table,
                        pd.DataFrame([{"Item": sel_std, "Modo": sel_std_mode, "Quantidade": float(sel_std_qty)}]),
                    ],
                    ignore_index=True,
                )

    st.session_state.std_table = st.data_editor(
        st.session_state.std_table,
        use_container_width=True,
        num_rows="dynamic",
        key="std_table_editor",
    )

    if st.button("Limpar lista de padrões/controles", key="clear_std"):
        st.session_state.std_table = st.session_state.std_table.iloc[0:0].copy()

    st.divider()

    # ==========================================================
    # 5) COLUNAS
    # ==========================================================
    st.markdown("### Colunas")
    st.caption("Modo típico: corridas total (vida útil em corridas).")
    with st.expander("Como preencher colunas e como o custo é calculado"):
        st.markdown(HELP_TEXTS["colunas"])
    c01, c02, c03, c04 = st.columns([3, 2, 2, 1])
    with c01:
        sel_col = st.selectbox(
            "Adicionar coluna",
            options=columns_options if columns_options else cons_options_all,
            index=0 if (columns_options or cons_options_all) else None,
            key="sel_col_item",
        )
    with c02:
        sel_col_mode = st.selectbox(
            "Modo",
            options=["corridas total", "unidades total"],
            index=0,
            key="sel_col_mode",
        )
    with c03:
        sel_col_qty = st.number_input(
            "Quantidade (corridas ou unidades)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="sel_col_qty",
        )
    with c04:
        if st.button("Adicionar", key="btn_add_col"):
            if sel_col:
                st.session_state.col_table = pd.concat(
                    [
                        st.session_state.col_table,
                        pd.DataFrame([{"Item": sel_col, "Modo": sel_col_mode, "Quantidade": float(sel_col_qty)}]),
                    ],
                    ignore_index=True,
                )

    st.session_state.col_table = st.data_editor(
        st.session_state.col_table,
        use_container_width=True,
        num_rows="dynamic",
        key="col_table_editor",
    )

    if st.button("Limpar lista de colunas", key="clear_col"):
        st.session_state.col_table = st.session_state.col_table.iloc[0:0].copy()

    st.divider()

    # ==========================================================
    # Instrumentação (serviços) - mantido como estava
    # ==========================================================
    st.markdown("### Instrumentação (serviços)")
    st.caption("Escolha serviços a partir da tabela de referência.")
    with st.expander("Como preencher instrumentação e como o custo é calculado"):
        st.markdown(HELP_TEXTS["instrumentacao"])
    addi1, addi2, addi3, addi4 = st.columns([3, 1, 3, 1])
    with addi1:
        sel_inst = st.selectbox(
            "Adicionar serviço",
            options=inst_options,
            index=0 if inst_options else None,
            key="sel_inst_service",
        )
    with addi2:
        sel_inst_include = st.checkbox("Incluir", value=True, key="sel_inst_include")
    with addi3:
        sel_inst_obs = st.text_input("Observação", value="", key="sel_inst_obs")
    with addi4:
        if st.button("Adicionar", key="btn_add_inst"):
            if sel_inst:
                st.session_state.inst_table = pd.concat(
                    [
                        st.session_state.inst_table,
                        pd.DataFrame([{"Servico": sel_inst, "Incluir": bool(sel_inst_include), "Observacao": sel_inst_obs}]),
                    ],
                    ignore_index=True,
                )

    st.session_state.inst_table = st.data_editor(
        st.session_state.inst_table,
        use_container_width=True,
        num_rows="dynamic",
        key="inst_table_editor",
    )

    if st.button("Limpar lista de serviços", key="clear_inst"):
        st.session_state.inst_table = st.session_state.inst_table.iloc[0:0].copy()
        
##########################################################
##########################################################
with tabs[1]:
    st.subheader("Orçamento (calculado)")

    with st.expander("Como o orçamento é calculado", expanded=False):
        st.markdown("""
    O orçamento é calculado a partir dos parâmetros informados na aba anterior.
    
    **Regras gerais:**
    - Para consumíveis, o custo de referência geralmente vem de:
      **Preço_unitario / Formato**
    - Para instrumentação, o custo vem de:
      **Custo_por_amostra**
    - Quando o modo é **por amostra**, o app multiplica pelo total de amostras/injeções.
    - Quando o modo é **total**, o app usa diretamente a quantidade informada.
    
    **Importante:**
    Se o campo **Custo (manual)** for preenchido, ele substitui o custo calculado automaticamente.
    """)

    # --- ensure parameter tables exist (avoid first-run issues) ---
    if "solv_table" not in st.session_state:
        st.session_state.solv_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])
    if "plast_table" not in st.session_state:
        st.session_state.plast_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])
    if "glass_table" not in st.session_state:
        st.session_state.glass_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])
    if "std_table" not in st.session_state:
        st.session_state.std_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])
    if "col_table" not in st.session_state:
        st.session_state.col_table = pd.DataFrame(columns=["Item", "Modo", "Quantidade"])

    if "inst_table" not in st.session_state:
        st.session_state.inst_table = pd.DataFrame(columns=["Servico", "Incluir", "Observacao"])

    cons_dict, inst_dict = build_price_dict(st.session_state.cons_ref, st.session_state.inst_ref)
    n_total = int(st.session_state.n_samples + st.session_state.n_qc + st.session_state.n_blank)

    rows = []

    # -------------------------
    # Helper to add "unit-based" categories
    # -------------------------
    def add_unit_rows(df: pd.DataFrame, categoria_label: str, mode_labels: Tuple[str, str], qty_suffix: str = ""):
        """
        mode_labels:
          (per_sample_token, total_token)
        qty_suffix: string appended to qty label, e.g. " un" or "".
        """
        if df is None or df.empty:
            return

        per_sample_token, total_token = mode_labels

        for _, r in df.iterrows():
            item = str(r.get("Item", "")).strip()
            mode = str(r.get("Modo", "")).strip().lower()
            qty = to_float(r.get("Quantidade")) or 0.0

            unit_cost = cons_dict.get(norm_key(item))

            if per_sample_token in mode:
                qty_total = qty * n_total
                qty_label = f"{qty:g}{qty_suffix}/amostra × {n_total} = {qty_total:g}{qty_suffix}"
            else:
                qty_total = qty
                qty_label = f"{qty_total:g}{qty_suffix} (total)"

            cost_calc = (qty_total * unit_cost) if unit_cost is not None else None

            rows.append({
                "Categoria": categoria_label,
                "Item/Serviço": item,
                "Quantidade (calc)": qty_label,
                "Custo unitário (ref)": unit_cost,
                "Custo (calc)": cost_calc,
                "Custo (manual)": None,
                "Observações": ""
            })

    # -------------------------
    # Solventes
    # -------------------------
    if st.session_state.solv_table is not None and not st.session_state.solv_table.empty:
        for _, r in st.session_state.solv_table.iterrows():
            item = str(r.get("Item", "")).strip()
            mode = str(r.get("Modo", "")).strip().lower()
            qty = to_float(r.get("Quantidade")) or 0.0  # mL

            unit_cost = cons_dict.get(norm_key(item))

            if "por amostra" in mode:
                qty_total = qty * n_total
                qty_label = f"{qty:g} mL/amostra × {n_total} = {qty_total:g} mL"
            else:
                qty_total = qty
                qty_label = f"{qty_total:g} mL (total)"

            cost_calc = (qty_total * unit_cost) if unit_cost is not None else None

            rows.append({
                "Categoria": "Consumíveis - Solventes",
                "Item/Serviço": item,
                "Quantidade (calc)": qty_label,
                "Custo unitário (ref)": unit_cost,
                "Custo (calc)": cost_calc,
                "Custo (manual)": None,
                "Observações": ""
            })

    # -------------------------
    # Plásticos (un)
    # -------------------------
    add_unit_rows(
        st.session_state.plast_table,
        categoria_label="Consumíveis - Plásticos",
        mode_labels=("por amostra", "total"),
        qty_suffix=" un"
    )

    # -------------------------
    # Vidros (un)
    # -------------------------
    add_unit_rows(
        st.session_state.glass_table,
        categoria_label="Consumíveis - Vidros",
        mode_labels=("por amostra", "total"),
        qty_suffix=" un"
    )

    # -------------------------
    # Padrões e Controles (un)
    # -------------------------
    # Aceita "unidades total" e "unidades por amostra" (você já usa isso na UI)
    add_unit_rows(
        st.session_state.std_table,
        categoria_label="Consumíveis - Padrões e Controles",
        mode_labels=("por amostra", "total"),
        qty_suffix=" un"
    )

    # -------------------------
    # Colunas (corridas total ou unidades total)
    # -------------------------
    if st.session_state.col_table is not None and not st.session_state.col_table.empty:
        for _, r in st.session_state.col_table.iterrows():
            item = str(r.get("Item", "")).strip()
            mode = str(r.get("Modo", "")).strip().lower()
            qty = to_float(r.get("Quantidade")) or 0.0

            unit_cost = cons_dict.get(norm_key(item))

            # aqui não faz sentido "por amostra" normalmente; o modo é informativo
            if "corridas" in mode:
                qty_total = qty
                qty_label = f"{qty_total:g} corridas (total)"
            else:
                qty_total = qty
                qty_label = f"{qty_total:g} un (total)"

            cost_calc = (qty_total * unit_cost) if unit_cost is not None else None

            rows.append({
                "Categoria": "Consumíveis - Colunas",
                "Item/Serviço": item,
                "Quantidade (calc)": qty_label,
                "Custo unitário (ref)": unit_cost,
                "Custo (calc)": cost_calc,
                "Custo (manual)": None,
                "Observações": ""
            })

    # -------------------------
    # Instrumentation
    # -------------------------
    if st.session_state.inst_table is not None and not st.session_state.inst_table.empty:
        for _, r in st.session_state.inst_table.iterrows():
            if not bool(r.get("Incluir", True)):
                continue

            svc = str(r.get("Servico", "")).strip()
            obs = str(r.get("Observacao", "")).strip()

            cps = inst_dict.get(norm_key(svc))
            cost_calc = (n_total * cps) if cps is not None else None

            rows.append({
                "Categoria": "Instrumentação",
                "Item/Serviço": svc,
                "Quantidade (calc)": f"{n_total} amostras",
                "Custo unitário (ref)": cps,
                "Custo (calc)": cost_calc,
                "Custo (manual)": None,
                "Observações": obs
            })

    # -------------------------
    # Build budget with fixed schema (even if rows is empty)
    # -------------------------
    BUDGET_COLS = [
        "Categoria",
        "Item/Serviço",
        "Quantidade (calc)",
        "Custo unitário (ref)",
        "Custo (calc)",
        "Custo (manual)",
        "Observações",
    ]
    budget = pd.DataFrame(rows, columns=BUDGET_COLS)

    st.caption("Se você preencher **Custo (manual)**, ele substitui o custo calculado.")
    edited = st.data_editor(budget, use_container_width=True, num_rows="dynamic", key="budget_editor")

    # ---- Safety: ensure Categoria exists after data_editor ----
    if "Categoria" not in edited.columns:
        if "Categoria" in budget.columns and len(budget) == len(edited):
            edited["Categoria"] = budget["Categoria"].values
        else:
            edited["Categoria"] = "Sem categoria"

    # -------------------------
    # Final cost (manual overrides calc)
    # -------------------------
    def final_cost(row):
        m = to_float(row.get("Custo (manual)"))
        c = row.get("Custo (calc)")
        c = float(c) if c is not None and not pd.isna(c) else None
        return m if m is not None else (c if c is not None else 0.0)

    edited["Custo_final"] = edited.apply(final_cost, axis=1)

    total = float(pd.to_numeric(edited["Custo_final"], errors="coerce").fillna(0).sum())
    st.metric("Total do orçamento", br_money(total))

    st.markdown("### Totais por categoria")
    by_cat = (
        edited.groupby("Categoria", dropna=False)["Custo_final"]
        .sum()
        .reset_index()
        .sort_values("Custo_final", ascending=False)
    )
    st.dataframe(by_cat, use_container_width=True)

    st.session_state.budget_final = edited

##########################################################
##########################################################
with tabs[2]:
    st.subheader("Exportar Excel")

    if "budget_final" not in st.session_state:
        st.info("Gere o orçamento na aba **Orçamento**.")
    else:
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            st.session_state.cons_ref.to_excel(writer, sheet_name="REF_Consumiveis", index=False)
            st.session_state.inst_ref.to_excel(writer, sheet_name="REF_Instrumentacao", index=False)

            st.session_state.solv_table.to_excel(writer, sheet_name="PARAM_Solventes", index=False)
            st.session_state.plast_table.to_excel(writer, sheet_name="PARAM_Plasticos", index=False)
            st.session_state.glass_table.to_excel(writer, sheet_name="PARAM_Vidros", index=False)
            st.session_state.std_table.to_excel(writer, sheet_name="PARAM_Padroes_Controles", index=False)
            st.session_state.col_table.to_excel(writer, sheet_name="PARAM_Colunas", index=False)

            st.session_state.inst_table.to_excel(writer, sheet_name="PARAM_Instrumentacao", index=False)
            st.session_state.budget_final.to_excel(writer, sheet_name="ORCAMENTO", index=False)

        st.download_button(
            "Baixar Excel (referências + parâmetros + orçamento)",
            data=out.getvalue(),
            file_name="Precificacao_orcamento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
