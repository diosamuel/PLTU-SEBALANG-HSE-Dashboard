SELECT 
  -- Fact Table Keys
  f.kode_temuan, 
  -- Create Date (tanggal pembuatan)
  CASE WHEN dd_create."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_create."year" AS int), 
    CAST(dd_create."month" AS int), 
    CAST(dd_create."day" AS int), 
    CAST(dd_create.hours AS int), 
    CAST(dd_create.minutes AS int), 
    0.0
  ) ELSE NULL END AS tanggal, 
  dd_create.day_name AS create_day_name, 
  -- Close Date (tanggal penutupan)
  CASE WHEN dd_close."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_close."year" AS int), 
    CAST(dd_close."month" AS int), 
    CAST(dd_close."day" AS int), 
    CAST(dd_close.hours AS int), 
    CAST(dd_close.minutes AS int), 
    0.0
  ) ELSE NULL END AS close_at, 
  dd_close.day_name AS close_day_name, 
  -- Open Date (tanggal dibuka)
  CASE WHEN dd_open."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_open."year" AS int), 
    CAST(dd_open."month" AS int), 
    CAST(dd_open."day" AS int), 
    CAST(dd_open.hours AS int), 
    CAST(dd_open.minutes AS int), 
    0.0
  ) ELSE NULL END AS open_at, 
  dd_open.day_name AS open_day_name, 
  -- Update Date (tanggal update terakhir)
  CASE WHEN dd_update."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_update."year" AS int), 
    CAST(dd_update."month" AS int), 
    CAST(dd_update."day" AS int), 
    CAST(dd_update.hours AS int), 
    CAST(dd_update.minutes AS int), 
    0.0
  ) ELSE NULL END AS update_at, 
  dd_update.day_name AS update_day_name, 
  -- Target Date (tanggal target penyelesaian)
  CASE WHEN dd_target."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_target."year" AS int), 
    CAST(dd_target."month" AS int), 
    CAST(dd_target."day" AS int), 
    CAST(dd_target.hours AS int), 
    CAST(dd_target.minutes AS int), 
    0.0
  ) ELSE NULL END AS target_at, 
  dd_target.day_name AS target_day_name, 
  dc.creator_id, 
  dc.creator_name, 
  dc.creator_kode_jabatan, 
  dc.nama_perusahaan AS creator_perusahaan, 
  dc.creator_departemen_dan_role, 
  dc.creator_role, 
  dc.creator_departemen, 
  dp.pic_id, 
  dp.pic_name, 
  dp.pic_departemen, 
  dt.raw_judul, 
  dt.raw_kondisi, 
  dt.raw_rekomendasi, 
  dt.temuan_nama, 
  dt.temuan_kondisi, 
  dt.temuan_rekomendasi, 
  dt.temuan_kategori, 
  dt.temuan_status, 
  dt.temuan_nama_spesifik, 
  dt.note AS temuan_note, 
  dt.keterangan_lokasi, 
  COALESCE(loc.nama_lokasi, f.tempat_id) AS nama_lokasi, 
  loc.lat, 
  loc.long AS lon, 
  loc.zone AS zona 
FROM 
  public.fact_k3 f -- Temuan Dimension
  LEFT JOIN public.dim_temuan dt ON f.kode_temuan = dt.kode_temuan -- Creator Dimension
  LEFT JOIN public.dim_creator dc ON f.creator_id = dc.creator_id -- PIC Dimension
  LEFT JOIN public.dim_pic dp ON f.kode_temuan = dp.kode_temuan -- Tempat/Lokasi Dimension
  LEFT JOIN public.dim_tempat loc ON UPPER(f.tempat_id) = UPPER(loc.nama_lokasi) -- Create Date Dimension
  LEFT JOIN public.dim_create_date dd_create ON f.kode_temuan = dd_create.kode_temuan -- Close Date Dimension
  LEFT JOIN public.dim_close_date dd_close ON f.kode_temuan = dd_close.kode_temuan -- Open Date Dimension
  LEFT JOIN public.dim_open_date dd_open ON f.kode_temuan = dd_open.kode_temuan -- Update Date Dimension
  LEFT JOIN public.dim_update_date dd_update ON f.kode_temuan = dd_update.kode_temuan -- Target Date Dimension
  LEFT JOIN public.dim_target_date dd_target ON f.kode_temuan = dd_target.kode_temuan