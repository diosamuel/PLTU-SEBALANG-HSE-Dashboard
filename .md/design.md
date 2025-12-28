# UI/UX Design Specification

## A. Color Palette
- **Background:** `#CBECF5` (Light Blue Gradient).
- **Primary Text:** `#00526A` (Dark Water).
- **Alert/Critical:** `#FF4B4B` (Red Pulse).
- **Warning:** `#FFAA00` (Yellow/Orange).
- **Positive:** `#28A745` (Green).

## B. Visual Components
- **Container Styling:** White Cards dengan `border-radius: 15px` dan `box-shadow` halus.
- **Glassmorphism:** Sidebar menggunakan efek semi-transparan (Opacity 80%).
- **Typography:** Sans-serif (Inter atau Roboto). Ukuran font minimal 12px untuk keterbacaan tinggi.

## C. Interaction Rules
- **Cross-Filtering:** Mengklik elemen di satu grafik harus memfilter seluruh halaman.
- **Responsive Layout:** Sidebar tetap (fixed) di kiri; konten utama menggunakan sistem grid Streamlit `st.columns()`.