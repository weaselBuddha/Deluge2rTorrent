# Deluge2rTorrent

Tool to Transfer torrents from deluge to rtorrent given criteria

Pull a maximum number of torrents that either are a ratio of x or have been seeding y days

Usage ./deluge2rtorrent.py --ratio x --days y --max z --Watch watchfolder --Label

Requires John Doee's Simple Deluge client (https://github.com/JohnDoee/deluge-client) for talking to deluge

pip install deluge-client

And pyroscopes pyrocore to create fast resume rtorrent torrent

pip install pyrocore


