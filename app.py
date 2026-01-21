import streamlit as st
import pandas as pd

st.set_page_config(page_title="Çağrı & Şikayet Dashboard", layout="wide")

st.title("📊 Çağrı & Şikayet Dashboard")
st.info("3 Excel dosyasını yükleyin. Dosya adları önemli değildir.")

# --- Dosya yükleme alanları
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


def clean_df(df: pd.DataFrame, drop_unnamed: bool) -> pd.DataFrame:
    out = df.copy()
    if drop_unnamed:
        out = out.loc[:, ~out.columns.astype(str).str.startswith("Unnamed")]
    return out


if mma_file and ham_file and sikayet_file:
    data = load_excels(mma_file, ham_file, sikayet_file)
    st.success("Dosyalar yüklendi ✅")

    # --- Sekmeler
    tabA, tabB, tabC = st.tabs(["📌 Analiz (Dilimleyici)", "📄 Veri Görüntüle", "📚 Tüm Sayfalar"])

    # ============ TAB A: Slicer Analizi ============
    with tabA:
        st.subheader("Excel Dilimleyici Mantığı – MMA Analizi")

        # MMA içinden Data sheet (yoksa ilk sheet)
        mma_sheets = data["MMA"]
        if "Data" in mma_sheets:
            mma_df = mma_sheets["Data"].copy()
        else:
            mma_df = mma_sheets[list(mma_sheets.keys())[0]].copy()

        # Tip dönüşümleri
        for col in ["Çağrı Tarih Saati", "Anket Tarihi"]:
            if col in mma_df.columns:
                mma_df[col] = pd.to_datetime(mma_df[col], errors="coerce")

        for col in ["Soru Puan 1", "Soru Puan 2"]:
            if col in mma_df.columns:
                mma_df[col] = pd.to_numeric(mma_df[col], errors="coerce")

        # Sidebar ayar
        st.sidebar.header("Filtreler")
        drop_unnamed = st.sidebar.checkbox("Unnamed kolonları gizle", value=False)

        lokasyon_opts = sorted(mma_df["Lokasyon"].dropna().unique()) if "Lokasyon" in mma_df.columns else []
        lider_opts = sorted(mma_df["Takım Lideri"].dropna().unique()) if "Takım Lideri" in mma_df.columns else []
        skill_opts = sorted(mma_df["Skill İsmi"].dropna().unique()) if "Skill İsmi" in mma_df.columns else []

        lokasyon_sel = st.sidebar.multiselect("Lokasyon", lokasyon_opts)
        lider_sel = st.sidebar.multiselect("Takım Lideri", lider_opts)
        skill_sel = st.sidebar.multiselect("Skill", skill_opts)

        # Tarih filtresi
        date_range = None
        if "Çağrı Tarih Saati" in mma_df.columns and mma_df["Çağrı Tarih Saati"].notna().any():
            min_d = mma_df["Çağrı Tarih Saati"].min().date()
            max_d = mma_df["Çağrı Tarih Saati"].max().date()
            date_range = st.sidebar.date_input("Tarih Aralığı", value=(min_d, max_d))

        # Filtre uygula
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

        fdf = clean_df(fdf, drop_unnamed)

        st.caption(f"Filtre sonrası kayıt: {len(fdf)} satır")

        # KPI’lar
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Kayıt", f"{len(fdf)}")

        if "Müşteri Temsilcisi Adı" in fdf.columns:
            k2.metric("Aktif Asistan", f"{fdf['Müşteri Temsilcisi Adı'].nunique()}")
        else:
            k2.metric("Aktif Asistan", "—")

        if "Takım Lideri" in fdf.columns:
            k3.metric("Takım Lideri (seçili)", str(len(lider_sel)) if lider_sel else "Hepsi")
        else:
            k3.metric("Takım Lideri", "—")

        st.divider()

        # Asistan bazlı ortalamalar
        if "Müşteri Temsilcisi Adı" in fdf.columns:
            agg_dict = {}
            if "No" in fdf.columns:
                agg_dict["Kayit_Adedi"] = ("No", "count")
            else:
                agg_dict["Kayit_Adedi"] = ("Müşteri Temsilcisi Adı", "count")

            if "Soru Puan 1" in fdf.columns:
                agg_dict["Ortalama_Puan1"] = ("Soru Puan 1", "mean")
            if "Soru Puan 2" in fdf.columns:
                agg_dict["Ortalama_Puan2"] = ("Soru Puan 2", "mean")

            grp = fdf.groupby("Müşteri Temsilcisi Adı", dropna=False).agg(**agg_dict).reset_index()

            if "Ortalama_Puan1" in grp.columns and "Ortalama_Puan2" in grp.columns:
                grp["Genel_Ortalama"] = grp[["Ortalama_Puan1", "Ortalama_Puan2"]].mean(axis=1)

            grp = grp.sort_values(by="Kayit_Adedi", ascending=False)

            st.subheader("👥 Asistan Bazlı Ortalamalar")
            st.dataframe(grp, use_container_width=True, height=520)

            csv = grp.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Asistan ortalamalarını CSV indir", csv, "asistan_ortalamalari.csv", "text/csv")
        else:
            st.warning("MMA içinde 'Müşteri Temsilcisi Adı' kolonu bulunamadı.")

    # ============ TAB B: Tek sheet görüntüleme ============
    with tabB:
        st.subheader("📄 Veri Görüntüle (Sheet seç)")
        dataset = st.selectbox("Dosya", list(data.keys()), key="view_dataset")
        sheets = data[dataset]
        sheet = st.selectbox("Sayfa (Sheet)", list(sheets.keys()), key="view_sheet")

        df = sheets[sheet]
        st.dataframe(df, use_container_width=True, height=650)

    # ============ TAB C: Tüm sheet'ler ============
    with tabC:
        st.subheader("📚 Tüm Sayfalar")
        dataset2 = st.selectbox("Hangi dosyanın tüm sayfaları?", list(data.keys()), key="all_dataset")
        for sh_name, sh_df in data[dataset2].items():
            st.markdown(f"### {sh_name}")
            st.dataframe(sh_df, use_container_width=True, height=420)

else:
    st.warning("Dashboard’un açılması için 3 Excel dosyasını da yükleyin.")
