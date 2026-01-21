import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Universal BI (Power BI Mantığı)", layout="wide")
st.title("📊 Universal BI Dashboard (Power BI Mantığı)")
st.info("İstediğin Excel dosyalarını yükle. Uygulama kolonları tanıyıp slicer + matrix + grafik üretir.")

# ---------- Helpers ----------
def norm(s: str) -> str:
    return (str(s).strip().lower()
            .replace(" ", "").replace("_", "").replace("-", "")
            .replace("ı","i").replace("ş","s").replace("ğ","g")
            .replace("ö","o").replace("ü","u").replace("ç","c"))

def find_col(df: pd.DataFrame, candidates: list[str]):
    cols = list(df.columns)
    for c in candidates:
        if c in cols:
            return c
    nmap = {norm(c): c for c in cols}
    for cand in candidates:
        k = norm(cand)
        if k in nmap:
            return nmap[k]
    return None

def safe_to_datetime(df, col):
    if col and col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def safe_to_numeric(df, col):
    if col and col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@st.cache_data
def read_excel_all_sheets(uploaded_file):
    # sheet_name=None => tüm sheet'ler dict
    return pd.read_excel(uploaded_file, sheet_name=None)

# ---------- Upload multiple files ----------
files = st.file_uploader("📂 Excel dosyaları (birden fazla seçebilirsin)", type=["xlsx"], accept_multiple_files=True)

if not files:
    st.warning("Devam etmek için en az 1 Excel yükle.")
    st.stop()

# Read all
all_books = {}
for f in files:
    all_books[f.name] = read_excel_all_sheets(f)

tabBI, tabDATA = st.tabs(["📌 BI Dashboard", "📄 Veri Görüntüle"])

# ---------- Tab: Data viewer ----------
with tabDATA:
    st.subheader("Ham Veri (Sheet Görüntüleme)")
    book_name = st.selectbox("Dosya", list(all_books.keys()))
    sheet_name = st.selectbox("Sheet", list(all_books[book_name].keys()))
    st.dataframe(all_books[book_name][sheet_name], use_container_width=True, height=650)

