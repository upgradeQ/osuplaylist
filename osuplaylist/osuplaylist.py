import argparse
import configparser
import re
from struct import unpack
from difflib import get_close_matches
from time import time
from string import Template
from uuid import uuid1
from datetime import datetime, timedelta
from shutil import copy
from pathlib import Path
from collections.abc import MutableMapping, Mapping
from collections import OrderedDict, Counter, defaultdict
from itertools import groupby

cli_path = Path(__file__).absolute()
ini = "osu_playlist_config.ini"
cfg_path = cli_path.parent / ini
config = configparser.ConfigParser()
if not cfg_path.exists():
    config["osu_songs"] = {}
    full_path = input("Enter full osu/songs path: ")
    config["osu_songs"]["path"] = full_path
    with open(cfg_path, "w") as cfg:
        config.write(cfg)
config.read(cfg_path)

p = Path(config["osu_songs"]["path"])
# /songs path
collection_db = p.absolute().parent / "collection.db"
osu_db = p.absolute().parent / "osu!.db"

text = "bugs/suggestions ? github.com/upgradeq/osuplaylist"
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
    "--steam", "-s", action="store_true", dest="to_steam", help="export  to steam"
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


def nextint(f):
    return unpack("<I", f.read(4))[0]


def read_ubyte(f):
    return unpack("<B", f.read(1))[0]


def nextstr(f):
    """ https://github.com/jaasonw/osu-db-tools/blob/9bdd51f60d0f3d1a1541f3f91637f5979cda61b9/buffer.py#L39
    For the 's' format character, the count is interpreted as the length
    of the bytes, not a repeat count like for the other format characters; 
    https://docs.python.org/3/library/struct.html
    """
    strlen = 0
    strflag = read_ubyte(f)
    if strflag == 0x0B:
        strlen = 0
        shift = 0
        # uleb128
        # https://en.wikipedia.org/wiki/LEB128
        while True:
            byte = read_ubyte(f)
            strlen |= (byte & 0x7F) << shift
            if (byte & (1 << 7)) == 0:
                break
            shift += 7

    return (unpack("<" + str(strlen) + "s", f.read(strlen))[0]).decode("utf-8")


def nextlong(f):
    return unpack("<Q", f.read(8))[0]


offsets = {
    "byte": 1,
    "short": 2,
    "int": 4,
    "long": 8,
    "single": 4,
    "double": 8,
    "bool": 1,
    "datetime": 8,
}


def skip(_f, offset):
    return _f.read(offset)


def read_double_pair(_f):
    i = nextint(_f)
    for _ in range(i):
        skip(_f, offsets["byte"])
        skip(_f, offsets["int"])
        skip(_f, offsets["byte"])
        skip(_f, offsets["double"])


def read_timings(_f):
    i = nextint(_f)
    for _ in range(i):
        skip(_f, offsets["double"])
        skip(_f, offsets["double"])
        skip(_f, offsets["bool"])


