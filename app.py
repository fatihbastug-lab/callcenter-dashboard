# --- MMA Data sayfasını al (yoksa ilk sheet)
mma_sheets = data["MMA"]
if "Data" in mma_sheets:
    mma_df = mma_sheets["Data"].copy()
else:
    first_sheet = list(mma_sheets.keys())[0]
    mma_df = mma_sheets[first_sheet].copy()

# Tarih / puan kolonlarını normalize et
for col in ["Çağrı Tarih Saati", "Anket Tarihi"]:
    if col in mma_df.columns:
        mma_df[col] = pd.to_datetime(mma_df[col], errors="coerce")

for col in ["Soru Puan 1", "Soru Puan 2"]:
    if col in mma_df.columns:
        mma_df[col] = pd.to_numeric(mma_df[col], errors="coerce")

# --- Sekmeler
tabA, tabB, tabC = st.tabs(["📌 Analiz (Dilimleyici)", "📄 Veri Görüntüle", "📚 Tüm Sayfalar"])

with tabA:
    st.subheader("Excel Dilimleyici Mantığı – MMA Analizi")

    # Filtre alanları
    f1, f2, f3, f4 = st.columns(4)

    lokasyon_opts = sorted(mma_df["Lokasyon"].dropna().unique()) if "Lokasyon" in mma_df.columns else []
    lider_opts = sorted(mma_df["Takım Lideri"].dropna().unique()) if "Takım Lideri" in mma_df.columns else []
    skill_opts = sorted(mma_df["Skill İsmi"].dropna().unique()) if "Skill İsmi" in mma_df.columns else []

    with f1:
        lokasyon_sel = st.multiselect("Lokasyon", lokasyon_opts, default=["Ankara"] if "Ankara" in lokasyon_opts else None)

    with f2:
        lider_sel = st.multiselect("Takım Lideri", lider_opts)

    with f3:
        skill_sel = st.multiselect("Skill", skill_opts)

    with f4:
        # Tarih aralığı (varsa)
        if "Çağrı Tarih Saati" in mma_df.columns and mma_df["Çağrı Tarih Saati"].notna().any():
            min_d = mma_df["Çağrı Tarih Saati"].min().date()
            max_d = mma_df["Çağrı Tarih Saati"].max().date()
            date_range = st.date_input("Tarih Aralığı", value=(min_d, max_d))
        else:
            date_range = None
            st.info("Tarih kolonu bulunamadı")

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
            (fdf["Çağrı Tarih Saati"] <  pd.to_datetime(end_d) + pd.Timedelta(days=1))
        ]

    st.caption(f"Filtre sonrası kayıt: {len(fdf)} satır")

    # Asistan ortalamaları (Takım liderinin takımındaki)
    if "Müşteri Temsilcisi Adı" in fdf.columns:
        grp = fdf.groupby("Müşteri Temsilcisi Adı", dropna=False).agg(
            Kayit_Adedi=("No", "count") if "No" in fdf.columns else ("Müşteri Temsilcisi Adı","count"),
            Ortalama_Puan1=("Soru Puan 1", "mean") if "Soru Puan 1" in fdf.columns else ("Müşteri Temsilcisi Adı","count"),
            Ortalama_Puan2=("Soru Puan 2", "mean") if "Soru Puan 2" in fdf.columns else ("Müşteri Temsilcisi Adı","count"),
        ).reset_index()

        # Genel Ortalama (Puan1 ve Puan2 varsa)
        if "Soru Puan 1" in fdf.columns and "Soru Puan 2" in fdf.columns:
            grp["Genel_Ortalama"] = grp[["Ortalama_Puan1", "Ortalama_Puan2"]].mean(axis=1)

        grp = grp.sort_values(by="Kayit_Adedi", ascending=False)

        st.subheader("👥 Asistan Bazlı Ortalamalar")
        st.dataframe(grp, use_container_width=True, height=520)
    else:
        st.warning("Müşteri Temsilcisi Adı kolonu bulunamadı.")
