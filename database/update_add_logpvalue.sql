SET search_path TO rest;

BEGIN;
  CREATE TABLE tmp_results (LIKE single_analyses_results INCLUDING ALL);
  INSERT INTO tmp_results (SELECT * FROM single_analyses_results);
  ALTER TABLE tmp_results ADD COLUMN log_pvalue REAL;
  UPDATE tmp_results SET log_pvalue = -log(p_value);
  CREATE INDEX log_pvalue_index ON tmp_results USING btree(log_pvalue);
  ALTER TABLE single_analyses_results RENAME TO old_results;
  ALTER TABLE tmp_results RENAME TO single_analyses_results;
  ALTER SEQUENCE single_analyses_results_id_seq OWNED BY single_analyses_results.id;
COMMIT;

/* After checking out the table to make sure everything looks OK:
DROP TABLE old_results;
*/
