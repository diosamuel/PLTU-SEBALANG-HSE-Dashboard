# Page 4: Spatial Risk Analysis

## A. Geospatial Engine (Folium)
- **Data Source:** `df_master` (Deduplicated) untuk menghindari penumpukan pin akibat explode.
- **Coordinate Mapping:** Gunakan `map_reference.md` sebagai lookup table antara `nama_lokasi` dan Lat-Lon.
- **Priority Pin Logic:** - Jika koordinat sama, tampilkan satu Pin dengan warna kategori tertinggi (Near Miss > Unsafe > Positive).
    - Gunakan `MarkerCluster` untuk area padat temuan.

## B. Map Elements
- **Base Layer Toggle:** Satellite View vs Schematic View (Image Overlay).
- **Heatmap Toggle:** Intensitas berdasarkan akumulasi temuan di area tersebut.
- **Floating Legend:** Pojok kiri bawah untuk instruksi warna dan kategori.

## C. Top Location Card (Sidebar)
- **Ranking:** 5 area dengan `Risk Index` tertinggi.
- **Logic:** `RiskIndex = (NearMiss * 10) + (Unsafe * 5) + (Positive * 1)`.