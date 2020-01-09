# osu-playlist
Extract osu all songs or whole collection and create .m3u8 playlist.
# Usage 
Put this file in your osu!/Songs folder, run `python3 osu_playlist.py` to export all songs
 
_or_

 run `python3 osu_playlist.py --collection "name of collection"` to export collection. Name might be case insensitive or with mistakes.

_or_

run `python3 osu_playlist.py --tag tagname` to export all songs with one `tagname`. Name might be case insensitive.

Depending on choice playlist.m3u8 will be created; .m3u8 format can be used in various music players.

Example  with [mpv](https://mpv.io/):
  `mpv --playlist=playlist.m3u8 --shuffle --volume 35` 
  
 
# How can I help?

1. Open issues on things that are broken
2. Fix open issues by sending PRs
3. Add documentation

# Credits
Exctraction of paths and collections has taken from [osu-cplayer](https://github.com/eshrh/osu-cplayer)

Case insensitive structure has taken from [psf/requests
](https://github.com/psf/requests/blob/master/requests/structures.py)
