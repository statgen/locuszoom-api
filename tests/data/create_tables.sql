CREATE SCHEMA rest;

CREATE TABLE rest.traits (
  trait TEXT,
  label TEXT,
  grouping TEXT,
  PRIMARY KEY (trait,label)
);

CREATE TABLE rest.assoc_master (
 id BIGINT NOT NULL,
 study TEXT NOT NULL,
 trait TEXT NOT NULL,
 tech TEXT,
 build TEXT,
 imputed TEXT,
 analysis TEXT,
 pmid TEXT,
 pubdate DATE,
 first_author TEXT,
 last_author TEXT
);

CREATE TABLE rest.assoc_results (
 id BIGINT NOT NULL,
 variant_name TEXT NOT NULL,
 chrom TEXT NOT NULL,
 pos BIGINT NOT NULL,
 ref_allele TEXT NOT NULL,
 ref_freq REAL,
 log_pvalue REAL NOT NULL,
 beta DOUBLE PRECISION,
 se DOUBLE PRECISION,
 score_stat DOUBLE PRECISION,
 effect_allele TEXT,
 noneffect_allele TEXT
);

CREATE TABLE rest.recomb (
  id BIGINT PRIMARY KEY,
  name text NOT NULL,
  build text NOT NULL,
  version text NOT NULL
);

CREATE TABLE rest.recomb_results (
  id BIGINT NOT NULL,
  chromosome text NOT NULL,
  position BIGINT NOT NULL,
  recomb_rate REAL NOT NULL,
  pos_cm REAL
);

CREATE TABLE rest.interval (
  id BIGINT PRIMARY KEY,
  study TEXT NOT NULL,
  build TEXT NOT NULL,
  version TEXT NOT NULL,
  type TEXT,
  assay TEXT,
  tissue TEXT,
  protein TEXT,
  histone TEXT,
  cell_line TEXT,
  pmid TEXT,
  description TEXT,
  url TEXT
);

CREATE TABLE rest.interval_results (
  id BIGINT NOT NULL,
  public_id TEXT,
  chrom TEXT NOT NULL,
  start BIGINT NOT NULL,
  "end" BIGINT NOT NULL,
  strand CHAR(1),
  annotation JSONB
);

CREATE TABLE rest.dbsnp_master (
  id BIGINT NOT NULL,
  genome_build TEXT NOT NULL,
  dbsnp_build TEXT NOT NULL,
  taxid INTEGER NOT NULL,
  organism TEXT
);

CREATE TABLE rest.dbsnp_snps (
  id BIGINT NOT NULL,
  rsid TEXT NOT NULL,
  chrom TEXT NOT NULL,
  pos BIGINT NOT NULL,
  ref TEXT NOT NULL,
  alt TEXT NOT NULL
);

CREATE TABLE rest.dbsnp_trans (
  id BIGINT NOT NULL,
  rsid_old TEXT NOT NULL,
  rsid_current TEXT NOT NULL
);

CREATE TABLE rest.gene_master (
  id BIGINT NOT NULL,
  source TEXT NOT NULL,
  version TEXT NOT NULL,
  genome_build TEXT NOT NULL,
  taxid INTEGER NOT NULL,
  organism TEXT
);

CREATE TABLE rest.gene_data (
  id BIGINT NOT NULL,
  feature_type TEXT NOT NULL,
  chrom TEXT NOT NULL,
  start BIGINT NOT NULL,
  "end" BIGINT NOT NULL,
  strand CHAR(1),
  gene_id TEXT,
  gene_name TEXT,
  transcript_id TEXT,
  exon_id TEXT,
  annotation JSONB
);

CREATE TABLE rest.gwascat_master (
  id BIGINT NOT NULL,
  name TEXT NOT NULL,
  genome_build TEXT NOT NULL,
  date_inserted TIMESTAMP WITH TIME ZONE NOT NULL,
  catalog_version TEXT NOT NULL
);

CREATE TABLE rest.gwascat_data (
  id BIGINT NOT NULL,
  variant TEXT NOT NULL,
  rsid TEXT,
  chrom TEXT NOT NULL,
  pos BIGINT NOT NULL,
  ref TEXT NOT NULL,
  alt TEXT NOT NULL,
  trait TEXT NOT NULL,
  trait_group TEXT,
  risk_allele TEXT,
  risk_frq REAL,
  log_pvalue REAL NOT NULL,
  or_beta REAL,
  genes TEXT,
  pmid TEXT,
  pubdate DATE,
  first_author TEXT,
  study TEXT
);
