import streamlit as st
import pandas as pd

st.set_page_config(page_title="Çağrı & Şikayet Dashboard", layout="wide")
st.title("📊 Çağrı & Şikayet Dashboard")
st.info("3 Excel dosyasını yükleyin. Dosya adları önemli değildir.")

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


def get_mma_main_sheet(mma_sheets: dict) -> pd.DataFrame:
    # Öncelik: "Data" varsa onu al, yoksa ilk sheet
    if "Data" in mma_sheets:
        return mma_sheets["Data"].copy()
    return mma_sheets[list(mma_sheets.keys())[0]].copy()


# ---------------- Main ----------------
if mma_file and ham_file and sikayet_file:
    data = load_excels(mma_file, ham_file, sikayet_file)
    st.success("Dosyalar yüklendi ✅")

    # Sekmeler burada TANIMLANIYOR -> tabA hatası biter
    tabA, tabB, tabC = st.tabs(["📌 Analiz (Dilimleyici)", "📄 Veri Görüntüle", "📚 Tüm Sayfalar"])

    # ============ TAB A: Excel Dilimleyici Mantığı ============
    with tabA:
        st.subheader("Excel Dilimleyici Mantığı (Lokasyon → Takım Lideri → Asistan Ort.)")

        mma_df = get_mma_main_sheet(data["MMA"])

        # Tip dönüşümleri
        if "Çağrı Tarih Saati" in mma_df.columns:
            mma_df["Çağrı Tarih Saati"] = pd.to_datetime(mma_df["Çağrı Tarih Saati"], errors="coerce")

        for col in ["Soru Puan 1", "Soru Puan 2"]:
            if col in mma_df.columns:
                mma_df[col] = pd.to_numeric(mma_df[col], errors="coerce")

        # --- Filtreler (Slicer)
        f1, f2, f3, f4 = st.columns(4)

        lokasyon_opts = sorted(mma_df["Lokasyon"].dropna().unique()) if "Lokasyon" in mma_df.columns else []
        lider_opts_all = sorted(mma_df["Takım Lideri"].dropna().unique()) if "Takım Lideri" in mma_df.columns else []
        skill_opts = sorted(mma_df["Skill İsmi"].dropna().unique()) if "Skill İsmi" in mma_df.columns else []

        with f1:
            lokasyon_sel = st.multiselect("Lokasyon", lokasyon_opts)

        # Cascading: Lokasyon seçilince lider listesi daralsın
        tmp = mma_df.copy()
        if lokasyon_sel and "Lokasyon" in tmp.columns:
            tmp = tmp[tmp["Lokasyon"].isin(lokasyon_sel)]
        lider_opts = sorted(tmp["Takım Lideri"].dropna().unique()) if "Takım Lideri" in tmp.columns else lider_opts_all

        with f2:
            lider_sel = st.multiselect("Takım Lideri", lider_opts)

        with f3:
            skill_sel = st.multiselect("Skill", skill_opts)

        with f4:
            date_range = None
            if "Çağrı Tarih Saati" in mma_df.columns and mma_df["Çağrı Tarih Saati"].notna().any():
                min_d = mma_df["Çağrı Tarih Saati"].min().date()
                max_d = mma_df["Çağrı Tarih Saati"].max().date()
                date_range = st.date_input("Tarih Aralığı", value=(min_d, max_d))

        # --- Filtre uygula
        fdf = mma_df.copy()

        if lokasyon_sel and "Lokasyon" in fdf.columns:
            fdf = fdf[fdf["Lokasyon"].isin(lokasyon_sel)]

        if lider_sel and "Takım Lideri" in fdf.columns:
            fdf = fdf[fdf["Takım Lideri"].isin(lider_sel)]

        if skill_sel and "Skill İsmi" in fdf.columns:
            fdf = fdf[fdf["Skill İsmi"].isin(skill_sel)]

        if date_range and "Çağrı Tarih Saati" in fdf.columns:
            start_d, end_d = date_range
            fdf = fdf[
                (fdf["Çağrı Tarih Saati"] >= pd.to_datetime(start_d)) &
                (fdf["Çağrı Tarih Saati"] < pd.to_datetime(end_d) + pd.Timedelta(days=1))
            ]

        st.caption(f"Filtre sonrası kayıt: {len(fdf)}")

        # --- Asistan ortalamaları
        if "Müşteri Temsilcisi Adı" in fdf.columns:
            agg = {
                "Kayıt Adedi": ("Müşteri Temsilcisi Adı", "count"),
            }
            if "Soru Puan 1" in fdf.columns:
                agg["Ort Puan 1"] = ("Soru Puan 1", "mean")
            if "Soru Puan 2" in fdf.columns:
                agg["Ort Puan 2"] = ("Soru Puan 2", "mean")

            grp = fdf.groupby("Müşteri Temsilcisi Adı", dropna=False).agg(**agg).reset_index()

            if "Ort Puan 1" in grp.columns and "Ort Puan 2" in grp.columns:
                grp["Genel Ortalama"] = grp[["Ort Puan 1", "Ort Puan 2"]].mean(axis=1)

            grp = grp.sort_values(by="Kayıt Adedi", ascending=False)

            st.subheader("👥 Takımdaki Asistanların Ortalamaları")
            st.dataframe(grp, use_container_width=True, height=520)

            csv = grp.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Asistan ortalamaları CSV", csv, "asistan_ortalama.csv", "text/csv")
        else:
            st.warning("Kolon bulunamadı: 'Müşteri Temsilcisi Adı'")

    # ============ TAB B: Tek sheet görüntüleme ============
    with tabB:
        st.subheader("📄 Sheet Seçerek Veri Gör")
        dataset = st.selectbox("Dosya", list(data.keys()), key="view_dataset")
        sheets = data[dataset]
        sheet = st.selectbox("Sheet", list(sheets.keys()), key="view_sheet")
        st.dataframe(sheets[sheet], use_container_width=True, height=650)

    # ============ TAB C: Tüm sheetler ============
    with tabC:
        st.subheader("📚 Tüm Sheet'ler")
        dataset2 = st.selectbox("Hangi dosya?", list(data.keys()), key="all_dataset")
        for sh_name, sh_df in data[dataset2].items():
            st.markdown(f"### {sh_name}")
            st.dataframe(sh_df, use_container_width=True, height=420)

else:
    st.warning("Devam etmek için 3 dosyayı da yükleyin.")
