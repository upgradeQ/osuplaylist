import argparse
import configparser
import difflib
import struct
import re
import hashlib
import time
from string import Template
from uuid import uuid1
from datetime import datetime
from shutil import copy
from pathlib import Path
from collections.abc import MutableMapping, Mapping
from collections import OrderedDict
from itertools import groupby

cli_path = Path(__file__).absolute()
ini = "osu_playlist_config.ini"
cfg_path = cli_path.parent / ini
config = configparser.ConfigParser()
if not cfg_path.exists():
    config["osu_songs"] = {}
    full_path = input('Enter full osu/songs path: ')
    config["osu_songs"]["path"] = full_path
    with open(cfg_path, "w") as cfg:
        config.write(cfg)
config.read(cfg_path)

p = Path(config["osu_songs"]["path"])
# /songs path
collection_db = p.absolute().parent / "collection.db"

text = "bugs/suggestions ? github.com/hqupgradehq/osuplaylist"
parser = argparse.ArgumentParser(description=text)
# https://stackoverflow.com/questions/18157376/handle-spaces-in-argparse-input
parser.add_argument(
    "--collection",
    "-c",
    action="store",
    dest="collection_name",
    help="export collection as playlist.m3u8",
)
parser.add_argument(
    "--import_mp3",
    "-m",
    action="store",
    dest="path_to_mp3s",
    help="provide path where mp3s are,search them in-game mp3 osu will index it",
)
parser.add_argument(
    "--nameit", "-n", action="store", dest="name_it", help="provide name ascii"
)
parser.add_argument(
    "--reg_tag",
    "-r",
    action="store",
    dest="reg_tag",
    help="export all songs with regular expression applied to tag string lowercase",
)
parser.add_argument(
    "--date_range",
    "-t",
    action="store",
    dest="date_range",
    help="apply daterange, daterange format:Year.month.day example: >2020.1.1 larger than, 2020.1.1:2020.1.24 in this range",
)
parser.add_argument(
    "--to_dir", "-d", action="store", dest="to_dir", help="provide output path"
)

parser.add_argument(
    "--update_db",
    "-g",
    action="store",
    dest="db_col_name",
    help="provide collection name",
)
parser.add_argument(
    "--inverse", "-i", action="store_true", dest="inverse", help="inverse regex search"
)
parser.add_argument(
    "--loopify", "-l", action="store_true", dest="loops", help="create loops "
)
args = parser.parse_args()
osu_file_format = Template(
    """\
osu file format v14

[General]
AudioFilename: $an
AudioLeadIn: 0
PreviewTime: -1
Countdown: 0
SampleSet: Soft
StackLeniency: 0.7
Mode: 0
LetterboxInBreaks: 0
WidescreenStoryboard: 0

[Editor]
DistanceSpacing: 1.4
BeatDivisor: 4
GridSize: 4
TimelineZoom: 1

[Metadata]
Title:$title
TitleUnicode:$title
Artist:OP
ArtistUnicode:OP
Creator:osu_playlist
Version:zero
Source:
Tags:$bn
BeatmapID:0
BeatmapSetID:-1

[Difficulty]
HPDrainRate:7
CircleSize:5
OverallDifficulty:7
ApproachRate:9
SliderMultiplier:1.4
SliderTickRate:1

[Events]
//Background and Video events
0,0,"bg.png",0,0
//Break Periods
//Storyboard Layer 0 (Background)
//Storyboard Layer 1 (Fail)
//Storyboard Layer 2 (Pass)
//Storyboard Layer 3 (Foreground)
//Storyboard Layer 4 (Overlay)
//Storyboard Sound Samples

[TimingPoints]
4852.88555273078,315.789473684211,4,2,0,40,1,0
25852,300,4,2,0,40,1,0
42502,315.789473684211,4,2,0,40,1,0


[HitObjects]
256,192,905,12,0,1234,0:0:0:0:"""
)


def get_songs():

    songdirs = []
    for song_dir in p.iterdir():
        # is it osu beatmap?
        if str(song_dir.name).split()[0].isdigit():
            # check if there is osu file in directory, this might happen if you deleted all song difs
            if list(song_dir.glob("*.osu")):
                songdirs.append(str(song_dir.name))

    paths = [p.joinpath(i) for i in songdirs]
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
    osudict = {}
    for pos, i in enumerate(songdirs):
        temp = i
        if i.endswith("[no video]"):
            temp = temp[:-10]
        temp = " ".join(temp.split()[1:])
        names.append(temp)
        namedict[temp] = audios[pos]
        osudict[temp] = osufiles[pos]
    result = (sorted(list(set(names))), namedict, osudict)
    return result


