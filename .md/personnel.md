# Page 5: Personnel Performance

## A. Human Performance KPIs
1. **Participation Rate:** % `Unique Reporter` / `Total Employee`.
2. **SLA Discipline:** % Kepatuhan individu terhadap target 7 hari.
3. **Max Workload:** Jumlah `Open Tasks` terbanyak yang dipegang satu PIC.

## B. Productivity Scatter Plot
- **X-Axis:** Total Tugas (`count kode_temuan` di mana `nama_pic` == User).
- **Y-Axis:** Avg Resolution Speed (MTTR individu).
- **Interaction:** Mengklik titik (bubble) akan memfilter profil di `Personnel Detail`.

## C. Personnel Detail Card
- **Source:** `creator_name` slicer.
- **Identity:** Menampilkan Nama, Role, dan Team Role.
- **Individual Metrics:** - Total Findings Reported (sebagai pelapor).
    - Total Tasks Closed (sebagai PIC).
    - Avg. Resolution Time (speed).
- **Personal Map:** Menampilkan hotspot lokasi di mana personil tersebut sering melapor/bekerja.