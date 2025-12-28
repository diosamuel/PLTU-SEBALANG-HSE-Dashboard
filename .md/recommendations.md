# Page 3: Recommendations & SLA

## A. Risk-to-Location Flow (Sankey Chart)
- **Flow Logic:** `temuan_kategori` → `temuan.nama` → `temuan.tempat`.
- **Data Source:** `df_exploded`.
- **Insight:** Menelusuri jenis risiko dan objek spesifik hingga ke titik lokasi teknis hasil NER.

## B. Execution KPIs (The "Non-Repetitive" Logic)
1. **Pending High-Risk:** Count `distinct(kode_temuan)` kategori `Near Miss` status `Open`.
2. **SLA Compliance:** % temuan yang `close_at` <= `synthetic_target` (Created + 7 hari).
3. **Avg. Aging:** Rata-rata umur temuan `Open` sejak `created_at` hingga hari ini.

## C. High-Risk Priority Table
- **Logic:** Filter `temuan_kategori` == 'Near Miss'.
- **Styling:** Baris dengan status `Open` wajib di-highlight warna Merah Transparan.
- **Column:** Menampilkan `nama_pic` sebagai penanggung jawab eksekusi.

## D. SLA per Department (Horizontal Bar)
- **Sumbu Y:** `nama` (Departemen PIC/Eksekutor).
- **Sumbu X:** % Completion Rate tepat waktu.