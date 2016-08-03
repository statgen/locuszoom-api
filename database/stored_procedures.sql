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
