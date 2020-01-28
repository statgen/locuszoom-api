/*
This stored procedure is necessary to ensure postgres caches the execution plan.
Otherwise, the planning time for executing this query each time is excessively high.
Additionally, this procedure must be executed 5 times (not changeable!) before postgres
will switch to using the generic plan instead of the custom plan, which requires additional
time to execute.
*/
CREATE OR REPLACE FUNCTION rest.phewas_query(v TEXT, builds TEXT[])
RETURNS TABLE(
	id BIGINT,
	study TEXT,
	trait TEXT,
	trait_label TEXT,
	trait_group TEXT,
	tech TEXT,
	build TEXT,
	description TEXT,
	pmid TEXT,
	variant TEXT,
	chromosome TEXT,
	"position" BIGINT,
	ref_allele TEXT,
	ref_allele_freq REAL,
	log_pvalue REAL,
	beta DOUBLE PRECISION,
	se DOUBLE PRECISION,
	score_test_stat DOUBLE PRECISION
) AS
$$
BEGIN
	RETURN QUERY SELECT
  sa.id,sa.study,sa.trait,traits.label as trait_label,traits.grouping as trait_group,sa.tech,sa.build,sa.analysis as description,sa.pmid,
  sr.variant_name as variant,sr.chrom as chromosome,sr.pos as position,sr.ref_allele,sr.ref_freq as ref_allele_freq,
  sr.log_pvalue,sr.beta,sr.se,sr.score_stat as score_test_stat
	FROM rest.assoc_master sa
	  JOIN rest.assoc_results sr ON sa.id = sr.id
	  LEFT JOIN rest.traits ON sa.trait = traits.trait
	WHERE variant_name = v
	  AND sa.build = ANY(builds)
	  AND traits.grouping IS NOT NULL
	  AND traits.label IS NOT NULL
	ORDER BY log_pvalue DESC;
END;
$$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION rest.sp_transcripts_exons(
  IN gene_ids varchar[] = NULL,
  IN transcript_sources bigint[] = NULL)
  RETURNS TABLE(source_id bigint,
                gene_id varchar,
                transcript_id varchar,
                transcript_name varchar,
                transcript_chrom varchar,
                transcript_start bigint,
                transcript_end bigint,
                transcript_strand char(1),
                exon_id varchar,
                exon_start bigint,
                exon_end bigint,
                exon_strand char(1)) AS
$BODY$
DECLARE
  queryText varchar;
BEGIN
  queryText = 'SELECT transcripts.source_id as source_id,
        transcripts.gene_id as gene_id,
        transcripts.transcript_id AS transcript_id,
        transcripts.transcript_name AS transcript_name,
        transcripts.chromosome AS transcript_chrom,
        transcripts.interval_start AS transcript_start,
        transcripts.interval_end AS transcript_end,
        transcripts.strand AS transcript_strand,
        exons.exon_id AS exon_id,
        exons.interval_start AS exon_start,
        exons.interval_end AS exon_end,
        exons.strand AS exon_strand
    FROM rest.transcripts
    LEFT OUTER JOIN rest.exons ON transcripts.transcript_id = exons.transcript_id AND transcripts.source_id = exons.source_id
		WHERE (transcripts.gene_id = ANY($1) OR $1 IS NULL)';

    IF transcript_sources IS NOT NULL THEN
      queryText := queryText || ' AND (transcripts.source_id = ANY($2)) ';
    END IF;

    queryText := queryText || ';';
    RETURN QUERY EXECUTE queryText USING gene_ids, transcript_sources;
END;
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION rest.sp_single_analysis_region(
    IN analysis_ids bigint[],
    IN chromosomes text[],
    IN region_start bigint,
    IN region_end bigint)
  RETURNS TABLE(id bigint, analysis_id bigint, variant_name text, chromosome text, "position" bigint, ref_allele_freq real, ref_allele text, p_value double precision, score_test_stat double precision) AS
