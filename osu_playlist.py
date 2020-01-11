##### PUT THIS FILE IN OSU/SONGS FOLDER #####
import argparse
import difflib
import struct
import re
import hashlib
from shutil import copy
from pathlib import Path
from collections.abc import MutableMapping
from collections import OrderedDict
from itertools import groupby

p = Path(".")
collection_db = p.absolute().parent / "collection.db"

text = "https://mpv.io/manual/stable/#keyboard-control"
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
    "--reg_tag",
    "-r",
    action="store",
    dest="reg_tag",
    help="export all songs with regular expression applied to tag string lowercase",
)
parser.add_argument(
    "--to_dir", "-d", action="store", dest="to_dir", help="provide output path"
)
args = parser.parse_args()


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
    nextint(f)
    ncol = nextint(f)
    for i in range(ncol):
        colname = nextstr(f)
        col[colname] = []
        for j in range(nextint(f)):
            f.read(2)
            col[colname].append(f.read(32).decode("utf-8"))
    f.close()
    return col


def get_songs():
    songdirs = [str(i) for i in p.iterdir() if str(i).split()[0].isdigit()]
    # fix empty difficulties
    songdirs = [i for i in songdirs if list(Path(i).glob("*.osu"))]
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
    return (sorted(list(set(names))), namedict, osudict)


names, namedict, osudict = get_songs()
md5s = generate_hashes(osudict)
collections = get_collections()


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


def filter_tags(regtag=None):
    """apply regex to tag line"""
    regtag = regtag.lower()
    regex = re.compile(regtag)

    def group_tags(sn_with_tags, regtag):
        groups = dict()
        f = lambda x: bool(regex.search(x[1]))
        for sn, t in groupby(sn_with_tags, key=f):
            _group = list(t)
            if sn in groups:
                groups[sn] += _group
            else:
                groups[sn] = _group

        return groups

    sn_tags = list()
    for song_name, dot_osu in osudict.items():
        with open(dot_osu[0], "r", encoding="utf8") as f:
            for line in f.readlines():
                if line.startswith("Tags"):
                    tag_line = line.partition(":")[2].strip()
                    sn_tags.append([song_name, tag_line.lower()])
                    break
    _tags = group_tags(sn_tags, regtag)
    true_tags = _tags[True]
    sn_list = [r[0] for r in true_tags]

    return sn_list


def create_playlist(list_of_song_names):
    with open("playlist.m3u8", "w", encoding="utf8") as playlist:
        playlist.write("#EXTM3U" + "\n")
        for sn in list_of_song_names:
            song_name = "#EXTINF:-1," + sn + "\n"
            playlist.write(song_name)
            song_path = str(namedict[sn].resolve()) + "\n"
            playlist.write(song_path)
    print("Playlist created,available songs:", len(list_of_song_names))


def export_to_dir(list_of_song_names, to_dir=None):
    to_dir = Path(str(to_dir))
    if not to_dir.exists():
        to_dir.mkdir()
    for sn in list_of_song_names:
        from_dir = str(namedict[sn])
        end_dir = str(to_dir / sn) + str(namedict[sn].suffix)
        copy(from_dir, end_dir)
    print("Songs export complete,quantity: ", len(list_of_song_names))


if __name__ == "__main__":
    col_name = args.collection_name
    regtag = args.reg_tag
    to_dir = args.to_dir
    if col_name:
        col_list = collection_content(col_name)
        if to_dir:
            export_to_dir(col_list, to_dir)
        else:
            create_playlist(col_list)
    elif regtag:
        tag_list = filter_tags(regtag)
        if to_dir:
            export_to_dir(tag_list, to_dir)
        else:
            create_playlist(tag_list)
    else:
        if to_dir:
            export_to_dir(names, to_dir)
        else:
            create_playlist(names)
