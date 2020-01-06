##### PUT THIS FILE IN OSU/SONGS FOLDER #####
from pathlib import Path
import argparse
import hashlib
import struct
import difflib
from collections.abc import MutableMapping
from collections import OrderedDict

p = Path(".")
collection_db = p.absolute().parent / "collection.db"

text = "https://mpv.io/manual/stable/#keyboard-control"
parser = argparse.ArgumentParser(description=text)
# https://stackoverflow.com/questions/18157376/handle-spaces-in-argparse-input
parser.add_argument(
    "--collection", dest="collection_name", help="export collection as playlist.m3u8"
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


def create_playlist(list_of_song_names):
    with open("playlist.m3u8", "w", encoding="utf8") as playlist:
        playlist.write("#EXTM3U" + "\n")
        for sn in list_of_song_names:
            song_name = "#EXTINF:-1," + sn + "\n"
            playlist.write(song_name)
            song_path = str(namedict[sn].resolve()) + "\n"
            playlist.write(song_path)
    print("Playlist created,available songs:", len(list_of_song_names))


if __name__ == "__main__":
    col_name = args.collection_name
    if not col_name:
        create_playlist(names)
    else:
        col_list = collection_content(col_name)
        create_playlist(col_list)
