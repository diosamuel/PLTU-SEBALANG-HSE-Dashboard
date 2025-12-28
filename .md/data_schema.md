# Data Processing Schema: HSE PLTU Sebalang

## A. Dual-Source Strategy
Dashboard ini menggunakan satu dataset (Engineered Data), namun harus diproses menjadi dua state berbeda:
1. **Master State (Unique):** - Digunakan untuk: KPI Cards, SLA Calculation, dan Map Pins.
   - Logic: `df.drop_duplicates(subset='kode_temuan')`.
2. **Exploded State (Granular):**
   - Digunakan untuk: Treemap, Pareto, Wordcloud, dan Sankey.
   - Logic: Gunakan seluruh baris (setiap baris mewakili satu entitas objek NER).

## B. Core Columns Mapping
- **Primary Key:** `kode_temuan` (ID Unik Laporan).
- **Time Dimension:** `tanggal` (Format: DD/MM/YYYY).
- **Spatial Dimension:** `nama_lokasi` (Mapping ke Koordinat).
- **NLP Entities (NER):** - `temuan.nama` (Objek fisik yang bermasalah).
    - `temuan.kondisi.lemma` (Kata dasar anomali/kondisi).
    - `temuan.tempat` (Lokasi mikro/spesifik).
- **Accountability:**
    - `team_role`: Departemen Pelapor (Discoverer).
    - `nama`: Departemen PIC (Finisher/Responsible).