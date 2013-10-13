# The Onionoo-like API provided by torsearch

This is a document explaining the Onionoo-like API implemented by torsearch. The document will probably later be further extended.

## General API description

Like with Onionoo, clients send GET requests (which may contain GET request arguments, as in GET /summary?search=searchstring).
The API responds with JSON replies.
HTTP 400 is returned if the API does not understand what the client is saying.

## Upper limit

With Onionoo, the whole result set is bounded by a date range. Namely, Onionoo only deals with relays that are or have been running in the past week (or some small number of days.) In our case, these kinds of bounds are not present by design. Hence all that the torsearch API returns will always have an upper limit, in terms of the amount of result nodes / entries.

As of now, the upper limit of any kinds of results returned is **500**.

(Perhaps it would be best to keep two values: default upper limit (lower than 500), and maximum upper limit. For now, we want to see if we have, so to speak, some wiggle (temporal) space.)

## Result order

Results are always ordered by the status entry **valid-after** field, in **descending** order. (In the future, specifying a way of re-ordering results should be possible.)

## offset and limit

Whatever the results may be, it is always possible to specify the following types of parameters, which are always optional:

 - **offset** - skip the given number of results. This is one of the ways to "browse" through the whole result set.
   Must be a positive integer.

 - **limit** - limit the result set to be returned to the given number. Can be safely used together with **offset**.
   Must be a positive integer not larger than the upper limit, otherwise ignored.

## Document types

### Summary documents

Summary documents contain short summaries of relays with nicknames, fingerprints, IP addresses, and running information. Summary documents contain the following fields:

 - **relays_published**: UTC timestamp (YYYY-MM-DD hh:mm:ss) when the last known relay network status consensus started being valid. Indicates how recent the relay summaries in this document are. Required field.
 - **count**: the number of relays returned in this response.
 - **relays**: Array of objects representing relay summaries. Required field. Each array object contains the following key-value pairs:
   - **n**: Relay nickname consisting of 1-19 alphanumerical characters. Optional field. Omitted if the relay nickname is _"Unnamed"_.
   - **f**: Relay fingerprint consisting of 40 upper-case hexadecimal characters. Required field.
   - **a**: Array of (for now) IPv4 addresses which the relay used to exit to the Internet during the last consensus this relay was present in. Required field.
   - **r**:  Boolean field saying whether this relay was listed as running in the last relay network status consensus. Required field.

### Detail documents

Detail documents contain more details about relays. Detail documents contain the following fields:

 - **relays_published**: UTC timestamp (YYYY-MM-DD hh:mm:ss) when the last known relay network status consensus started being valid. Indicates how recent the relay summaries in this document are. Required field.
 - **count**: the number of relays returned in this response.
 - **relays**: Array of objects representing relay summaries. Required field. Each array object contains the following key-value pairs:
   - **nickname**: Relay nickname consisting of 1-19 alphanumerical characters. Optional field. Omitted if the relay nickname is _"Unnamed"_.
   - **fingerprint**: Relay fingerprint consisting of 40 upper-case hexadecimal characters. Required field.
   - **exit_addresses**: Array of (for now) IPv4 addresses that the relay used to exit to the Internet in the past 24 hours, as reported by the latest consensus. Required field (for now, because we are not returning *or_addresses* as of now.)
   - **last_seen**: UTC timestamp (YYYY-MM-DD hh:mm:ss) when this relay was last seen in a network status consensus. Required field.
   - **first_seen**: UTC timestamp (YYYY-MM-DD hh:mm:ss) when this relay was first seen in a network status consensus. Required field.
   - **running**: Boolean field saying whether this relay was listed as running in the last relay network status consensus. Required field.

### Network status entry documents

Network status entry documents provide a list of network statuses that a given relay is present in.

For now, two different result formats are provided: the full form and the condensed form. By default, the full result form is used. The condensed form can be retrieved (as mentioned below) by setting the **condensed** parameter in the query to true. This is not elegant, and the full form will be retired after the condensed form is finalized and sufficiently tested.

The default, full result form contains the following fields:

 - **fingerprint**: Relay fingerprint consisting of 40 upper-case hexadecimal characters. Required field.
 - **count**: the number of entries returned in this response.
 - **relays_published**: UTC timestamp (YYYY-MM-DD hh:mm:ss) when the last known relay network status consensus started being valid. Required field.
 - **entries**: Array of objects representing router status summaries. Required field. Each array object contains the following key-value pairs:
   - **nickname**: Relay nickname consisting of 1-19 alphanumerical characters. Optional field. Omitted if the relay nickname is _"Unnamed"_.
   - **exit_addresses**: Array of (for now) IPv4 addresses that the relay used to exit to the Internet in the past 24 hours, as of and reported by this network status. Required field (for now, because we are not returning *or_addresses* as of now.)
   - **valid-after**: UTC timestamp (YYYY-MM-DD hh:mm:ss) when this network status became valid. The timestamp uniquely indicates the consensus which contains this network status which, in turn, includes this particular relay. Required field.

