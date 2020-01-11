# osu-playlist
Extract all osu songs, collection,run a regex search in .osu tag line.Export audio to directory or create m3u8 playlist.
# Usage 
Put this file in your osu!/Songs folder
## Commands
* `python3 osu_playlist.py` to export all songs as .m3u8 playlist
 
* `python3 osu_playlist.py --collection "name of collection"` to export collection. Name might be case insensitive or with mistakes.

* `python3 osu_playlist.py --regtag "regex"` run a regex search on tags provided from .osu file e.g: this "(azer|drumstep)" will match all songs which contain azer or drumstep, lowercase.
* `python3 osu_playlist.py --to_dir "path"` provide path to export audio(optional)


Example  with [mpv](https://mpv.io/):
  `mpv --playlist=playlist.m3u8 --shuffle --volume 35` 
  
 
# How can I help?

1. Open issues on things that are broken
2. Fix open issues by sending PRs
3. Add documentation

# Pull requests
Pull requests regarding things which aren't directly related to the program will not be merged.
For example, pull requests related to README.md will not be merged, you can open an issue instead.