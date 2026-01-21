import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Callcenter BI Dashboard", layout="wide")
st.title("📊 Callcenter BI Dashboard (Excel / Power BI Mantığı)")

st.info("3 Excel dosyasını yükleyin. Dosya adları önemli değildir. Uygulama kolonları otomatik bulur.")

# ---------------- Upload ----------------
u1, u2, u3 = st.columns(3)
with u1:
    mma_file = st.file_uploader("📂 MMA Excel", type=["xlsx"], key="mma")
with u2:
    ham_file = st.file_uploader("📂 HAM VERİ Excel", type=["xlsx"], key="ham")
with u3:
    sikayet_file = st.file_uploader("📂 ŞİKAYET Excel", type=["xlsx"], key="sikayet")

@st.cache_data
def load_excels(mma_file, ham_file, sikayet_file):
    mma = pd.read_excel(mma_file, sheet_name=None)
    ham = pd.read_excel(ham_file, sheet_name=None)
    sikayet = pd.read_excel(sikayet_file, sheet_name=None)
    return {"MMA": mma, "HAM_VERI": ham, "SIKAYET": sikayet}

def norm(s: str) -> str:
    return str(s).strip().lower().replace(" ", "").replace("_", "").replace("-", "").replace("ı","i").replace("ş","s").replace("ğ","g").replace("ö","o").replace("ü","u").replace("ç","c")

def find_col(df: pd.DataFrame, candidates: list[str]):
    cols = list(df.columns)
    # 1) exact match
    for c in candidates:
        if c in cols:
            return c
    # 2) normalized match
    nmap = {norm(col): col for col in cols}
    for c in candidates:
        key = norm(c)
        if key in nmap:
            return nmap[key]
    return None

def find_best_sheet(sheets: dict, needed_cols_any: list[list[str]]):
    """
    needed_cols_any: örn [[agent adayları], [lider adayları], [lokasyon adayları], [form puan adayları]]
    """
    best = None
    best_score = -1
    for sh, df in sheets.items():
        score = 0
        for group in needed_cols_any:
            if find_col(df, group) is not None:
                score += 1
        if score > best_score:
            best_score = score
            best = (sh, df.copy())
    return best  # (sheet_name, df)

def to_datetime_safe(df: pd.DataFrame, col: str):
    if col and col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def to_numeric_safe(df: pd.DataFrame, col: str):
    if col and col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

if not (mma_file and ham_file and sikayet_file):
    st.warning("Devam etmek için 3 dosyayı da yükleyin.")
    st.stop()

data = load_excels(mma_file, ham_file, sikayet_file)
st.success("Dosyalar yüklendi ✅")

# ---------------- Tabs ----------------
tabBI, tabDATA = st.tabs(["📌 BI Dashboard (Power BI Mantığı)", "📄 Ham Veri (Sheet Görüntüle)"])

# ======================================================================
# TAB: HAM VERİ (sheet seçip birebir gör)
# ======================================================================
with tabDATA:
    st.subheader("Ham Veri Görüntüleme (Excel’deki gibi sheet seç)")
    ds = st.selectbox("Dosya", list(data.keys()), key="ds_view")
    sh = st.selectbox("Sheet", list(data[ds].keys()), key="sh_view")
    df_view = data[ds][sh]
    st.dataframe(df_view, use_container_width=True, height=650)

