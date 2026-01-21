import streamlit as st
import pandas as pd

st.set_page_config(page_title="Çağrı & Şikayet Dashboard", layout="wide")
st.title("📊 Çağrı & Şikayet Dashboard")
st.info("3 Excel dosyasını yükleyin. Dosya adları önemli değildir.")

col1, col2, col3 = st.columns(3)
with col1:
    mma_file = st.file_uploader("📂 MMA Excel", type=["xlsx"], key="mma")
with col2:
    ham_file = st.file_uploader("📂 HAM VERİ Excel", type=["xlsx"], key="ham")
with col3:
    sikayet_file = st.file_uploader("📂 ŞİKAYET Excel", type=["xlsx"], key="sikayet")

def clean_df(df: pd.DataFrame, drop_unnamed: bool) -> pd.DataFrame:
    out = df.copy()
    if drop_unnamed:
        out = out.loc[:, ~out.columns.astype(str).str.startswith("Unnamed")]
    return out

if mma_file and ham_file and sikayet_file:

    @st.cache_data
    def load_excels(mma_file, ham_file, sikayet_file):
        mma = pd.read_excel(mma_file, sheet_name=None)
        ham = pd.read_excel(ham_file, sheet_name=None)
        sikayet = pd.read_excel(sikayet_file, sheet_name=None)
        return {"MMA": mma, "HAM_VERI": ham, "SIKAYET": sikayet}

    data = load_excels(mma_file, ham_file, sikayet_file)
    st.success("Dosyalar yüklendi ✅")

    st.sidebar.header("Görüntüleme Ayarları")
    drop_unnamed = st.sidebar.checkbox("Unnamed kolonları gizle (opsiyon)", value=False)

    tab1, tab2 = st.tabs(["📄 Veri Görüntüle", "📚 Tüm Sayfalar"])

    # --- TAB 1: tek sheet birebir
    with tab1:
        st.sidebar.subheader("Seçimler")
        dataset = st.sidebar.selectbox("Dosya", list(data.keys()))
        sheets = data[dataset]
        sheet = st.sidebar.selectbox("Sayfa (Sheet)", list(sheets.keys()))

        df = clean_df(sheets[sheet], drop_unnamed)

        c1, c2, c3 = st.columns(3)
        c1.metric("Dosya", dataset)
        c2.metric("Sayfa", sheet)
        c3.metric("Satır / Kolon", f"{df.shape[0]} / {df.shape[1]}")

        st.divider()
        st.dataframe(df, use_container_width=True, height=650)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Bu sayfayı CSV indir", csv, f"{dataset}_{sheet}.csv", "text/csv")

    # --- TAB 2: seçilen dosyadaki tüm sheet’leri alt alta
    with tab2:
        dataset2 = st.selectbox("Hangi dosyanın tüm sayfaları?", list(data.keys()), key="all_sheets_dataset")
        st.write(f"**{dataset2}** dosyasındaki tüm sheet’ler aşağıda listelenmiştir.")

        for sh_name, sh_df in data[dataset2].items():
            st.subheader(f"📌 {sh_name}")
            df2 = clean_df(sh_df, drop_unnamed)
            st.dataframe(df2, use_container_width=True, height=420)

else:
    st.warning("Devam etmek için 3 dosyayı da yükleyin.")
