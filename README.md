# nyaarss.py
============

    python nyaarss.py [-l] [configfile]

actions performed
------------------
1. reads the rss feed from nyaa.eu (currently hardoced to "http://www.nyaa.se/?page=rss&cats=1_37&filter=2")
2. reads list of regexes from regex_list (nyaarss.config)
3. tries to match the titles in the rss with the regexes. script stops here if '-l' is used. output:
  * OLD: .torrent file already exists in done_dir
  * DOUBLE: .torrent file already exists in torrent_dir
  * NEW: .torrent file marked for download
4. downloads all NEW .torrent files to the torrent_dir (nyaarss.config)
5. [optionally wait for a specific process to stop existing (unix only)]
6. move the earliest created .torrent in the torrent_dir to the done_dir (nyaarss.config)
7. execute the torrent_command (nyaarss.config) with %f replaced by the moved .torrent file path

usage example
-------------
you're following a specific series that is posted as "[some_group] some name - some episode number[1080p].mkv".

add a line to regex_list looking like this:
    
    \[some_group\].*some\sname.*[0-9]*.*\[1080p]
    
(I'm not going to explain regexes here, use google)

create or modify the config file:
    
    torrent_dir = path to some folder
    done_dir = path to some other folder
    regex_file = ./regex_list
    # command to execute to download a torrent:
    torrent_command = transmission-cli %f

next just run

    python nyaarss.py your_config_file
    
and a torrent matching the regex will be downloaded (if any exists in the rss feed).

The script executes the torrent_command only once (with one file) but the torrent_dir is
filled with all matches from the feed. The script is intended to be run regularly, dowloading
only one torrent per run.

The done_dir is used to prevent double downloads


