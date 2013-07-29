-- no sequential read, will serve a subset of our purposes:

select * from (select distinct on (fingerprint) fingerprint, validafter, nickname from statusentry where nickname like 'moria1' order by fingerprint, validafter desc) as subq order by validafter desc limit 100;