# ---------- Tab: BI ----------
with tabBI:
    st.subheader("Power BI Mantığı: Fact Seç → Kolon Eşleştir → Slicer + Matrix")

    # 1) Fact selection
    book_name = st.selectbox("Ana tablo (Fact) hangi dosyada?", list(all_books.keys()), key="fact_book")
    sheet_name = st.selectbox("Fact sheet", list(all_books[book_name].keys()), key="fact_sheet")
    fact = all_books[book_name][sheet_name].copy()

    st.caption(f"📌 Fact kaynak: **{book_name} / {sheet_name}**")

    cols = list(fact.columns)

    # 2) Auto-detect suggestions (Power BI gibi öneri)
    agent_c = ["Agent", "AGENT", "Müşteri Temsilcisi Adı", "Temsilci", "Asistan", "Kullanıcı", "User", "Personel"]
    leader_c = ["Takım Lideri", "TAKIM LİDERİ", "Team Leader", "TL", "Lider"]
    loc_c    = ["Lokasyon", "LOKASYON", "Location", "Şehir", "Sehir", "City", "Bölge", "Bolge"]
    date_c   = ["Tarih", "Kayıt Tarihi", "Şikayet Tarihi", "Çağrı Tarih Saati", "Çağrı Tarihi", "Date", "Datetime"]
    score_c  = ["Form Puan", "FORM PUAN", "Puan", "Skor", "Score", "Toplam Puan", "Genel Puan", "Ortalama"]

    auto_agent = find_col(fact, agent_c)
    auto_leader = find_col(fact, leader_c)
    auto_loc = find_col(fact, loc_c)
    auto_date = find_col(fact, date_c)
    auto_score = find_col(fact, score_c)

    st.markdown("### 🧷 Kolon Eşleştirme (Power BI Fields gibi)")
    st.caption("Zorunlu: **Puan/Skor** (ortalama almak için). Diğerleri opsiyonel.")

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        col_score = st.selectbox("Puan/Skor (zorunlu)", cols, index=cols.index(auto_score) if auto_score in cols else 0)
    with m2:
        col_agent = st.selectbox("Agent (ops.)", ["(YOK)"] + cols,
                                 index=(["(YOK)"] + cols).index(auto_agent) if auto_agent in cols else 0)
    with m3:
        col_leader = st.selectbox("Takım Lideri (ops.)", ["(YOK)"] + cols,
                                  index=(["(YOK)"] + cols).index(auto_leader) if auto_leader in cols else 0)
    with m4:
        col_loc = st.selectbox("Lokasyon (ops.)", ["(YOK)"] + cols,
                               index=(["(YOK)"] + cols).index(auto_loc) if auto_loc in cols else 0)
    with m5:
        col_date = st.selectbox("Tarih (ops.)", ["(YOK)"] + cols,
                                index=(["(YOK)"] + cols).index(auto_date) if auto_date in cols else 0)

    if col_agent == "(YOK)":
        col_agent = None
    if col_leader == "(YOK)":
        col_leader = None
    if col_loc == "(YOK)":
        col_loc = None
    if col_date == "(YOK)":
        col_date = None

    # Types
    fact = safe_to_numeric(fact, col_score)
    if col_date:
        fact = safe_to_datetime(fact, col_date)

    # 3) Slicers (only for mapped dims)
    st.sidebar.header("🔎 Dilimleyiciler (Slicer)")

    fdf = fact.copy()

    def slicer_multiselect(df, col, label):
        if not col:
            return []
        opts = sorted(df[col].dropna().unique())
        return st.sidebar.multiselect(label, opts)

    # Cascading order: loc -> leader -> agent
    sel_loc = slicer_multiselect(fdf, col_loc, "Lokasyon") if col_loc else []
    if sel_loc and col_loc:
        fdf = fdf[fdf[col_loc].isin(sel_loc)]

    sel_leader = slicer_multiselect(fdf, col_leader, "Takım Lideri") if col_leader else []
    if sel_leader and col_leader:
        fdf = fdf[fdf[col_leader].isin(sel_leader)]

    sel_agent = slicer_multiselect(fdf, col_agent, "Agent") if col_agent else []
    if sel_agent and col_agent:
        fdf = fdf[fdf[col_agent].isin(sel_agent)]

    # Date slicer
    if col_date and fdf[col_date].notna().any():
        min_d = fdf[col_date].min().date()
        max_d = fdf[col_date].max().date()
        dr = st.sidebar.date_input("Tarih Aralığı", value=(min_d, max_d))
        if dr:
            sd, ed = dr
            fdf = fdf[(fdf[col_date] >= pd.to_datetime(sd)) & (fdf[col_date] < pd.to_datetime(ed) + pd.Timedelta(days=1))]

    # 4) KPI
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Kayıt Adedi", f"{len(fdf):,}".replace(",", "."))
    k2.metric("Skor Ort.", f"{fdf[col_score].mean():.2f}" if fdf[col_score].notna().any() else "—")
    k3.metric("Skor Min/Max", f"{fdf[col_score].min():.2f} / {fdf[col_score].max():.2f}" if fdf[col_score].notna().any() else "—")
    k4.metric("Aktif Agent", f"{fdf[col_agent].nunique():,}".replace(",", ".") if col_agent else "—")

    # 5) Matrix / Pivot (Rows + Values)
    st.divider()
    st.markdown("### 🧩 Matrix (Power BI) – Satırlar / Değerler")

    row_dim_map = {"(Seç)": None}
    if col_agent: row_dim_map["Agent"] = col_agent
    if col_leader: row_dim_map["Takım Lideri"] = col_leader
    if col_loc: row_dim_map["Lokasyon"] = col_loc

    # Ayrıca kullanıcı isterse fact içindeki başka kolonları da satır yapabilsin
    extra_cols = st.multiselect("Ek satır kırılımları (ops.)", cols)
    for ec in extra_cols:
        row_dim_map[f"Kolon: {ec}"] = ec

    row_keys = [k for k,v in row_dim_map.items() if v is not None]
    if not row_keys:
        st.warning("Matrix için en az 1 Satır kırılımı seç (Agent/Lokasyon/Lider veya ek kolon).")
        st.stop()

    p1, p2, p3 = st.columns([2,2,1])
    with p1:
        row_dim = st.selectbox("Satırlar (Rows)", row_keys)
    with p2:
        values = st.multiselect(
            "Değerler (Values)",
            ["Kayıt Adedi", "Skor Ortalama", "Skor Min", "Skor Max"],
            default=["Kayıt Adedi", "Skor Ortalama"]
        )
    with p3:
        top_n = st.number_input("Top N", min_value=5, max_value=500, value=50, step=5)

    row_col = row_dim_map[row_dim]

    agg = {}
    if "Kayıt Adedi" in values:
        agg["Kayıt Adedi"] = (col_score, "count")
    if "Skor Ortalama" in values:
        agg["Skor Ortalama"] = (col_score, "mean")
    if "Skor Min" in values:
        agg["Skor Min"] = (col_score, "min")
    if "Skor Max" in values:
        agg["Skor Max"] = (col_score, "max")

    matrix = fdf.groupby(row_col, dropna=False).agg(**agg).reset_index()
    sort_col = "Skor Ortalama" if "Skor Ortalama" in matrix.columns else matrix.columns[1]
    matrix = matrix.sort_values(by=sort_col, ascending=False).head(int(top_n))

    st.dataframe(matrix, use_container_width=True, height=520)

    csv = matrix.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Matrix CSV indir", csv, "matrix.csv", "text/csv")

    # 6) Chart
    st.divider()
    st.markdown("### 📈 Grafik")
    if "Skor Ortalama" in matrix.columns:
        fig = px.bar(matrix, x=row_col, y="Skor Ortalama")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Grafik için 'Skor Ortalama' değerini seç.")
