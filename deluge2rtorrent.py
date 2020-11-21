#!/usr/bin/python2
# Tool to Transfer torrents from deluge to rtorrent given criteria
# Pull a maximum number of torrents that either are a ratio of x or have been seeding y days
#
# deluge2rtorrent.py --ratio x --days y --max z --Watch watchfolder --Label
#

import os
import sys
import argparse
import logging

from deluge_client import LocalDelugeRPCClient

from pyrobase import bencode
from pyrocore.util import os, metafile

LOGFILE='/tmp/D2R.log'


parser = argparse.ArgumentParser()

# To run as cron job without parameters, change defaults 
# Current defaults: Torrent either has a ratio of 2.99+ or has been seeding for 5 days for up to 100 torrents

parser.add_argument (
    '-r', '--ratio',
    required=False,
    type=float,
    default=3.0, 
    dest="ratio",
    metavar="<torrent ratio>",
    help="Minimum Ratio of Torrent to Select"
)

parser.add_argument(
    '-d', '--days',
    required=False,
    type=int,
    default=5, 
    dest="days",
    metavar="<number of days>",
    help="Number of Days Seeding Required to Select"
)

parser.add_argument(
    '-m', '--max',
    required=False,
    type=int,
    default=100,
    dest="max",
    metavar="<maximum torrents>",
    help="Maximum Number of Torrents to Select"
)

parser.add_argument(
    '-W', '--Watch',
    required=False,
    type=str,
    default='watch',
    dest="watchFolder",
    metavar="<watch folder base>",
    help="Receiving Watch Folder"
)

parser.add_argument(
    '-L', '--Label',
    action='store_true',
    required=False,
    default=False,
    dest="label",
    help="Use Label as Watch Folder Subdirectory"
)


args = parser.parse_args()

home = os.path.expanduser("~")
delugeBasePath = home + "/.config/deluge/state/"
watchFolder = os.path.join( home, args.watchFolder)

max_seconds = args.days * 60 * 60 * 24

D2Rlog = logging.getLogger('Deluge2Rtorrent')

handler = logging.FileHandler( LOGFILE )
layout = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(layout)

D2Rlog.setLevel(logging.INFO)
D2Rlog.addHandler(handler) 

D2Rlog.info("Run Started: " + str(sys.argv[0:]) )

client = LocalDelugeRPCClient()

client.connect()

if client.connected:
    
#   Get all torrents from Deluge
    torrentList = client.core.get_torrents_status({ "is_seed": [True] },['ratio','seeding_time', 'save_path', 'label', 'name'])
    
    D2Rlog.info( "Fetched "+str(len(torrentList))+" Seeding Torrents" )

    torrent_index = 0

#   Step through them
    D2Rlog.info( "Moving a max of "+str(args.max)+" torrents with a ratio >= "+str(args.ratio)+" or has been seeding for >= "+str( max_seconds )+" seconds." )
    for torrent,details in torrentList.items():

        ratio = float(details["ratio"])
        seeding_time = int(details["seeding_time"])

#       Match our criteria?
        if ratio >= args.ratio or seeding_time >= max_seconds:

            D2Rlog.info( "[ "+str(torrent_index +1)+" ] "+" Selected <"+ details['name'] + "> Ratio: "+str(ratio)+" Seed Time: "+str(seeding_time ) )

            delugeTorrent = os.path.join( delugeBasePath, torrent + ".torrent" )

#           Read Torrent
            metainfo = bencode.bread( delugeTorrent )

            payloadPath = os.path.join( details["save_path"], metainfo["info"]["name"] )

#           Add RTorrent Fast Resume
            rTorrent = metafile.add_fast_resume(metainfo, payloadPath)


#           Determine where to save the new torrent
            destination = watchFolder

            if args.label :
                labeled = os.path.join( watchFolder, details[ "label" ] )

#               Label Folder must exist, otherwise add torrent to base watch folder (no label)
                if  os.path.exists( labeled ):
                    destination = labeled

            torrentFile = os.path.join( destination, torrent + ".torrent" )

#           Write out rtorrent torrent to watch folder destination
            try:
                bencode.bwrite(torrentFile, rTorrent)

            except Exception as writeFailed:
                D2Rlog.warn( "Write of New Torrent Failed: %s" + writeFailed[1] )
                pass
            else:
                D2Rlog.info( "Wrote Fast Resume Torrent to: " + torrentFile )

#           Remove torrent from Deluge
            try:
                client.core.remove_torrent( torrent, False )
            except Exception as removeFailed:
                D2Rlog.warn( "Remove of Deluge Torrent Failed: %s" + removeFailed[1] )
            else:
                D2Rlog.info( "Removed torrent from Deluge." )

            torrent_index += 1

#           If reached maximum for run
            if torrent_index == args.max:
                break;

        
        exit_value = 0
else:
    D2Rlog.warn( "Failed to Connect, Deluged Running?" )
    exit_value = -1


D2Rlog.info("Run Complete, Exit Value: "+str(exit_value))
sys.exit(exit_value)