$BODY$
BEGIN
	 RETURN QUERY SELECT a.id, a.analysis_id, a.variant_name, a.chromosome, a.position, a.ref_allele_freq, a.ref_allele, a.p_value, a.score_test_stat
		FROM rest.single_analyses_results AS a
		WHERE (a.analysis_id = ANY(analysis_ids) OR analysis_ids IS NULL) AND
			(a.chromosome = ANY(chromosomes) OR chromosomes IS NULL) AND
			(a.position >= region_start OR region_start IS NULL) AND
			(a.position <= region_end OR region_end IS NULL);
END;
$BODY$
LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION rest.sp_single_analysis(IN analysis_id bigint[])
  RETURNS TABLE(id bigint, study text, trait text, tech text, build text, imputed text) AS
$BODY$
BEGIN
	 RETURN QUERY SELECT a.id, a.study, a.trait, a.tech, a.build, a.imputed
		FROM rest.single_analyses AS a
		WHERE (a.id = ANY(analysis_id) OR analysis_id IS NULL);
END;
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION rest.sp_annotation_sources(IN source_ids bigint[])
  RETURNS TABLE(source_id bigint, source_name varchar, build varchar, version varchar) AS
$BODY$
BEGIN
  RETURN QUERY SELECT res.source_id, res.source_name, res.build, res.version FROM rest.annotationSources AS res
		WHERE (res.source_id = ANY(source_ids) OR source_ids IS NULL);
END;
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION rest.sp_annotation_genes(
  IN gene_names varchar[] = NULL,
  IN gene_sources bigint[] = NULL,
  IN region_start bigint = NULL,
  IN start_comparator varchar = NULL,
  IN region_end bigint = NULL,
  IN end_comparator varchar = NULL,
  IN gene_chromosome varchar = NULL)
  RETURNS TABLE(source_id bigint,
                gene_id varchar,
                gene_name varchar,
                chromosome varchar,
                gene_start bigint,
                gene_end bigint,
                gene_strand char(1),
                transcript_id varchar,
                transcript_name varchar,
                transcript_start bigint,
                transcript_end bigint,
                transcript_strand char(1),
                exon_id varchar,
                exon_start bigint,
                exon_end bigint,
                exon_strand char(1)) AS
$BODY$
DECLARE
  queryText varchar;
BEGIN
  queryText = 'SELECT genes.source_id AS source_id,
        genes.gene_id AS gene_id,
        genes.gene_name AS gene_name,
        genes.chromosome AS chromosome,
        genes.interval_start AS gene_start,
        genes.interval_end AS gene_end,
        genes.strand AS gene_strand,
        transcripts.transcript_id AS transcript_id,
        transcripts.transcript_name AS transcript_name,
        transcripts.interval_start AS transcript_start,
        transcripts.interval_end AS transcript_end,
        transcripts.strand AS transcript_strand,
        exons.exon_id AS exon_id,
        exons.interval_start AS exon_start,
        exons.interval_end AS exon_end,
        exons.strand AS exon_strand
    FROM rest.genes
      LEFT OUTER JOIN rest.transcripts ON genes.source_id = transcripts.source_id AND genes.gene_id = transcripts.gene_id
        LEFT OUTER JOIN rest.exons ON genes.source_id = exons.source_id AND genes.gene_id = exons.gene_id 
		WHERE (genes.gene_name = ANY($1) OR $1 IS NULL)';

    IF gene_sources IS NOT NULL THEN
      queryText := queryText || ' AND (genes.source_id = ANY($2)) ';
    END IF;
    IF gene_chromosome IS NOT NULL THEN
      queryText := queryText || ' AND (genes.chromosome = $3) ';
    END IF;
    IF (region_start IS NOT NULL AND start_comparator IS NOT NULL) THEN
      queryText := queryText || ' AND (genes.interval_start ' || start_comparator ||  ' $4)';
    END IF;
    IF (region_end IS NOT NULL AND end_comparator IS NOT NULL) THEN
      queryText := queryText || ' AND (genes.interval_end ' || end_comparator || ' $5) ';
    END IF;

    queryText := queryText || ';';
    RETURN QUERY EXECUTE queryText USING gene_names, gene_sources, gene_chromosome, region_start, region_end;
