# ipv - IP Vanish Connection Utility

Downloads and ranks .ovpn files that are necessary for connection 
to IP Vanish servers and provides an interface for connecting to 
the fastest one.

This only ranks by ping response time.  Server load would be nice 
at one point, but the way IP Vanish chooses to make that 
information available makes it more complicated than it is worth 
at this point.

### Quickstart

If needed get a list of sites

`ipv -l`

Download .ovpn files for site

`ipv -d <site>`

Rank the servers

`ipv -r`

Connect to the fastest server

`ipv` or `ipv --s 1`


### Options

#### Download
`-d <site>`

`--download <site>`

This will download all .ovpn files from the IP Vanish website for 
the specified site*

If files already exist for the site, only files not currently in 
the directory will be downloaded

\* site refers to the city or area to download files for.

#### Update
`-u`

`--update`

Fetches new .ovpn files from the IP Vanish website for all 
the sites you currently have downloaded.

Essentially it just determines all the sites you have files for 
and runns --download with them

#### Remove
`-rm <site>`

`--remove <site>`

Removes all .ovpn files for the specified site

#### Rank Servers
`-r`

`--rank-servers`

Pulls the url from all the .ovpn files that have been downloaded, 
pings them 5 times, averages the results, and then creates a list 
sorting them by the fastest average response time

#### Server
`-s <rank>`

`--server <rank>`
Connects to the server at the specified rank.  Running ipv with no 
arguments is the same as running `-s 1`.

The option to select a server that isn't ranked #1 is especially 
necessary since server load is not part of the ranking.