def read_beatmap_song(f, version):
    """https://osu.ppy.sh/help/wiki/osu!_File_Formats/Db_(file_format) """

    if version <= 20191106:
        skip(f, offsets["int"])
    else:
        pass

    artist = nextstr(f)  # artist
    nextstr(f)  # unicode
    title = nextstr(f)  # song
    nextstr(f)  #  unicode
    nextstr(f)  # mapper
    nextstr(f)  # diff
    audio_file = nextstr(f)  # audio
    md5_hash = nextstr(f)
    osu_file = nextstr(f)  # .osu
    skip(f, offsets["byte"])  # ranked
    skip(f, offsets["short"])  # ...
    skip(f, offsets["short"])  # ...
    skip(f, offsets["short"])  # spinner
    skip(f, offsets["long"])  # modif
    skip(f, offsets["single"])  # ar
    skip(f, offsets["single"])  # cs
    skip(f, offsets["single"])  # hp
    skip(f, offsets["single"])  # od
    skip(f, offsets["double"])  # slider
    read_double_pair(f)
    read_double_pair(f)
    read_double_pair(f)
    read_double_pair(f)
    skip(f, offsets["int"])  # drain
    skip(f, offsets["int"])  # total
    skip(f, offsets["int"])  # start
    read_timings(f)
    skip(f, offsets["int"])
    set_id = nextint(f)  # set id
    skip(f, offsets["int"])  # thread
    skip(f, offsets["byte"])
    skip(f, offsets["byte"])
    skip(f, offsets["byte"])
    skip(f, offsets["byte"])  # mania
    skip(f, offsets["short"])
    skip(f, offsets["single"])
    skip(f, offsets["byte"])  # game mode
    nextstr(f)  # song source
    tags = nextstr(f)  # song tags
    skip(f, offsets["short"])
    nextstr(f)  # font
    skip(f, offsets["bool"])
    last_time_played = nextlong(f)
    skip(f, offsets["bool"])
    folder_name = nextstr(f)  # folder
    skip(f, offsets["long"])
    skip(f, offsets["bool"])  # sound
    skip(f, offsets["bool"])
    skip(f, offsets["bool"])
    skip(f, offsets["bool"])
    skip(f, offsets["bool"])  # visual
    skip(f, offsets["int"])
    skip(f, offsets["byte"])
    return {
        "artist": artist,
        "title": title,
        "set_id": set_id,
        "folder_name": folder_name,
        "audio_file": audio_file,
        "osu_file": osu_file,
        "tags": tags,
        "md5_hash": md5_hash,
        "last_time_played": last_time_played,
    }


def get_songs():
    f = open(osu_db, "rb")
    version = nextint(f)
    skip(f, offsets["int"])  # folder
    skip(f, offsets["bool"])  # acc
    skip(f, offsets["datetime"])  # dt
    nextstr(f)  # nick
    beatmap_number = nextint(f)

    beatmaps = list()
    for _ in range(beatmap_number):
        beatmaps.append(read_beatmap_song(f, version))

    names = list()
    tagdict = dict()
    osudict = defaultdict(list)
    hashdict = defaultdict(list)
    namedict = dict()
    datedict = dict()

    for i in beatmaps:
        # create pathlib objects
        audio = p / i["folder_name"] / i["audio_file"]
        name = i["artist"] + " - " + i["title"]
        names.append(name)
        tagdict[name] = i["tags"]
        namedict[name] = audio
        osudict[name].append(p / i["folder_name"] / i["osu_file"])
        hashdict[name].append(i["md5_hash"])
        datedict[i["md5_hash"]] = i["last_time_played"]

    return (list(set(names)), namedict, osudict, tagdict, hashdict, datedict)


def get_collections():
    """read .db file, return raw collection"""
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


def get_recent(hashdict, datedict, osudict):
    """read osu.db file, return songs
     sorted by last set score"""

    def convert_dotnet_tick(ticks):
        # source https://gist.github.com/gamesbook/03d030b7b79370fb6b2a67163a8ac3b5
        """Convert .NET ticks to datetime object
        Args:
            ticks: integer
                i.e 100 nanosecond increments since 1/1/1 AD"""
        _date = datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)
        return _date

    # {hash:date,...}
    dt_sn = dict()
    for md5hash, longtick in datedict.items():
        dt_object = convert_dotnet_tick(longtick)
        dt_sn[md5hash] = dt_object

    # {songname : [hash,date],...}
    sn_dates = dict()

    hashdict = {sn: hashes for sn, hashes in hashdict.items() if sn in osudict}

    for sn, hashes in hashdict.items():
        try:
            song_hashes_date = []
            for h in hashes:
                song_hashes_date.append([h, dt_sn[h]])
            most_recent = max(song_hashes_date, key=lambda i: i[1])
            sn_dates[sn] = most_recent
        except KeyError:
            continue

    songs_by_date = {  # {sn:date}
        k: v[1] for k, v in sorted(sn_dates.items(), key=lambda i: i[1][1])
    }
    return songs_by_date


# db write  https://github.com/osufiles/osuCollectionManager-backup
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


