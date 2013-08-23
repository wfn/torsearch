-- update the first_va field in the fingerprint table.
-- when we make the final import of all the olden status entry archives,
-- we'll only need to do this once.

UPDATE fingerprint SET first_va = oldest.validafter
FROM (SELECT DISTINCT ON (fingerprint) fingerprint, validafter FROM statusentry ORDER BY fingerprint, validafter ASC) AS oldest
WHERE fingerprint.fingerprint = oldest.fingerprint;
