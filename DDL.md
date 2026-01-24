-- ==========================================
-- HSSE-ETL Star Schema DDL
-- fact_k3 is the CENTER of the star
-- ==========================================

-- DROP SCHEMA public;
CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION pg_database_owner;

-- ==========================================
-- FACT TABLE (Create first - Center of Star)
-- ==========================================

CREATE TABLE public.fact_k3 (
	kode_temuan text NOT NULL,
	creator_id text NULL,
	tempat_id VARCHAR NULL,
	distrik_id varchar NULL,
	CONSTRAINT fact_k3_pkey PRIMARY KEY (kode_temuan)
);

-- ==========================================
-- DIMENSION TABLES (All reference fact_k3)
-- ==========================================

-- Dimension: Temuan (Finding)
CREATE TABLE public.dim_temuan (
	kode_temuan varchar NOT NULL,
	raw_judul varchar NULL,
	raw_kondisi varchar NULL,
	raw_rekomendasi varchar NULL,
	temuan_nama varchar NULL,
	temuan_kondisi varchar NULL,
	temuan_rekomendasi varchar NULL,
	temuan_kategori varchar NULL,
	note varchar NULL,
	keterangan_lokasi varchar NULL,
	temuan_status varchar NULL,
	temuan_nama_spesifik text NULL,
	CONSTRAINT dim_temuan_pkey PRIMARY KEY (kode_temuan)
);

ALTER TABLE public.dim_temuan 
	ADD CONSTRAINT fk_temuan_fact FOREIGN KEY (kode_temuan) REFERENCES public.fact_k3(kode_temuan);

-- Dimension: Creator
CREATE TABLE public.dim_creator (
	creator_id varchar NOT NULL,
	creator_name varchar NULL,
	creator_kode_jabatan varchar NULL,
	nama_perusahaan varchar NULL,
	creator_departemen_dan_role varchar NULL,
	creator_role varchar NULL,
	creator_departemen varchar NULL,
	CONSTRAINT dim_creator_pkey PRIMARY KEY (creator_id)
);

ALTER TABLE public.fact_k3 
	ADD CONSTRAINT fk_fact_creator FOREIGN KEY (creator_id) REFERENCES public.dim_creator(creator_id);

-- Dimension: Distrik
CREATE TABLE public.dim_distrik (
	distrik_id varchar NOT NULL,
	creator_nama_distrik varchar NULL,
	temuan_kode_distrik varchar NULL,
	temuan_nama_distrik varchar NULL,
	CONSTRAINT dim_distrik_pkey PRIMARY KEY (distrik_id)
);

ALTER TABLE public.fact_k3 
	ADD CONSTRAINT fk_fact_distrik FOREIGN KEY (distrik_id) REFERENCES public.dim_distrik(distrik_id);

-- Dimension: Tempat (Location)
CREATE TABLE public.dim_tempat (
	nama_lokasi text NULL,
	lat float8 NULL,
	long float8 NULL,
	"zone" text NULL,
	CONSTRAINT dim_tempat_pkey PRIMARY KEY (nama_lokasi)
);

ALTER TABLE public.fact_k3 
	ADD CONSTRAINT fk_fact_tempat FOREIGN KEY (tempat_id) REFERENCES public.dim_tempat(tempat_id);

-- Dimension: PIC (Person In Charge)
CREATE TABLE public.dim_pic (
	kode_temuan varchar NOT NULL,
	pic_id varchar NULL,
	pic_name varchar NULL,
	pic_departemen varchar NOT NULL,
	CONSTRAINT dim_pic_pkey PRIMARY KEY (kode_temuan)
);

ALTER TABLE public.dim_pic 
	ADD CONSTRAINT fk_pic_fact FOREIGN KEY (kode_temuan) REFERENCES public.fact_k3(kode_temuan);

-- ==========================================
-- DATE DIMENSIONS (All reference fact_k3)
-- ==========================================

-- Dimension: Close Date
CREATE TABLE public.dim_close_date (
	kode_temuan text NOT NULL,
	"day" float8 NULL,
	"month" float8 NULL,
	"year" float8 NULL,
	hours float8 NULL,
	minutes float8 NULL,
	day_name text NULL,
	CONSTRAINT dim_close_date_pkey PRIMARY KEY (kode_temuan)
);

ALTER TABLE public.dim_close_date 
	ADD CONSTRAINT fk_close_date_fact FOREIGN KEY (kode_temuan) REFERENCES public.fact_k3(kode_temuan);

-- Dimension: Create Date
CREATE TABLE public.dim_create_date (
	kode_temuan text NOT NULL,
	"day" int4 NULL,
	"month" int4 NULL,
	"year" int4 NULL,
	hours int4 NULL,
	minutes int4 NULL,
	day_name text NULL,
	CONSTRAINT dim_create_date_pkey PRIMARY KEY (kode_temuan)
);

ALTER TABLE public.dim_create_date 
	ADD CONSTRAINT fk_create_date_fact FOREIGN KEY (kode_temuan) REFERENCES public.fact_k3(kode_temuan);

-- Dimension: Open Date
CREATE TABLE public.dim_open_date (
	kode_temuan text NOT NULL,
	"day" float8 NULL,
	"month" float8 NULL,
	"year" float8 NULL,
	hours float8 NULL,
	minutes float8 NULL,
	day_name text NULL,
	CONSTRAINT dim_open_date_pkey PRIMARY KEY (kode_temuan)
);

ALTER TABLE public.dim_open_date 
	ADD CONSTRAINT fk_open_date_fact FOREIGN KEY (kode_temuan) REFERENCES public.fact_k3(kode_temuan);

-- Dimension: Target Date
CREATE TABLE public.dim_target_date (
	kode_temuan text NOT NULL,
	"day" float8 NULL,
	"month" float8 NULL,
	"year" float8 NULL,
	hours float8 NULL,
	minutes float8 NULL,
	day_name text NULL,
	CONSTRAINT dim_target_date_pkey PRIMARY KEY (kode_temuan)
);

ALTER TABLE public.dim_target_date 
	ADD CONSTRAINT fk_target_date_fact FOREIGN KEY (kode_temuan) REFERENCES public.fact_k3(kode_temuan);

-- Dimension: Update Date
CREATE TABLE public.dim_update_date (
	kode_temuan text NOT NULL,
	"day" float8 NULL,
	"month" float8 NULL,
	"year" float8 NULL,
	hours float8 NULL,
	minutes float8 NULL,
	day_name text NULL,
	CONSTRAINT dim_update_date_pkey PRIMARY KEY (kode_temuan)
);

ALTER TABLE public.dim_update_date 
	ADD CONSTRAINT fk_update_date_fact FOREIGN KEY (kode_temuan) REFERENCES public.fact_k3(kode_temuan);
