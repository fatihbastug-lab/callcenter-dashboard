import altair as alt

def find_first_sheet_with_cols(sheets: dict, required_cols: set):
    for sh_name, df in sheets.items():
        cols = set(map(str, df.columns))
        if required_cols.issubset(cols):
            return sh_name, df.copy()
    return None, None

with tabA:
    st.subheader("📊 Performans (Excel Dilimleyici Gibi)")

    # Burada MMA yerine performans datası hangi dosyadaysa onu seçtiriyoruz
    perf_file = st.selectbox("Performans dosyası hangi yüklenen dosyada?", list(data.keys()), index=0)
    sheets = data[perf_file]

    # Kolonlara göre uygun sheet bul (senin dosyana göre gerekirse isimleri ayarlarız)
    required = {"TAKIM LİDERİ", "LOKASYON", "AGENT"}
    sh_name, perf = find_first_sheet_with_cols(sheets, required)

    if perf is None:
        st.error("Bu dosyada beklenen kolonlar bulunamadı: TAKIM LİDERİ, LOKASYON, AGENT")
        st.stop()

    st.caption(f"Kullanılan sayfa: {sh_name}")

    # Aylık kolonları otomatik yakala (KASIM/ARALIK/OCAK benzeri)
    month_cols = [c for c in perf.columns if str(c).upper().strip() in ["KASIM", "ARALIK", "OCAK", "KASIM (2022)", "ARALIK (2022)", "OCAK (2023)"]]
    # Eğer farklı isimler varsa en alttaki listede genişletiriz.

    # --- Slicer'lar (cascading gibi)
    c1, c2 = st.columns([3, 1])

    with c2:
        lokasyon_opts = sorted(perf["LOKASYON"].dropna().unique())
        lokasyon_sel = st.multiselect("LOKASYON", lokasyon_opts)

        # Lokasyon filtresi uygulanmış data üzerinden lider listesi
        tmp = perf.copy()
        if lokasyon_sel:
            tmp = tmp[tmp["LOKASYON"].isin(lokasyon_sel)]

        lider_opts = sorted(tmp["TAKIM LİDERİ"].dropna().unique())
        lider_sel = st.multiselect("TAKIM LİDERİ", lider_opts)

    # Filtre uygula
    fdf = perf.copy()
    if lokasyon_sel:
        fdf = fdf[fdf["LOKASYON"].isin(lokasyon_sel)]
    if lider_sel:
        fdf = fdf[fdf["TAKIM LİDERİ"].isin(lider_sel)]

    # Sayısal ay kolonlarını sayıya çevir
    for mc in month_cols:
        fdf[mc] = pd.to_numeric(fdf[mc], errors="coerce")

    # Son 3 ay ort
    if len(month_cols) >= 3:
        last3 = month_cols[-3:]
        fdf["Son 3 Ay Ortalama"] = fdf[last3].mean(axis=1)

    # --- Excel benzeri tablo + sparkline
    with c1:
        st.write("### Liste")

        # Sparkline için uzun form
        if len(month_cols) >= 2:
            long = fdf[["AGENT"] + month_cols].melt(id_vars=["AGENT"], var_name="Ay", value_name="Skor").dropna()

            # Sparkline chart: AGENT bazlı küçük çizgiler
            # (Altair ile tek tek küçük grafik üretip tabloya gömmek zor; onun yerine AGENT seçince sağda sparkline gösteriyoruz.)
            agent_opts = sorted(fdf["AGENT"].dropna().unique())
            sel_agent = st.selectbox("Sparkline görmek için AGENT seç", agent_opts) if agent_opts else None

            if sel_agent:
                g = long[long["AGENT"] == sel_agent].copy()
                chart = (
                    alt.Chart(g)
                    .mark_line(point=True)
                    .encode(x="Ay:N", y="Skor:Q")
                    .properties(height=200)
                )
                st.altair_chart(chart, use_container_width=True)

        # Tablo kolonları
        show_cols = ["AGENT", "TAKIM LİDERİ", "LOKASYON"] + month_cols
        if "Son 3 Ay Ortalama" in fdf.columns:
            show_cols += ["Son 3 Ay Ortalama"]

        st.dataframe(
            fdf[show_cols].sort_values(by="Son 3 Ay Ortalama" if "Son 3 Ay Ortalama" in fdf.columns else "AGENT", ascending=False),
            use_container_width=True,
            height=520
        )
