-- this might look like a mess, but this query, to the best of my understanding, makes a lot of sense and is rather optimal.
-- there are two tables: descriptor and statusentry. we want to get a (unique, in terms of fingerprints) list of all the
-- fingerprints for a given nickname, sorted by tor consensus valid_after (descending), together with certain values from
-- both the descriptor as well as the statusentry tables.

-- the descriptor table is (much) smaller than the statusentry table. we search for fingerprints in the descriptor table,
-- extract unique fingerprints (depending on their publishing date), join with statusentry (fingerprint + descriptor digest),
-- and again extract only unique fingerprints, this time depending on 'validafter'.

-- we need to do this nested distinct+sort, because:
--   for a given nickname,
--     there will be many fingerprints in the descriptor table.
--     for a given fingerprint,
--       there will be many occurences of it / rows featuring it in the descriptor table.
--     we select the occurences depending on their 'freshness' (descriptor.published)
--     each occurence is a (fingerprint, descriptor) pair which is unique to the descriptor table.
--  for a given (fingerprint, descriptor) pair,
--    there will be many occurences of it / rows featuring it in the statusentry table.
--    each (fp, desc) occurence in the statusentry field can be identified by (fp, desc, validafter).
--  we select the statusentry occurences (descriptor network statuses) depending on their statusentry.validafter
--  we return a unique set of fingerprints associated with a given nickname, sorted by validafter (descending).

select * from
(
  select distinct on (fingerprint) -- outer distinct on statusentry
  * from
  (
    select descriptor.*, statusentry.validafter from
    (
      select distinct on (fingerprint) -- inner distinct on descriptor
      fingerprint, descriptor, nickname, published
      from descriptor where
        lower(nickname) = 'default'
        order by fingerprint, published desc -- first, let's get distinct most recently published fingerprints from descriptor table
    ) as descriptor,
    statusentry where                        -- and join them with statusentry using a near-unique key (fingerprint+descriptor)
      substr(statusentry.fingerprint, 0, 12) = substr(descriptor.fingerprint, 0, 12)
      and substr(lower(statusentry.digest), 0, 12) = substr(descriptor.descriptor, 0, 12)
  ) as everything                            -- statusentry will still return lots of rows per a single descriptor
  order by fingerprint, validafter desc      -- (that was unique in the descr.table) - therefore, need to re-select distinct again,
) as sorted                                  -- this time distinguishing on those fingerprints with the latest validafter. 
order by validafter desc;                    -- the rows returned will have the latest fingerprints, but we still need to (re-)sort.

-- below is a sample EXPLAIN output:

"Sort  (cost=2165.62..2165.62 rows=1 width=107)"
"  Sort Key: statusentry.validafter"
"  ->  Unique  (cost=2165.59..2165.60 rows=1 width=107)"
"        ->  Sort  (cost=2165.59..2165.59 rows=1 width=107)"
"              Sort Key: public.descriptor.fingerprint, statusentry.validafter"
"              ->  Nested Loop  (cost=2120.97..2165.58 rows=1 width=107)"
"                    ->  Unique  (cost=2120.95..2123.61 rows=2 width=99)"
"                          ->  Sort  (cost=2120.95..2122.28 rows=532 width=99)"
"                                Sort Key: public.descriptor.fingerprint, public.descriptor.published"
"                                ->  Bitmap Heap Scan on descriptor  (cost=13.78..2096.87 rows=532 width=99)"
"                                      Recheck Cond: (lower((nickname)::text) = 'moria1'::text)"
"                                      ->  Bitmap Index Scan on descriptor_lower_idx  (cost=0.00..13.64 rows=532 width=0)"
"                                            Index Cond: (lower((nickname)::text) = 'moria1'::text)"
"                    ->  Index Scan using statusentry_substr_substr1_idx on statusentry  (cost=0.01..20.95 rows=1 width=90)"
"                          Index Cond: ((substr((fingerprint)::text, 0, 12) = substr((public.descriptor.fingerprint)::text, 0, 12)) AND (substr(lower((digest)::text), 0, 12) = substr((public.descriptor.descriptor)::text, 0, 12)))"

