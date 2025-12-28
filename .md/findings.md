# Page 2: Findings Analysis

## A. Object Analysis (Interactive Module)
- **Visual:** Switch/Toggle antara **Treemap** dan **Pareto Chart**.
- **Data Source:** `df_exploded['temuan.nama']`.
- **Pareto Logic:** - Bar: Urutan frekuensi objek terbanyak (Descending).
    - Line: Akumulasi persentase kontribusi objek terhadap total temuan.
- **Insight:** Mengidentifikasi 20% objek yang menyebabkan 80% masalah operasional (Hukum Pareto).

## B. Condition Wordcloud
- **Data Source:** `df_exploded['temuan.kondisi.lemma']`.
- **Logic:** Menggunakan teks kata dasar (lemma) untuk menghindari redundansi kata imbuhan.
- **Visual:** Ukuran kata mewakili frekuensi kemunculan anomali di lapangan.

## C. Risk Category Matrix
- **Sumbu Y (Rows):** `team_role` (Departemen yang menemukan/melapor).
- **Sumbu X (Cols):** `temuan_kategori` (Near Miss, Unsafe Act/Condition, Positive).
- **Value:** Count of `kode_temuan`.

## D. Finding Details Table
- **Columns:** `tanggal`, `temuan_kategori`, `temuan.nama`, `temuan.kondisi`, `temuan.tempat`, `temuan_status`.
- **Filter Source:** `df_exploded` (untuk menampilkan detail objek per baris).