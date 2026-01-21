import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Callcenter BI Dashboard", layout="wide")
st.title("📊 Callcenter BI Dashboard (Excel / Power BI Mantığı)")
st.info("3 Excel dosyasını yükleyin. BI ekranında hangi dosya/sheet 'ana tablo' olacak seçebilirsin (Power BI gibi).")

# ---------------- Upload ----------------
c1, c2, c3 = st.columns(3)
with c1:
    mma_file = st.file_uploader("📂 MMA Excel", type=["xlsx"], key="mma")
with c2:
    ham_file = st.file_uploader("📂 HAM VERİ Excel", type=["xlsx"], key="ham")
with c3:
    sikayet_file = st.file_uploader("📂 ŞİKAYET Excel", type=["xlsx"], key="sikayet")

@st.cache_data
def load_excels(mma_file, ham_file, sikayet_file):
    mma = pd.read_excel(mma_file, sheet_name=None)
    ham = pd.read_excel(ham_file, sheet_name=None)
    sikayet = pd.read_excel(sikayet_file, sheet_name=None)
    return {"MMA": mma, "HAM_VERI": ham, "SIKAYET": sikayet}

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

tabBI, tabDATA = st.tabs(["📌 BI Dashboard (Power BI Mantığı)", "📄 Ham Veri (Sheet Görüntüle)"])

# ---------------- Ham Veri Görüntüleme ----------------
with tabDATA:
    st.subheader("Ham Veri Görüntüleme")
    ds = st.selectbox("Dosya", list(data.keys()), key="ds_view")
    sh = st.selectbox("Sheet", list(data[ds].keys()), key="sh_view")
    st.dataframe(data[ds][sh], use_container_width=True, height=650)

# ---------------- BI Dashboard ----------------
with tabBI:
    st.subheader("Power BI / Pivot Mantığı (Fact Tablo Seçimi)")

    # 1) Fact tablo seç (sen HAM_VERI seçeceksin)
    ds_fact = st.selectbox("Ana Veri (Fact) hangi dosyada?", list(data.keys()), index=list(data.keys()).index("HAM_VERI") if "HAM_VERI" in data else 0)
    sh_fact = st.selectbox("Fact sheet", list(data[ds_fact].keys()))
    fact = data[ds_fact][sh_fact].copy()

    st.caption(f"📌 Fact kaynak: **{ds_fact} / {sh_fact}**")

    # 2) Kolon eşleştirme (Power BI gibi)
    st.markdown("### 🧷 Kolon Eşleştirme (Zorunlu: Agent + Form Puan)")
    cols = list(fact.columns)

    cc1, cc2, cc3, cc4, cc5 = st.columns(5)

    with cc1:
        col_agent = st.selectbox("Agent / Asistan", cols, index=cols.index("Müşteri Temsilcisi Adı") if "Müşteri Temsilcisi Adı" in cols else 0)

    with cc2:
        col_lider = st.selectbox("Takım Lideri (ops.)", ["(YOK)"] + cols, index=0)

    with cc3:
        col_lok = st.selectbox("Lokasyon (ops.)", ["(YOK)"] + cols, index=0)

    with cc4:
        col_date = st.selectbox("Tarih (ops.)", ["(YOK)"] + cols, index=0)

    with cc5:
        # Form Puan zorunlu
        # Eğer listede yoksa user seçer; senin durumda burada olacak
        col_form = st.selectbox("Form Puan (zorunlu)", cols)

    if col_lider == "(YOK)":
        col_lider = None
    if col_lok == "(YOK)":
        col_lok = None
    if col_date == "(YOK)":
        col_date = None

    # 3) Tip dönüşümleri
    fact = to_numeric_safe(fact, col_form)
    if col_date:
        fact = to_datetime_safe(fact, col_date)

    # 4) Filtreler (Excel slicer gibi)
    st.sidebar.header("🔎 Filtreler (Slicer)")

    fdf = fact.copy()

    def multisel(df, col, label):
        if not col:
            return []
        opts = sorted(df[col].dropna().unique())
        return st.sidebar.multiselect(label, opts)

    # Cascading: Lokasyon -> Lider -> Agent gibi davranır
    sel_lok = multisel(fdf, col_lok, "Lokasyon") if col_lok else []
    if sel_lok and col_lok:
        fdf = fdf[fdf[col_lok].isin(sel_lok)]

    sel_lider = multisel(fdf, col_lider, "Takım Lideri") if col_lider else []
    if sel_lider and col_lider:
        fdf = fdf[fdf[col_lider].isin(sel_lider)]

    # Agent filtresi (opsiyonel)
    sel_agent = multisel(fdf, col_agent, "Agent") if col_agent else []
    if sel_agent and col_agent:
        fdf = fdf[fdf[col_agent].isin(sel_agent)]

    # Tarih filtresi (opsiyonel)
    if col_date and fdf[col_date].notna().any():
        min_d = fdf[col_date].min().date()
        max_d = fdf[col_date].max().date()
        dr = st.sidebar.date_input("Tarih Aralığı", value=(min_d, max_d))
        if dr:
            sd, ed = dr
            fdf = fdf[(fdf[col_date] >= pd.to_datetime(sd)) & (fdf[col_date] < pd.to_datetime(ed) + pd.Timedelta(days=1))]

    # 5) KPI Kartları (Power BI hissi)
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Kayıt Adedi", f"{len(fdf):,}".replace(",", "."))
    k2.metric("Aktif Agent", f"{fdf[col_agent].nunique():,}".replace(",", "."))
    k3.metric("Form Puan Ort.", f"{fdf[col_form].mean():.2f}" if fdf[col_form].notna().any() else "—")
    k4.metric("Form Puan Min/Max", f"{fdf[col_form].min():.2f} / {fdf[col_form].max():.2f}" if fdf[col_form].notna().any() else "—")

    st.divider()

    # 6) Satırlar / Değerler (Pivot / Matrix)
    st.markdown("### 🧩 Pivot Mantığı (Satırlar / Değerler)")

    row_dim_map = {
        "Agent": col_agent,
        "Takım Lideri": col_lider,
        "Lokasyon": col_lok,
    }
    row_dim_map = {k: v for k, v in row_dim_map.items() if v is not None}

    if not row_dim_map:
        st.error("Satır kırılımı için en az 1 kolon seçmelisin (Agent zaten zorunlu).")
        st.stop()

    p1, p2, p3 = st.columns([2, 2, 1])
    with p1:
        row_dim = st.selectbox("Satırlar (Rows)", list(row_dim_map.keys()), index=0)
    with p2:
        values = st.multiselect(
            "Değerler (Values)",
            ["Kayıt Adedi", "Form Puan Ortalama", "Form Puan Min", "Form Puan Max"],
            default=["Kayıt Adedi", "Form Puan Ortalama"]
        )
    with p3:
        top_n = st.number_input("Top N", min_value=5, max_value=500, value=50, step=5)

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

    sort_col = "Form Puan Ortalama" if "Form Puan Ortalama" in pivot.columns else pivot.columns[1]
    pivot = pivot.sort_values(by=sort_col, ascending=False).head(int(top_n))

    st.dataframe(pivot, use_container_width=True, height=520)
    csv = pivot.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Pivot çıktısı CSV", csv, "pivot_cikti.csv", "text/csv")

    st.divider()

    # 7) Grafik
    st.markdown("### 📈 Grafik")
    if "Form Puan Ortalama" in pivot.columns:
        fig = px.bar(pivot, x=row_col, y="Form Puan Ortalama")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Grafik için 'Form Puan Ortalama' değerini seç.")
