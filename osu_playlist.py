##### PUT THIS FILE IN OSU/SONGS FOLDER #####
ABSPATH_TO_SONGS = "."
import os
from pathlib import Path
import argparse

text = "https://mpv.io/manual/stable/#keyboard-control"
parser = argparse.ArgumentParser(description=text)
parser.parse_args()


def get_songs():
    cur = ABSPATH_TO_SONGS
    songdirs = [i for i in [j for j in os.walk(cur)][0][1] if i.split()[0].isdigit()]
    # fix empty difficulties
    songdirs = [i for i in songdirs if list(Path(i).glob("*.osu"))]
    paths = [os.path.join(cur, i) for i in songdirs]
    audios = []
    osufiles = []
    for i in paths:
        osufile = [i for i in Path(i).glob("*.osu")]
        osufiles.append(osufile)
        with open(osufile[0], "r", encoding="utf8") as f:
            for line in f.readlines():
                if line.startswith("AudioFilename"):
                    audio_filename = line[line.index(":") + 2 :].strip()
                    break
        audios.append(Path(i, audio_filename))
    names = []
    namedict = {}
    for pos, i in enumerate(songdirs):
        temp = i
        if i.endswith("[no video]"):
            temp = temp[:-10]
        temp = " ".join(temp.split()[1:])
        names.append(temp)
        namedict[temp] = audios[pos]
    return (sorted(list(set(names))), namedict)


names, namedict = get_songs()
with open("playlist.m3u8", "w", encoding="utf8") as playlist:
    playlist.write("#EXTM3U" + "\n")
    for sn, _ in namedict.items():
        song_name = "#EXTINF:-1," + sn + "\n"
        playlist.write(song_name)
        song_path = str(namedict[sn].resolve()) + "\n"
        playlist.write(song_path)
print("Playlist created,available songs:", len(names))
# os.system("mpv --playlist=playlist.m3u8 --shuffle --volume 35")
