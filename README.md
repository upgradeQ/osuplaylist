# osu-playlist
Extract all osu songs, collection,run a regex search in .osu tag line.Export audio to directory or create m3u8 playlist.
# Russian 🇷🇺 [README](ReadmeRU.md)
# Usage 
Put this file in your osu!/Songs folder
## Commands
* `python3 osu_playlist.py` to export all songs as .m3u8 playlist
 
* `python3 osu_playlist.py --collection "name of collection"` to export collection. Name might be case insensitive or with mistakes.

* `python3 osu_playlist.py --regtag "regex"` run a regex search on tags provided from .osu file e.g: this "(azer|drumstep)" will match all songs which contain azer or drumstep, lowercase.
* `python3 osu_playlist.py -r "regex" -i ` run an inversed regex search on tags
* `python3 osu_playlist.py --to_dir "path"` provide path to export audio(optional)
* more on commands `python3 osu_playlist.py --help` 

## Example  with [mpv](https://mpv.io/):
  `mpv --playlist=playlist.m3u8 --shuffle --volume 35` 
  
 
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