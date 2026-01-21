import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Çağrı & Şikayet Dashboard", layout="wide")

DATA_DIR = Path("data")

@st.cache_data
def load_all_excels():
    # sheet_name=None => tüm sheet'leri dict olarak alır
    mma = pd.read_excel(DATA_DIR / "MMA.xlsx", sheet_name=None)
    ham = pd.read_excel(DATA_DIR / "HAM_VERI.xlsx", sheet_name=None)
    sikayet = pd.read_excel(DATA_DIR / "SIKAYET.xlsx", sheet_name=None)
    return {"MMA": mma, "HAM_VERI": ham, "SIKAYET": sikayet}

data = load_all_excels()

st.title("📊 Çağrı & Şikayet Dashboard (Tüm Sayfalar)")

# --- Sol menü: dosya ve sheet seçimi
st.sidebar.header("Veri Görüntüleme")
dataset_name = st.sidebar.selectbox("Dosya", list(data.keys()))
sheets_dict = data[dataset_name]
sheet_name = st.sidebar.selectbox("Sayfa (Sheet)", list(sheets_dict.keys()))

df = sheets_dict[sheet_name].copy()

# --- Üst bilgi
c1, c2, c3 = st.columns(3)
c1.metric("Dosya", dataset_name)
c2.metric("Sayfa", sheet_name)
c3.metric("Satır / Kolon", f"{df.shape[0]} / {df.shape[1]}")

st.divider()

# --- Tabloyu birebir göster
st.subheader("📄 Sayfa İçeriği")
st.dataframe(df, use_container_width=True, height=650)

# --- İndirme (CSV)
st.divider()
st.subheader("⬇️ İndir")
csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="Bu sayfayı CSV indir",
    data=csv,
    file_name=f"{dataset_name}_{sheet_name}.csv",
    mime="text/csv"
)
