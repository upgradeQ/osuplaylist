# osu-playlist
Extract all osu songs, collection,run a regex search in .osu tag line.Export audio to directory or create m3u8 playlist.
# Russian 🇷🇺 [README](ReadmeRU.md)
# Usage 
Put this file in your osu!/Songs folder
## Commands
### export all songs as .m3u8 playlist, may take a while
  `python3 osu_playlist.py`
### export collection. Name might be case insensitive or with typos 
 `python3 osu_playlist.py --collection "name of collection"` 
### run a regex search on tags provided from .osu file 
`python3 osu_playlist.py --regtag "regex"`
### run an inversed regex search on tags (optional)
  `python3 osu_playlist.py -r "regex" -i ` 
###  provide path to export audio.(optional) if used without arg - all songs
  `python3 osu_playlist.py --to_dir "path"`
### info
 `python3 osu_playlist.py --help` 

## Example  with [mpv](https://mpv.io/):
  `mpv --playlist=playlist.m3u8 --shuffle --volume 35` 
## Example regex search + inverse + to directory:
 `python3 osu_playlist.py -r "(azer|step)" -i -d "E:/music/osu_playlist"`

`-r "(azer|step)"` will match all songs which contain azer or step

`-i` (optional) return an inverted result , all songs which NOT contain azer or step

`-d` (optional) export .mp3 to directory E:/music/osu_playlist

# Using osu_playlist.py as a library
```python
import osu_playlist
from osu_playlist import osudict, names, namedict

print(len(names))
# this will filter taglines matching azer or step 
first_search = osu_playlist.filter_tags(osudict, regtag="(azer|step") 
print(first_search)
# this will filter taglines from first_search matching drumstep 
second_search = osu_playlist.filter_tags(
    osudict, regtag="drumstep", list_of_song_names=first_search
)
print(second_search)
# export to dir
osu_playlist.export_to_dir(second_search)
```

# Pull requests
Pull requests regarding things which aren't directly related to the program will not be merged.
For example, pull requests related to README.md will not be merged, you can open an issue instead.