def update_collection(list_of_song_names, name, osudict=None, hashdict=None):
    """manually add beatmaps to .db file"""
    backup_db = collection_db.parents[0] / "OPLbackup_collection.db"
    # read version ,count
    collection_dict, version = get_collections()
    # copy as backup.db , osu client on launch will create .bak also
    if not backup_db.exists():
        copy(collection_db, backup_db)
    md5s = hashdict
    hashes = []
    for h in list_of_song_names:
        for difficultly_hash in md5s[h]:
            hashes.append(difficultly_hash)
    timestamp = str(int(time()))
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


def import_songs_as_collection(path_with_mp3s, collection_name,hashdict=None):
    """import mp3 files as fake beatmaps hit F5 in song menu in oss"""

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
    update_collection(list_of_song_names, collection_name, osudict=osudict,hashdict=hashdict)
    print('import mp3s to game collection complete')


def collection_content(collection_name, collections, md5s):
    """read collection name case insensitive with typos,return song list"""
    name = get_close_matches(
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


def filter_tags(
    osudict=None, regtag=None, inverse=False, list_of_song_names=None, tagdict=None
):
    """apply regex to tag line of all songs or to a list_of_song_names, return songlist"""
    regtag = regtag.lower()  # ignore case
    regex = re.compile(regtag)

    def group_tags(sn_with_tags):
        """create 2 groups with one mathching regex, and second not matching"""
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
        osudict = {sn: osudict[sn] for sn in list_of_song_names}
    sn_tags = list()
    for song_name, _ in osudict.items():
        tag_line = tagdict[song_name]
        sn_tags.append([song_name, tag_line.lower()])
    _tags = group_tags(sn_tags)
    try:
        sn_list = [r[0] for r in _tags[bool(not inverse)]]
        return sn_list
    except KeyError:
        print("Not found")
        return []


def create_playlist(list_of_song_names):
    if not list_of_song_names:
        print("list is empty")
        return
    with open("playlist.m3u8", "w", encoding="utf8") as playlist:
        playlist.write("#EXTM3U" + "\n")
        for sn in list_of_song_names:
            song_name = "#EXTINF:-1," + sn + "\n"
            playlist.write(song_name)
            song_path = str(namedict[sn].resolve()) + "\n"
            playlist.write(song_path)
    print("Playlist created[playlist.m3u8],available songs:", len(list_of_song_names))


def export_to_dir(list_of_song_names,namedict,to_dir="osu_playlist_output"):
    to_dir = Path(str(to_dir))
    if not to_dir.exists():
        to_dir.mkdir()
    for sn in list_of_song_names:
        from_dir = str(namedict[sn])
        end_dir = str(to_dir / sn) + str(namedict[sn].suffix)
        print("from",end_dir)
        try:
            copy(from_dir, end_dir)
        except:
            print('Failed to copy file')
    print("Songs export complete,quantity: ", len(list_of_song_names))


def apply_daterange(
    list_of_song_names, daterange=None, osudict=None, hashdict=None, datedict=None
):
    """ filter by last time played , return song list"""

    def get_date(datestring):
        format = "%Y.%m.%d"
        date = datetime.strptime(datestring, format)
        return date

    if list_of_song_names:
        osudict = {sn: osudict[sn] for sn in list_of_song_names}

    sn_date = get_recent(hashdict, datedict, osudict)

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


def export_m3u8_to_steam(list_of_song_names):
    """ export m3u8 playlist to steam
    this will overwrite queue.m3u8 if you have one
    source: https://steamcommunity.com/groups/steammusic/discussions/1/622954747299287987/
    overwrite queue.m3u8 while steam is closed
    --------------------------------
    Steam browser controls:
    steam://musicplayer/<command>
    Commands related to the Steam music player.
    play
    pause
    toggleplaypause
    playprevious
    playnext
    togglemute
    increasevolume
    decreasevolume
    toggleplayingrepeatstatus
    toggleplayingshuffled   
    source: https://developer.valvesoftware.com/wiki/Steam_browser_protocol"""
    if not list_of_song_names:
        print("list is empty")
        return
    try:
        full_steam_database_path = config["osu_songs"]["steam_path"]
    except KeyError:
        full_steam_database_path = input("Enter full Steam/music/_database path: ")
        config["osu_songs"]["steam_path"] = full_steam_database_path
        with open(cfg_path, "w") as cfg:
            config.write(cfg)
    _path = Path(full_steam_database_path)
    q = "queue.m3u8"
    p = _path / q
    create_playlist(list_of_song_names)
    with open("playlist.m3u8", "r") as pf:
        # this playlist can't handle song names,while exported to steam music, instead it is audio name
        playlist = pf.read()
    with open(p, "w") as f:
        f.write(playlist)
    print("Export to steam complete")


def get_tags(list_of_song_names, osudict):
    "return 100 most common tags in list_of_song_names , for use in API"
    if list_of_song_names:
        # update osudict
        osudict = {sn: osudict[sn] for sn in list_of_song_names}

    sn_tags = list()
    for song_name, dot_osu in osudict.items():
        with open(dot_osu[0], "r", encoding="utf8") as f:
            for line in f:
                if line.startswith("Tags"):
                    tag_line = line.partition(":")[2].strip()
                    sn_tags.append([song_name, tag_line.lower()])
                    break
    clean_tags = []
    for song_name, song_tags in sn_tags:
        s = song_tags.split(" ")
        stopwords = ["and", "you", "insert", "the", "tag", "your"]
        for i in s:
            if len(i) > 2 and i not in stopwords:
                clean_tags.append(i)
    tags = Counter(clean_tags).most_common(100)

    return tags


names, namedict, osudict, tagdict, hashdict, datedict = get_songs()


def main(
    names=names,
    namedict=namedict,
    osudict=osudict,
    tagdict=tagdict,
    hashdict=hashdict,
    datedict=datedict,
):
    """main logic ,takes those parameters because of closure
       nested args parsing return is used to stop execution
       it may not cover everything
    """

    print("Loading beatmaps...")
    col_name = args.collection_name
    regtag = args.reg_tag
    to_dir = args.to_dir
    inverse = args.inverse  # flag
    to_game = args.db_col_name
    daterange = args.date_range
    name = args.name_it
    path_to_mp3s = args.path_to_mp3s
    to_steam = args.to_steam  # flag
    # ----------------------------------------------------
    if col_name:
        md5s = hashdict
        collections, _version = get_collections()
        col_list = collection_content(col_name, collections, md5s)
        if to_dir:
            export_to_dir(col_list,namedict, to_dir)
            return
        if to_steam:
            export_m3u8_to_steam(col_list)
            return
        else:
            create_playlist(col_list)
            return

    # ----------------------------------------------------
    if path_to_mp3s:
        import_songs_as_collection(path_to_mp3s, name,hashdict=hashdict)
        return

    # ----------------------------------------------------
    if regtag:
        tag_list = filter_tags(osudict, regtag, inverse, tagdict=tagdict)
        if daterange:
            tag_list = apply_daterange(tag_list, daterange, osudict, hashdict, datedict)

        if to_steam:
            export_m3u8_to_steam(tag_list)
            return  # prevent double checking if daterange
        if to_dir:
            export_to_dir(tag_list,namedict, to_dir)
            return

        if to_game:
            update_collection(tag_list, name=to_game, osudict=osudict,hashdict=hashdict)
            return

        else:
            # create playlist with reg as the only one argument
            create_playlist(tag_list)
            return

    # ----------------------------------------------------
    if daterange:
        by_date_names = apply_daterange(names, daterange, osudict, hashdict, datedict)

        if to_dir:
            export_to_dir(by_date_names,namedict, to_dir)
            return

        if to_game:
            update_collection(
                by_date_names, name=to_game, osudict=osudict, hashdict=hashdict
            )
            return

        if to_steam:
            export_m3u8_to_steam(by_date_names)
            return

        else:
            # create playlist with daterange as the only one argument
            create_playlist(by_date_names)
            return
    # ----------------------------------------------------
    if to_dir:  # export all mp3 to specified directory
        export_to_dir(names,namedict, to_dir)
        return

    if to_steam:  # overwrite m3u8 queue file as all songs from osu
        export_m3u8_to_steam(names)
        return

    else:
        # create playlist from all songs if none of args is selected
        if not any(args.__dict__.values()):
            create_playlist(names)


if __name__ == "__main__":
    main()
