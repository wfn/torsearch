# Use cases and examples of probing the searchable metrics archive API

Here are some examples how the Onionoo-like API [See its documentation here](https://github.com/wfn/torsearch/blob/master/docs/onionoo_api.md) can be used.

## Get summary information about relays

[Atlas](https://atlas.torproject.org/), [Globe](http://globe.rndm.de/) and others use the [Onionoo](https://onionoo.torproject.org/) protocol and backend for getting information about relays that have or had been recently running (present in the consensus.) This system provides a scalable solution to query and get information about relays in the more distant past, too; all within the framework of an Onionoo-derived protocol. It extends the API as well.

This archive can be queried to return the Onionoo-derived Relay Summary and Details documents (bridges are not included, at least not for now), as well as Network Status documents (a new addition.)

The results are always sorted by the date of the network status (associated with each result entry) in which each relay was present (i.e., the consensus valid-after field), in descending order.

 * [get a list of most recently run(ning) relays](http://ts.mkj.lt:5555/details) (get the Details document without specifying any parameters.) As these documents are constantly updated, it effectively means "get a list of currently running relays." (Note the [upper limit detailed in the Onionoo-like API doc](https://github.com/wfn/torsearch/blob/master/docs/onionoo_api.md#upper-limit).)

 * [iterate over the document](http://ts.mkj.lt:5555/details?offset=500); [use result limiting in combination with offset](http://ts.mkj.lt:5555/details?offset=500&limit=250)

 * [get a shorter summary document about recently run(ning) relays](http://ts.mkj.lt:5555/summary)

 * [get a list of relays that have run in a specific date range](http://ts.mkj.lt:5555/details?from=2013-02-25&to=2013-04)

We call this kind of usage "Onionoo-like": the types of queries that are run on Onionoo Summary and Details documents can be run on this system.

## Search for relays

Like with Onionoo, one can query the system to search for specific relays using [various search criteria](https://github.com/wfn/torsearch/blob/master/docs/onionoo_api.md#methods).

 * [search for a specific relays (all its fingerprints over time) using its full nickname](http://ts.mkj.lt:5555/details?search=moria1)

 * [search for all relays matching a full nickname that is shared by many](http://ts.mkj.lt:5555/details?search=unnamed)

 * [search using a part of a nickname](http://ts.mkj.lt:5555/details?search=mor)

 * [search by specifying a particular fingerprint](http://ts.mkj.lt:5555/details?lookup=4B35EA75FD72A0115451F69200ABDB3CF96A8087)

 * [search by IPv4 address](http://ts.mkj.lt:5555/details?search=79.98.25.182)

 * [search by a part of an IPv4 address](http://ts.mkj.lt:5555/details?search=79.98.)

 * [search by a part of a nickname, in a specific consensus date range, using offset and limit](http://ts.mkj.lt:5555/details?search=mor&from=2009-05&to=2012&offset=10&limit=50)

Generally speaking, the API is flexible enough to support both "look up a specific relay" as well as "have a vague idea / characteristics of relay(s)" searches. A narrowing-down type of search/browse is intended and supported use.

## ExoneraTor-type relay participation lookup

 * [see if a particular IPv4 address is currently participating as a relay in the network](http://ts.mkj.lt:5555/details?search=128.31.0.34&running=true)

 * [see what kinds of relays are currently running in the 128.0.0.0/8 CIDR block](http://ts.mkj.lt:5555/details?search=128.&running=true)

 * [querying for running relays is supported for all the above search parameters, too](http://ts.mkj.lt:5555/details?search=moria1&running=true)

 * note one of the earlier queries: it is possible to see if a [particular IP address has ever been participant in the relay network](http://ts.mkj.lt:5555/details?search=79.98.25.182)

## Network statuses

One can look up a specific relay to see a list of consensuses that it has been present in (i.e., a list of network statuses for that relay), as well as the IP addresses and nicknames at the time of that consensus.

 * [look up a summary of some relay](http://ts.mkj.lt:5555/statuses?lookup=9695DFC35FFEB861329B9F1AB04C46397020CE31&condensed=true) - if it is stable enough, the summary shouldn not be long

 * [on the other hand, more troublesome relays will have a different pattern of network statuses](http://ts.mkj.lt:5555/statuses?lookup=4B35EA75FD72A0115451F69200ABDB3CF96A8087)

 * [browse through the result set using offset](http://ts.mkj.lt:5555/statuses?lookup=F397038ADC51336135E7B80BD99CA3844360292B&condensed=true&offset=500)

 * [use date range parameters as before to narrow down results we are interested in](http://ts.mkj.lt:5555/statuses?lookup=F397038ADC51336135E7B80BD99CA3844360292B&condensed=true&from=2013-09&to=2013-09-22)

 * [browse through the full result set form](http://ts.mkj.lt:5555/statuses?lookup=F397038ADC51336135E7B80BD99CA3844360292B)
