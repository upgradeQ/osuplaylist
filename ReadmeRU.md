# osu-playlist
Извлекает все осу треки, коллекции, регулярные выражения по тегам из .osu файла. Экспорт треков в директорию или в отдельный m3u8 плейлист 
# Использование
Переместите этот файл в папку osu!/Songs 
## Команды
* `python3 osu_playlist.py` Экспорт треков в директорию или в отдельный m3u8 плейлист 
 
* `python3 osu_playlist.py --collection "название коллекции"` Экспорт коллекции.Может быть с опечатками или с верхним или нижним регистром 

* `python3 osu_playlist.py --regtag "regex"` регулярное выражине по тэгам с .osu files ,пример:  "(azer|drumstep)" будет соответствовать всем трекам которые содержат azer или drumpstep
* `python3 osu_playlist.py -r "regex" -i ` обратное регулярное выражение
* `python3 osu_playlist.py --to_dir "path"` указать путь для экспорта аудио (необязательно)
* more on commands `python3 osu_playlist.py --help` 

## Пример с  [mpv](https://mpv.io/):
  `mpv --playlist=playlist.m3u8 --shuffle --volume 35` 
  
 
# Использование osu_playlist.py как модуля
```python
import osu_playlist
from osu_playlist import osudict, names, namedict

print(len(names))
# это отфильтрует строки тегов, соответствующие azer или step 
first_search = osu_playlist.filter_tags(osudict, regtag="(azer|step") 
print(first_search)
# это отфильтрует строки тегов c first_search, соответствующие drumstep 
second_search = osu_playlist.filter_tags(
    osudict, regtag="drumstep", list_of_song_names=first_search
)
print(second_search)
# экспорт файлов мп3 
osu_playlist.export_to_dir(second_search)
```

# Pull requests
Pull requests относительно вещей прямо не связанных с программой не будут приняты 
Например, pull requests относительно README не будут приняты, вместо этого можете открыть issue
