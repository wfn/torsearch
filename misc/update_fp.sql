-- if we messed something up, or if we kept importing to fp table before we
-- found an ugly bug where we e.g. weren't joining fp table with the latest
-- statusentry rows, we need to run this. (this shouldn't be ever run in
-- production, with db-model-bug-free code.
-- only putting this here for reference.)

-- will run for >= 1h on a simple sata 7200rpm with 6gb of memory for pgsql.)

update fingerprint set
  digest = l.digest, last_va = l.validafter, address = l.address,
    nickname = l.nickname, sid = l.id
  from (
    select distinct on (fingerprint) fingerprint, digest, validafter, address,
      nickname, id
    from statusentry
    order by fingerprint, validafter DESC
  ) as l
where fingerprint.fingerprint = l.fingerprint;
