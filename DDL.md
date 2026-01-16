-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.dim_close_date (
  day integer,
  month integer,
  year integer,
  hours integer,
  close_date_sk integer NOT NULL DEFAULT nextval('dim_close_date_close_date_sk_seq'::regclass),
  minutes integer,
  day_name text
);
CREATE TABLE public.dim_close_date_dup (
  day double precision,
  month double precision,
  year double precision,
  hours double precision,
  kode_temuan text NOT NULL,
  minutes double precision,
  day_name text
);
CREATE TABLE public.dim_create_date (
  day integer,
  month integer,
  year integer,
  hours integer,
  minutes integer,
  create_date_sk integer NOT NULL DEFAULT nextval('dim_create_date_create_date_sk_seq'::regclass),
  day_name text
);
CREATE TABLE public.dim_create_date_dup (
  day integer,
  month integer,
  year integer,
  hours integer,
  minutes integer,
  kode_temuan text NOT NULL,
  day_name text
);
CREATE TABLE public.dim_creator (
  creator_id character varying NOT NULL,
  creator_name character varying,
  creator_kode_jabatan character varying,
  nama_perusahaan character varying,
  creator_departemen_dan_role character varying,
  creator_role character varying,
  creator_departemen character varying
);
CREATE TABLE public.dim_distrik (
  distrik_id character varying NOT NULL,
  creator_nama_distrik character varying,
  temuan_kode_distrik character varying,
  temuan_nama_distrik character varying
);
CREATE TABLE public.dim_open_date (
  day integer,
  month integer,
  year integer,
  hours integer,
  open_date_sk integer NOT NULL DEFAULT nextval('dim_open_date_open_date_sk_seq'::regclass),
  minutes integer,
  day_name text
);
CREATE TABLE public.dim_open_date_dup (
  day double precision,
  month double precision,
  year double precision,
  hours double precision,
  kode_temuan text NOT NULL,
  minutes double precision,
  day_name text
);
CREATE TABLE public.dim_pic (
  pic_id character varying,
  pic_name character varying,
  pic_departemen character varying NOT NULL,
  pic_sk smallint GENERATED ALWAYS AS IDENTITY NOT NULL,
  CONSTRAINT dim_pic_pkey PRIMARY KEY (pic_sk)
);
CREATE TABLE public.dim_target_date (
  target_date_sk integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  day integer,
  month integer,
  year integer,
  hours integer,
  minutes integer,
  day_name text,
  CONSTRAINT dim_target_date_pkey PRIMARY KEY (target_date_sk)
);
CREATE TABLE public.dim_target_date_dup (
  day double precision,
  month double precision,
  year double precision,
  hours double precision,
  kode_temuan text NOT NULL,
  minutes double precision,
  day_name text
);
CREATE TABLE public.dim_tempat (
  nama_lokasi text,
  lat double precision,
  long double precision,
  zone text
);
CREATE TABLE public.dim_temuan (
  kode_temuan character varying NOT NULL,
  raw_judul character varying,
  raw_kondisi character varying,
  raw_rekomendasi character varying,
  temuan_nama character varying,
  temuan_kondisi character varying,
  temuan_rekomendasi character varying,
  temuan_kategori character varying,
  note character varying,
  keterangan_lokasi character varying,
  temuan_status character varying,
  temuan_nama_spesifik text,
  CONSTRAINT dim_temuan_pkey PRIMARY KEY (kode_temuan)
);
CREATE TABLE public.dim_update_date (
  day integer,
  month integer,
  year integer,
  hours integer,
  minutes integer,
  update_date_sk integer NOT NULL DEFAULT nextval('dim_update_date_update_date_sk_seq'::regclass),
  day_name text
);
CREATE TABLE public.dim_update_date_dup (
  day double precision,
  month double precision,
  year double precision,
  hours double precision,
  kode_temuan text NOT NULL,
  minutes double precision,
  day_name text
);
CREATE TABLE public.fact_k3 (
  kode_temuan text,
  close_date_sk bigint,
  create_date_sk bigint,
  open_date_sk bigint,
  update_date_sk bigint,
  target_date_sk bigint,
  pic_sk bigint,
  creator_id text,
  tempat_id text
);