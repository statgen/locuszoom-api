#!/usr/bin/env python3
import psycopg2
import gzip

# This script dumps example data from the database for use in test cases
# for the LocusZoom API.

# Database connection
con = psycopg2.connect("dbname=api_internal_dev user=welchr host=127.0.0.1 port=5432")
cur = con.cursor()

# Dump recombination rates
print("Dumping recombination rate master...")
with gzip.open("table_recomb.gz", "w") as fp:
  cur.copy_to(fp, "rest.recomb")

# Dump recombination rates
print("Dumping recombination rates...")
cur.execute("""
  CREATE TEMPORARY TABLE recomb_test AS
  SELECT * FROM rest.recomb_results WHERE chromosome = '21' AND position > 0 AND position <= 10986933
  UNION
  SELECT * FROM rest.recomb_results WHERE chromosome = '21' AND position >= 10870000 AND position <= 10890000
  UNION
  SELECT * FROM rest.recomb_results WHERE chromosome = '21' AND position >= 10870000 AND position <= 10906725
  UNION
  SELECT * FROM rest.recomb_results WHERE chromosome = '21' AND position >= 10906720 AND position <= 10906920
  UNION
  SELECT * FROM rest.recomb_results WHERE chromosome = '21' AND position >= 48097610 AND position <= 49000000
""")

with gzip.open("table_recomb_results.gz", "w") as fp:
  cur.copy_to(fp, "recomb_test")

# Dump genes
print("Dumping genes...")
cur.execute("""
  CREATE TEMPORARY TABLE gene_test AS
  SELECT * FROM rest.gene_data_id2 WHERE chrom = '16' AND "end" > 56985060 AND start <= 57022881
  UNION
  SELECT * FROM rest.gene_data_id2 WHERE chrom = '16' AND "end" > 54164840 AND start <= 54265502
  UNION
  SELECT * FROM rest.gene_data_id2 WHERE chrom = '16' AND "end" > 77189937 AND start <= 80189937
  UNION
  SELECT * FROM rest.gene_data_id2 WHERE chrom = '16' AND "end" > 56985060 AND start <= 57022881
  UNION
  SELECT * FROM rest.gene_data WHERE id = 1 AND gene_name = 'CSF3'
""")

with gzip.open("table_gene_data.gz", "w") as fp:
  cur.copy_to(fp, "gene_test")

# Dump studies
print("Dumping studies...")
cur.execute("""
  CREATE TEMPORARY TABLE assoc_master_test AS
  SELECT * FROM rest.assoc_master WHERE id <= 45
""")

with gzip.open("table_assoc_master.gz", "w") as fp:
  cur.copy_to(fp, "assoc_master_test")

# Dump assoc results
print("Dumping assoc results...")
cur.execute("""
  CREATE TEMPORARY TABLE assoc_results_test AS
  SELECT * FROM rest.assoc_results WHERE id = 24 and chrom = '16' AND pos < 200000000
  UNION
  SELECT * FROM rest.assoc_results WHERE id = 45 and chrom = '2' AND pos > 242023897 AND pos < 242025881
  UNION
  SELECT * FROM rest.assoc_results WHERE variant_name = '10:114758349_C/T'
""")

with gzip.open("table_assoc_results.gz", "w") as fp:
  cur.copy_to(fp, "assoc_results_test")

# Dump intervals
print("Dumping intervals...")
cur.execute("""
  CREATE TEMPORARY TABLE interval_results_test AS
  SELECT * FROM rest.interval_results WHERE id = 18 and chrom = '16' AND "end" >= 53519169 AND start <= 54119169
""")

with gzip.open("table_interval_results.gz", "w") as fp:
  cur.copy_to(fp, "interval_results_test")

# Dump GWAS catalog master
print("Dumping GWAS catalog master...")
with gzip.open("table_gwascat_master.gz", "w") as fp:
  cur.copy_to(fp, "rest.gwascat_master")

# Dump GWAS catalog data
print("Dumping GWAS catalog data...")
cur.execute("""
  CREATE TEMPORARY TABLE gwascat_data_test AS
  SELECT * FROM rest.gwascat_data WHERE rsid = 'rs7903146' UNION (SELECT * FROM rest.gwascat_data WHERE LENGTH(alt) > 1 AND id = 2 limit 5)
""")

with gzip.open("table_gwascat_data.gz", "w") as fp:
  cur.copy_to(fp, "gwascat_data_test")

# Dump dbSNP master
print("Dumping dbSNP master...")
with gzip.open("table_dbsnp_master.gz", "w") as fp:
  cur.copy_to(fp, "rest.dbsnp_master")

# Dump dbSNP snps
print("Dumping dbSNP SNPs...")
cur.execute("""
  CREATE TEMPORARY TABLE dbsnp_snps_test AS
  SELECT * FROM rest.dbsnp_snps WHERE rsid = 'rs7903146'
""")

# Dump traits
print("Dumping traits...")
with gzip.open("table_traits.gz", "w") as fp:
  cur.copy_to(fp, "rest.traits")

con.rollback()