END;
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION rest.sp_single_analysis_region_sorted(
    IN analysis_ids bigint[],
    IN chromosomes text[],
    IN region_start bigint,
    IN region_end bigint,
    IN sorted text[],
    IN descending boolean[])
  RETURNS TABLE(id bigint, analysis_id bigint, variant_name text, chromosome text, "position" bigint, ref_allele_freq real, ref_allele text, p_value double precision, score_test_stat double precision) AS
$BODY$
DECLARE
        sql text;
BEGIN
        sql := 'SELECT a.id, a.analysis_id, a.variant_name, a.chromosome, a.position, a.ref_allele_freq, a.ref_allele, a.p_value, a.score_test_stat
                FROM rest.single_analyses_results AS a
                WHERE (a.analysis_id = ANY($1) OR $1 IS NULL) AND
                        (a.chromosome = ANY($2) OR $2 IS NULL) AND
                        (a.position >= $3 OR $3 IS NULL) AND
                        (a.position <= $4 OR $4 IS NULL)';

        IF array_length(sorted, 1) > 0 AND array_length(sorted, 1) = array_length(descending, 1) THEN
                IF NOT descending[1] THEN
                        sql = sql || ' ORDER BY ' || sorted[1];
                ELSE
                        sql = sql || ' ORDER BY ' || sorted[1] || ' DESC';
                END IF;
                FOR i IN 2..array_length(sorted, 1) LOOP
                        IF NOT descending[i] THEN
                                sql = sql || ', ' || sorted[i];
                        ELSE
                                sql = sql || ', ' || sorted[i] || ' DESC';
                        END IF;
                END LOOP;
        END IF;

        sql = sql || ' LIMIT 1000';

        -- RAISE NOTICE '%', sql;

        RETURN QUERY EXECUTE sql USING analysis_ids, chromosomes, region_start, region_end;
END;
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION rest.sp_score_cov(IN analysis_id bigint[]) 
  RETURNS TABLE(id bigint, study text, trait text, tech text, build text, imputed text) AS
$BODY$
BEGIN
        RETURN QUERY SELECT a.id, a.study, a.trait, a.tech, a.build, a.imputed
                FROM rest.single_analyses AS a
                WHERE (analysis_id IS NULL OR a.id = ANY(analysis_id)) AND a.id IN (SELECT DISTINCT p.analysis_id FROM rest.variants_pair_stat AS p);
END;
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION rest.sp_score_cov_submatrix_by_pos(
    IN analysis_ids bigint[],
    IN chromosomes1 text[],
    IN region_start1 bigint,
    IN region_end1 bigint,
    IN chromosomes2 text[],
    IN region_start2 bigint,
    IN region_end2 bigint)
  RETURNS TABLE(id bigint, analysis_id bigint, type_id bigint, variant_name1 text, chromosome1 text, "position1" bigint, variant_name2 text, chromosome2 text, "position2" bigint, statistic double precision) AS
$BODY$
BEGIN
        RETURN QUERY SELECT a.id, a.analysis_id, a.type_id, a.variant_name1, a.chromosome1, a.position1, a.variant_name2, a.chromosome2, a.position2, a.statistic
                FROM rest.variants_pair_stat AS a
                WHERE a.type_id = 1 AND
                        (a.analysis_id = ANY(analysis_ids) OR analysis_ids IS NULL) AND
                        (a.chromosome1 = ANY(chromosomes1) OR chromosomes1 IS NULL) AND
                        (a.position1 >= region_start1 OR region_start1 IS NULL) AND 
                        (a.position1 <= region_end1 OR region_end1 IS NULL) AND
                        (a.chromosome2 = ANY(chromosomes2) OR chromosomes2 IS NULL) AND
                        (a.position2 >= region_start2 OR region_start2 IS NULL) AND 
                        (a.position2 <= region_end2 OR region_end2 IS NULL);
END;
$BODY$
LANGUAGE plpgsql;