# ======================================================================
# TAB: BI Dashboard
# ======================================================================
with tabBI:
    st.subheader("Power BI / Pivot Mantığı")

    # ---------- MMA ana tabloyu otomatik bul ----------
    agent_candidates = ["Müşteri Temsilcisi Adı", "AGENT", "Agent", "Temsilci", "Asistan", "Agent Name"]
    lider_candidates = ["Takım Lideri", "TAKIM LİDERİ", "Team Leader", "TL", "Lider"]
    lok_candidates = ["Lokasyon", "LOKASYON", "Location"]
    skill_candidates = ["Skill İsmi", "SKILL", "Skill", "Skill Genel Bilgi", "SKILL GENEL BİLGİ"]
    takim_candidates = ["Takım Adı", "TAKIM ADI", "Team", "Takim"]
    date_candidates  = ["Çağrı Tarih Saati", "Çağrı Tarihi", "Anket Tarihi", "Tarih", "CALL DATE", "Date"]
    form_candidates  = ["Form Puan", "FORM PUAN", "FormPuan", "Form Puanı", "Form Puani", "FORM_PUAN", "PUAN", "Puan"]

    needed = [agent_candidates, lider_candidates, lok_candidates, form_candidates]
    mma_sheet, mma_df = find_best_sheet(data["MMA"], needed)

    st.caption(f"📌 MMA kullanılan sheet: **{mma_sheet}**")

    # Kolonları yakala
    col_agent = find_col(mma_df, agent_candidates)
    col_lider = find_col(mma_df, lider_candidates)
    col_lok   = find_col(mma_df, lok_candidates)
    col_skill = find_col(mma_df, skill_candidates)
    col_takim = find_col(mma_df, takim_candidates)
    col_date  = find_col(mma_df, date_candidates)
    col_form  = find_col(mma_df, form_candidates)

    # Kritik kolon kontrol
    missing = []
    if not col_agent: missing.append("AGENT / Müşteri Temsilcisi Adı")
    if not col_form:  missing.append("Form Puan")
    if missing:
        st.error("❌ Gerekli kolon(lar) bulunamadı: " + ", ".join(missing))
        st.stop()

    # Tip dönüşümleri
    mma_df = to_numeric_safe(mma_df, col_form)
    mma_df = to_datetime_safe(mma_df, col_date) if col_date else mma_df

    # ---------- Sidebar filters (Excel dilimleyici gibi) ----------
    st.sidebar.header("🔎 Filtreler (Slicer)")

    def multiselect_filter(label, df, col):
        if not col or col not in df.columns:
            return []
        opts = sorted(df[col].dropna().unique())
        return st.sidebar.multiselect(label, opts)

    # Cascading mantık: Lokasyon -> Lider -> Takım -> Skill
    fdf = mma_df.copy()

    sel_lok = multiselect_filter("Lokasyon", fdf, col_lok)
    if sel_lok and col_lok:
        fdf = fdf[fdf[col_lok].isin(sel_lok)]

    sel_lider = multiselect_filter("Takım Lideri", fdf, col_lider)
    if sel_lider and col_lider:
        fdf = fdf[fdf[col_lider].isin(sel_lider)]

    sel_takim = multiselect_filter("Takım Adı", fdf, col_takim)
    if sel_takim and col_takim:
        fdf = fdf[fdf[col_takim].isin(sel_takim)]

    sel_skill = multiselect_filter("Skill", fdf, col_skill)
    if sel_skill and col_skill:
        fdf = fdf[fdf[col_skill].isin(sel_skill)]

    # Tarih filtresi
    if col_date and fdf[col_date].notna().any():
        min_d = fdf[col_date].min().date()
        max_d = fdf[col_date].max().date()
        dr = st.sidebar.date_input("Tarih Aralığı", value=(min_d, max_d))
        if dr:
            sd, ed = dr
            fdf = fdf[(fdf[col_date] >= pd.to_datetime(sd)) & (fdf[col_date] < pd.to_datetime(ed) + pd.Timedelta(days=1))]

    st.sidebar.divider()

    # ---------- KPI Cards ----------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Kayıt Adedi", f"{len(fdf):,}".replace(",", "."))
    k2.metric("Aktif Agent", f"{fdf[col_agent].nunique():,}".replace(",", "."))
    k3.metric("Form Puan Ort.", f"{fdf[col_form].mean():.2f}" if fdf[col_form].notna().any() else "—")
    k4.metric("Form Puan Min/Max", f"{fdf[col_form].min():.2f} / {fdf[col_form].max():.2f}" if fdf[col_form].notna().any() else "—")

    st.divider()

    # ---------- "Satırlar / Değerler" (Pivot / Power BI matrix gibi) ----------
    st.markdown("### 🧩 Pivot Mantığı (Satırlar / Değerler)")

    row_dim_map = {
        "Agent": col_agent,
        "Takım Lideri": col_lider,
        "Lokasyon": col_lok,
        "Takım Adı": col_takim,
        "Skill": col_skill,
    }
    # olmayan kolonları listeden çıkar
    row_dim_map = {k: v for k, v in row_dim_map.items() if v is not None}

    v1, v2, v3 = st.columns([2, 2, 1])
    with v1:
        row_dim = st.selectbox("Satırlar (Rows)", list(row_dim_map.keys()), index=0)
    with v2:
        values = st.multiselect(
            "Değerler (Values)",
            ["Kayıt Adedi", "Form Puan Ortalama", "Form Puan Min", "Form Puan Max"],
            default=["Kayıt Adedi", "Form Puan Ortalama"]
        )
    with v3:
        top_n = st.number_input("Top N", min_value=5, max_value=200, value=50, step=5)

    row_col = row_dim_map[row_dim]

    agg = {}
    if "Kayıt Adedi" in values:
        agg["Kayıt Adedi"] = (col_form, "count")
    if "Form Puan Ortalama" in values:
        agg["Form Puan Ortalama"] = (col_form, "mean")
    if "Form Puan Min" in values:
        agg["Form Puan Min"] = (col_form, "min")
    if "Form Puan Max" in values:
        agg["Form Puan Max"] = (col_form, "max")

    pivot = fdf.groupby(row_col, dropna=False).agg(**agg).reset_index()
    # sort by first numeric metric
    sort_col = "Form Puan Ortalama" if "Form Puan Ortalama" in pivot.columns else (pivot.columns[1] if len(pivot.columns) > 1 else row_col)
    pivot = pivot.sort_values(by=sort_col, ascending=False).head(int(top_n))

    st.dataframe(pivot, use_container_width=True, height=520)

    csv = pivot.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Pivot çıktısını CSV indir", csv, "pivot_cikti.csv", "text/csv")

    st.divider()

    # ---------- Grafik (Power BI hissi) ----------
    st.markdown("### 📈 Grafik")
    if "Form Puan Ortalama" in pivot.columns:
        fig = px.bar(pivot, x=row_col, y="Form Puan Ortalama")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Grafik için 'Form Puan Ortalama' değerini seçersen bar chart oluşur.")
