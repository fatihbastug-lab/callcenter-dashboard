import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Çağrı & Şikayet Dashboard", layout="wide")

DATA_DIR = Path("data")

@st.cache_data
def load_data():
    mma = pd.read_excel(DATA_DIR / "MMA.xlsx", sheet_name=0)
    ham = pd.read_excel(DATA_DIR / "HAM VERİ.xlsx", sheet_name=0)
    sikayet = pd.read_excel(DATA_DIR / "ŞİKAYET.xlsx", sheet_name=0)

    # MMA tarih kolonlarını normalize etmeye çalış
    for col in ["Çağrı Tarih Saati", "Anket Tarihi"]:
        if col in mma.columns:
            mma[col] = pd.to_datetime(mma[col], errors="coerce")

    # Şikayet tarih kolonu olası isimler (gerekirse burayı senin kolon adına göre düzeltiriz)
    for col in ["Tarih", "Kayıt Tarihi", "Şikayet Tarihi"]:
        if col in sikayet.columns:
            sikayet[col] = pd.to_datetime(sikayet[col], errors="coerce")
            sikayet.rename(columns={col: "Şikayet Tarihi"}, inplace=True)
            break

    return mma, ham, sikayet

mma, ham, sikayet = load_data()

st.title("📊 Çağrı & Şikayet Dashboard")

# ---- Sidebar filtreler
st.sidebar.header("Filtreler")

date_col = "Çağrı Tarih Saati" if "Çağrı Tarih Saati" in mma.columns else None
min_date = mma[date_col].min() if date_col else None
max_date = mma[date_col].max() if date_col else None

if date_col and pd.notna(min_date) and pd.notna(max_date):
    start_date, end_date = st.sidebar.date_input(
        "Tarih Aralığı",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
else:
    start_date = end_date = None

lokasyon_col = "Lokasyon" if "Lokasyon" in mma.columns else None
skill_col = "Skill İsmi" if "Skill İsmi" in mma.columns else None

lokasyon_options = sorted(mma[lokasyon_col].dropna().unique()) if lokasyon_col else []
skill_options = sorted(mma[skill_col].dropna().unique()) if skill_col else []

selected_lokasyon = st.sidebar.multiselect("Lokasyon", lokasyon_options)
selected_skill = st.sidebar.multiselect("Skill", skill_options)

# ---- Filtre uygula
df = mma.copy()

if date_col and start_date and end_date:
    df = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))]

if lokasyon_col and selected_lokasyon:
    df = df[df[lokasyon_col].isin(selected_lokasyon)]

if skill_col and selected_skill:
    df = df[df[skill_col].isin(selected_skill)]

# ---- KPI’lar
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_calls = len(df)
kpi1.metric("Toplam Kayıt (MMA)", f"{total_calls:,}".replace(",", "."))

# Önem varsa
if "Önem" in df.columns:
    critical = df[df["Önem"].astype(str).str.contains("kritik|critical|yüksek", case=False, na=False)]
    kpi2.metric("Kritik/Yüksek Önem", f"{len(critical):,}".replace(",", "."))
else:
    kpi2.metric("Kritik/Yüksek Önem", "—")

# Şikayet toplam
kpi3.metric("Toplam Şikayet", f"{len(sikayet):,}".replace(",", "."))

# Farklı temsilci sayısı
agent_col = "Müşteri Temsilcisi Adı" if "Müşteri Temsilcisi Adı" in df.columns else None
kpi4.metric("Aktif Temsilci", f"{df[agent_col].nunique():,}".replace(",", ".") if agent_col else "—")

st.divider()

left, right = st.columns([2, 1])

# ---- Trend
with left:
    st.subheader("📈 Zaman Trendi (MMA)")
    if date_col:
        trend = df.dropna(subset=[date_col]).copy()
        trend["Gün"] = trend[date_col].dt.date
        trend = trend.groupby("Gün").size().reset_index(name="Adet")
        fig = px.line(trend, x="Gün", y="Adet", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("MMA içinde 'Çağrı Tarih Saati' kolonu bulunamadı.")

# ---- Lokasyon dağılımı
with right:
    st.subheader("📍 Lokasyon Dağılımı")
    if lokasyon_col:
        loc = df.groupby(lokasyon_col).size().reset_index(name="Adet").sort_values("Adet", ascending=False).head(12)
        fig2 = px.bar(loc, x=lokasyon_col, y="Adet")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("MMA içinde 'Lokasyon' kolonu bulunamadı.")

st.divider()

# ---- Tablo (isteğe bağlı)
with st.expander("📄 Filtrelenmiş MMA Verisi (ilk 200 satır)"):
    st.dataframe(df.head(200), use_container_width=True)
