# Page 1: Executive Summary

## A. Header Section
- **Global Alert:** Tampilkan Banner Merah jika ada `Near Miss` yang `Open`.
  - Logic: `if (df['temuan_kategori'] == 'Near Miss') & (df['temuan_status'] == 'Open'): show alert`.

## B. Top KPI Row (Source: Master State)
1. **Total Findings:** `count_distinct(kode_temuan)`.
2. **Closing Rate (Gauge):** Rasio `Closed` vs `Total Unique Findings`.
3. **Avg. Resolution (MTTR):** Rata-rata durasi penutupan (dalam Jam/Hari).
4. **Participation:** Jumlah `count_distinct(creator_name)` yang aktif.

## C. Main Charts
- **Finding Trend (Line Chart):** - X: `tanggal` (Bulanan).
  - Y: `count_distinct(kode_temuan)`.
- **Risk Distribution (Pie/Donut):** - Data: `temuan_kategori`.
  - Warna: Merah (Near Miss), Kuning (Unsafe), Hijau (Positive).

## D. Spatial & Ranking
- **Mini Heatmap:** Menampilkan hotspot awal berdasarkan `nama_lokasi`.
- **Top Entities (List):** Menampilkan 5 besar `temuan.nama` paling sering bermasalah (Source: Exploded State).