The condensed result form contains the following fields:

 - **fingerprint**: Relay fingerprint consisting of 40 upper-case hexadecimal characters. Required field.
 - **count**: the number of range entries (the number of objects in the list under the field 'ranges') returned in this response. Required field.
 - **total_status_count**: the total number of router status entries covered by this result set: the overall span of status entries explained by these results. (e.g., 500, i.e. our upper limit.) Required field.
 - **relays_published**: UTC timestamp (YYYY-MM-DD hh:mm:ss) when the last known relay network status consensus started being valid. Required field.
 - **ranges**: Array of objects representing router status entry _ranges_, i.e. intervals covered by their valid-after fields. Required field. Each array object contains the following key-value pairs:
   - **last_nickname**: Relay nickname (consisting of 1-19 alphanumerical characters) that the chronologically last status entry in this particular range had. Optional field. Omitted if the relay nickname is _"Unnamed"_.
   - **last_addresses**: Array of (for now) IPv4 addresses that the relay used to exit to the Internet in the past 24 hours, as of and reported by the chronologically last relay status in this particular range. Required field (for now, because we are not returning *or_addresses* as of now.)
   - **valid_after_from**: UTC timestamp (YYYY-MM-DD hh:mm:ss) that this relay status range starts at. That is, the status range covers a time interval starting with **valid_after_from**. 
   - **valid_after_to**: UTC timestamp (YYYY-MM-DD hh:mm:ss) that this relay status range ends with. That is, the status range covers a time interval ending with **valid_after_to**, **inclusive**.

## Methods

The following methods each return a single document containing zero or more relay documents.

**GET summary**

**GET details**

Each of these documents can be parameterized to select only a subset of relay documents to be included in the response. If multiple parameters are specified, they are combined using a logical AND operation, meaning that only the intersection of relays matching all parameters is returned.

 - **running** - Return only running (parameter value true) or only non-running relays (paramter value false or 0). Parameter values are case-insensitive.

 - **search** - Return only relays with the parameter value matching (part of a) nickname, (possibly $-prefixed) beginning of a fingerprint, or beginning of an IP address. Searches are case-insensitive.
   For now, "part of a" (nickname, fingerprint, address) means that the value for a given field has to begin with this search string. A search for "mor" will include "moria1", but a search for "oria" will not. This is valid for all three field types.

 - **lookup** - Return only the relay with the parameter value matching the fingerprint. Lookups only work for full fingerprints.

 - **from** - Return only relays that have been featured in consensus not before some date. For example, "?from=2012-05-01" will return relays (i.e., will match against fingerprints) that have been present in consensuses from 2012-05-01 00:00:00 and onwards.

 - **to** - Return only relays that have been featured in consensus up until some date, **not inclusive**. For example "?from=2012-05-01&to=2013" will return relays that have been present in consensuses not before 2012-05-01 00:00:00 and not after 2012-12-31 23:00:00 (this being the last consensus before the date matching "2013".)

These latter two parameters accept date and time strings in the format "YYYY-mm-dd HH:MM:SS" (years, months, days, hours, minutes, seconds), but one can omit elements starting from the right of the string, up until YYYY. For example, "2013" will resolve to "2013-01-01 00:00:00" (and hence indicate this particular consensus document, with that particular valid-after value), "2013-02" will resolve to "2013-02-01 00:00:00", "2013-02-15" will resolve to "2013-02-15 00:00:00".

Additionally as noted, **offset** and **limit** are supported as well.

**offset** is applied after all the other aforementioned parameters, and lastly, **limit** is applied on top of **offset**. Hence making a query such as "GET details?search=200.&from=2013-02&offset=50&limit=100" means, "get a list of relays (identified by fingerprint) sorted by their valid-after field in descending order, with status entries valid not before February 2013, matching an IP address wildcard '200.*', but offset results by 50 relay entries, and return only 100 entries of that eventual result set."

The following method returns a single document containing zero or more network status entry documents.

**GET statuses**

While the above parameters are optional for the summary and details documents, **GET statuses** requires the **lookup** parameter, which works as above:

 - **lookup** - Specify a particular (whole) fingerprint.

Apart from the mandatory lookup parameter, one can optionally supply any combination of the following parameters:

 - **from** - Return only network statuses that have been featured in consensus not before some date. For example, "?from=2012-05-01" will return network status entries that have been present in consensuses from 2012-05-01 00:00:00 and onwards.

 - **to** - Return only network statuses that have been featured in consensus up until some date, **not inclusive**. For example "?from=2012-05-01&to=2013" will return network status entries that have been present in consensuses not before 2012-05-01 00:00:00 and not after 2012-12-31 23:00:00 (this being the last consensus before the date matching "2013".)

 - Additionally,

  - **offset**
  - **limit**

are accepted as well, and work in the same way as they work for the summary and details documents: they are applied after all the other search query parameters, offset taking precedence to limit.

Finally, as mentioned above, one can supply

 - **condensed** - if set to true, will return network status entries in the condensed/compressed form, as detailed above. The condensed form will probably become the default, and the non-condensed format will be retired.

Somewhat unrelated (this might go into a separate doc): the backend works in such a way that if the GET statuses API point is queried with a fingerprint that it has not encountered before (since the last time the underlying database was restarted, to be exact), it will take a bit longer to reply (it will depend on how many network statuses the fingerprint in question is featured in). But after that first reply, subsequent queries will run faster, as a rule of thumb. This is unavoidable and is related to the way indexes and query results are cached in the database. We of course do have to worry about worst case scenarios, but if they are good enough, all is well.
