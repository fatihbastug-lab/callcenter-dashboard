import streamlit as st
import pandas as pd

st.set_page_config(page_title="Çağrı & Şikayet Dashboard", layout="wide")

st.title("📊 Çağrı & Şikayet Dashboard")
st.info("Lütfen aşağıdaki 3 Excel dosyasını yükleyin. Dosya adları önemli değildir.")

# --- Dosya yükleme alanları
col1, col2, col3 = st.columns(3)

with col1:
    mma_file = st.file_uploader("📂 MMA Excel", type=["xlsx"], key="mma")

with col2:
    ham_file = st.file_uploader("📂 HAM VERİ Excel", type=["xlsx"], key="ham")

with col3:
    sikayet_file = st.file_uploader("📂 ŞİKAYET Excel", type=["xlsx"], key="sikayet")

# --- Tüm dosyalar yüklendiyse
if mma_file and ham_file and sikayet_file:

    @st.cache_data
    def load_excels(mma_file, ham_file, sikayet_file):
        mma = pd.read_excel(mma_file, sheet_name=None)
        ham = pd.read_excel(ham_file, sheet_name=None)
        sikayet = pd.read_excel(sikayet_file, sheet_name=None)
        return {
            "MMA": mma,
            "HAM_VERI": ham,
            "SIKAYET": sikayet
        }

    data = load_excels(mma_file, ham_file, sikayet_file)

    st.success("Dosyalar başarıyla yüklendi ✅")

    st.divider()

    # --- Sol menü: dosya & sheet seçimi
    st.sidebar.header("Veri Seçimi")
    dataset = st.sidebar.selectbox("Dosya", list(data.keys()))
    sheets = data[dataset]
    sheet = st.sidebar.selectbox("Sayfa (Sheet)", list(sheets.keys()))

    df = sheets[sheet]

    # --- Üst bilgi
    c1, c2, c3 = st.columns(3)
    c1.metric("Dosya", dataset)
    c2.metric("Sayfa", sheet)
    c3.metric("Satır / Kolon", f"{df.shape[0]} / {df.shape[1]}")

    st.divider()

    # --- Tabloyu birebir göster
    st.subheader("📄 Sayfa İçeriği")
    st.dataframe(df, use_container_width=True, height=650)

    # --- İndirme
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Bu sayfayı CSV indir",
        csv,
        f"{dataset}_{sheet}.csv",
        "text/csv"
    )

else:
    st.warning("Dashboard’un açılması için 3 Excel dosyasını da yükleyin.")