class CaseInsensitiveDict(MutableMapping):
    """A case-insensitive ``dict``-like object.
    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.
    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::
        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True
    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.
    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def generate_hashes(osudict):
    md5s = {}
    for i in osudict:
        md5s[i] = [md5(j) for j in osudict[i]]
    return md5s


def nextint(f):
    return struct.unpack("<I", f.read(4))[0]


def nextstr(f):
    if f.read(1) == 0x00:
        return
    len = 0
    shift = 0
    while True:
        byte = ord(f.read(1))
        len |= (byte & 0b01111111) << shift
        if (byte & 0b10000000) == 0:
            break
        shift += 7
    return f.read(len).decode("utf-8")


def get_collections():
    col = {}
    f = open(collection_db, "rb")
    version = nextint(f)
    ncol = nextint(f)
    for i in range(ncol):
        colname = nextstr(f)
        col[colname] = []
        for j in range(nextint(f)):
            f.read(2)
            col[colname].append(f.read(32).decode("utf-8"))
    f.close()
    return (col, version)


# db write  https://github.com/LoPij/osu-collection-manager/blob/84c1d7dd0136183fad8b46b5e8bf703e81b50c15/osuCollectionManager.py#L148
def write_int(file, integer):
    int_b = integer.to_bytes(4, "little")
    file.write(int_b)


def get_uleb128(integer):
    result = 0
    shift = 0
    while True:
        byte = integer

        result |= (byte & 0x7F) << shift
        # Detect last byte:
        if byte & 0x80 == 0:
            break
        shift += 7
    return result.to_bytes(1, "little")


def write_string(file, string):
    if not string:
        # If the string is empty, the string consists of just this byte
        return bytes([0x00])
    else:
        # Else, it starts with 0x0b
        result = bytes([0x0B])

        # Followed by the length of the string as an ULEB128
        result += get_uleb128(len(string))

        # Followed by the string in UTF-8
        result += string.encode("utf-8")
        file.write(result)


def update_collection(list_of_song_names, name, osudict=None):
    backup_db = collection_db.parents[0] / "OPLbackup_collection.db"
    # read version ,count
    collection_dict, version = get_collections()
    # copy as backup.db , osu client on launch will create .bak also
    if not backup_db.exists():
        copy(collection_db, backup_db)
    md5s = generate_hashes(osudict)
    hashes = []
    for h in list_of_song_names:
        for difficultly_hash in md5s[h]:
            hashes.append(difficultly_hash)
    timestamp = str(int(time.time()))
    name = name + " " + timestamp
    collection_dict[name] = hashes
    with open(collection_db, "wb") as f:
        # write version int , count int
        write_int(f, version)
        write_int(f, len(collection_dict))
        # for each collection including generated
        for col_name, col_hashes in collection_dict.items():
            # write its name string,maps count len(),write hashes md5s
            write_string(f, col_name)
            write_int(f, len(col_hashes))
            for h in col_hashes:
                write_string(f, h)
    print("Export to db complete,quantity: ", len(list_of_song_names))


def import_songs_as_collection(path_with_mp3s, collection_name):
    # hit F5 in song menu in oss

    mp3s = [mp3_path for mp3_path in Path(path_with_mp3s).glob("*.mp3")]

    def create_fake_osu_beatmaps(mp3s):
        list_of_song_names = list()
        osudict = dict()
        for mp3 in mp3s:
            # uuid for unic hash when using update_collection and for unic name in osu/songs
            bn = str(uuid1())
            # create directory
            bp = Path(f"beatmap-{bn}")
            bp.mkdir()
            # move  audio to beatmap path
            copy(str(mp3), str(bp))
            # move bg
            copy("bg.png", str(bp))
            # create simple .osu
            title = mp3.name
            # doesnt works with unicode , so then check is it asii or not https://stackoverflow.com/a/18403812
            isascii = lambda s: len(s) == len(s.encode())
            if not isascii(title):
                title = bn
            fake_dot_osu = f"OP - {title} (osu_playlist) [zero].osu"
            bp_osu = bp / fake_dot_osu

            with bp_osu.open("w", encoding="utf-8") as f:
                f.write(osu_file_format.substitute(an=mp3.name, title=title, bn=bn))

            list_of_song_names.append(title)
            osudict[title] = [bp_osu]
        return list_of_song_names, osudict

    list_of_song_names, osudict = create_fake_osu_beatmaps(mp3s)
    update_collection(list_of_song_names, collection_name, osudict=osudict)


def collection_content(collection_name):
    name = difflib.get_close_matches(
        collection_name.lower(), [c.lower() for c in collections.keys()]
    )
    # https://github.com/psf/requests/blob/master/requests/structures.py
    cid = CaseInsensitiveDict(data=collections)
    result = list()
    for sn in names:
        try:
            for hash in md5s[sn]:
                if hash in cid[name[0]]:
                    result.append(sn)
                    break
        except KeyError:
            pass
    return result


def filter_tags(osudict=None, regtag=None, inverse=False, list_of_song_names=None):
    """apply regex to tag line of all songs or to a list_of_song_names"""
    regtag = regtag.lower()  # ignore case
    regex = re.compile(regtag)

    def group_tags(sn_with_tags):
        groups = dict()
        f = lambda x: bool(regex.search(x[1]))
        for sn, t in groupby(sn_with_tags, key=f):
            _group = list(t)
            if sn in groups:
                groups[sn] += _group
            else:
                groups[sn] = _group

        return groups

    if list_of_song_names:
        # update osudict
        osudict = {sn: osudict[sn] for sn in list_of_song_names}
    sn_tags = list()
    for song_name, dot_osu in osudict.items():
        with open(dot_osu[0], "r", encoding="utf8") as f:
            for line in f.readlines():
                if line.startswith("Tags"):
                    tag_line = line.partition(":")[2].strip()
                    sn_tags.append([song_name, tag_line.lower()])
                    break
    _tags = group_tags(sn_tags)
    try:
        sn_list = [r[0] for r in _tags[bool(not inverse)]]
        return sn_list
    except KeyError:
        print("Not found")
        return []


def create_playlist(list_of_song_names):
    with open("playlist.m3u8", "w", encoding="utf8") as playlist:
        playlist.write("#EXTM3U" + "\n")
        for sn in list_of_song_names:
            song_name = "#EXTINF:-1," + sn + "\n"
            playlist.write(song_name)
            song_path = str(namedict[sn].resolve()) + "\n"
            playlist.write(song_path)
    print("Playlist created,available songs:", len(list_of_song_names))


def export_to_dir(list_of_song_names, to_dir="osu_playlist_output"):
    to_dir = Path(str(to_dir))
    if not to_dir.exists():
        to_dir.mkdir()
    for sn in list_of_song_names:
        from_dir = str(namedict[sn])
        end_dir = str(to_dir / sn) + str(namedict[sn].suffix)
        copy(from_dir, end_dir)
    print("Songs export complete,quantity: ", len(list_of_song_names))


def apply_daterange(list_of_song_names, daterange=None):
    def get_date(datestring):
        format = "%Y.%m.%d"
        date = datetime.strptime(datestring, format)
        return date

    sn_date = dict()
    for sn in list_of_song_names:
        # creation date of file https://stackoverflow.com/a/52858040
        sn_date[sn] = datetime.fromtimestamp(namedict[sn].stat().st_ctime)

    def parse(daterange):
        list_of_song_names = list()
        if ">" in daterange:
            datestring = daterange.replace(">", "")
            date = get_date(datestring)
            for sn, dt in sn_date.items():
                if dt > date:
                    list_of_song_names.append(sn)
            return list_of_song_names
        if "<" in daterange:
            datestring = daterange.replace("<", "")
            date = get_date(datestring)
            for sn, dt in sn_date.items():
                if dt < date:
                    list_of_song_names.append(sn)
            return list_of_song_names
        if ":" in daterange:
            date_start, date_end = daterange.split(":")
            date_start, date_end = get_date(date_start), get_date(date_end)
            for sn, dt in sn_date.items():
                if date_start <= dt <= date_end:
                    list_of_song_names.append(sn)
            return list_of_song_names

    sn_list = parse(daterange)
    return sn_list


def create_loops(list_of_song_names, osudict):
    for song in list_of_song_names:
        update_collection([song], song + " LOOP", osudict=osudict)


names, namedict, osudict = get_songs()

def main(names=names,namedict=namedict,osudict=osudict):
    """main logic of the program,takes those parameters because of closure"""

    col_name = args.collection_name
    regtag = args.reg_tag
    to_dir = args.to_dir
    inverse = args.inverse
    to_game = args.db_col_name
    daterange = args.date_range
    name = args.name_it
    path_to_mp3s = args.path_to_mp3s
    loops = args.loops
    if col_name:
        md5s = generate_hashes(osudict)
        collections, _version = get_collections()
        col_list = collection_content(col_name)
        if to_dir:
            export_to_dir(col_list, to_dir)
        elif loops:
            create_loops(col_list, osudict)
        else:
            create_playlist(col_list)
    elif path_to_mp3s:
        import_songs_as_collection(path_to_mp3s, name)
    elif regtag:
        tag_list = filter_tags(osudict, regtag, inverse)
        if daterange:
            tag_list = apply_daterange(tag_list, daterange)
        elif to_dir:
            export_to_dir(tag_list, to_dir)
        elif loops:
            create_loops(tag_list, osudict)
        elif to_game:
            update_collection(tag_list, name=to_game, osudict=osudict)
        else:
            create_playlist(tag_list)
    else:
        if daterange:
            names = apply_daterange(names, daterange)
        if to_dir:
            export_to_dir(names, to_dir)
        # without args
        else:
            create_playlist(names)
if __name__ == "__main__":
    main()
