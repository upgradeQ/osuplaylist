from osuplaylist.osuplaylist import namedict, osudict, names, p
from osuplaylist.osuplaylist import (
    apply_daterange,
    filter_tags,
    get_collections,
    get_songs,
)
from osuplaylist.osuplaylist import export_to_dir
from osuplaylist.osuplaylist import (
    update_collection,
    generate_hashes,
    collection_content,
)
from pathlib import Path
import pytest

# create new directory, add beatmaps there, set it osu_playlist_config.ini as path
# one beatmap with regex matching "step" is needed
# for test_chain_functions set a score in osu!.db with date > 2020.1.1 beatmap with
# piano tag needed e.g  624995 xi - ANiMA/ 

LENGTH = 9  # legit maps
"""
osu.db
collection.db
songs/
    202017 asdf asdf asdf/
    1109271 Kanzaki Elza starring ReoNa - Dancer in the Discord/
    295848 nameless - SLoWMoTIoN [no video]/
    399096 OwataP - Turkish March - Owata (^o^)_/
    624995 xi - ANiMA/
    72474 Various Artist - Long Stream Practice Maps/
    752480 YURiKA - MIND CONDUCTOR (TV Size) [no video]/
    912680 Camellia - Exit This Earth's Atomosphere (Camellia's PLANETARY__200STEP Remix)/
    916990 _namirin - Koishiteiku Planet/
    92509 senya - Kanjou Chemistry (Drum 'n' Bass Remix)/
    961717 Reol - Utena/
"""


def test_integrity():
    len_1 = len(osudict)
    len_2 = len(names)
    len_3 = len(namedict)
    assert len_1 == len_2 == len_3 == LENGTH


def test_reg_tag():
    _len = len(filter_tags(osudict=osudict, list_of_song_names=names, regtag="step"))
    assert _len == 1
    _len = len(
        filter_tags(
            osudict=osudict, list_of_song_names=names, regtag="step", inverse=True
        )
    )
    assert _len == 8


def test_get_collections():
    c, n = get_collections()
    assert type(c) == dict


def test_apply_daterange():
    l =len(apply_daterange(names, ">2020.5.1",osudict))
    assert l > 1 and l <= LENGTH



@pytest.mark.xfail
def test_get_songs_no_path():
    a, b, c = get_songs(pathlib_object=Path(""))
    assert all([a, b, c])


def test_export_to_dir(tmp_path):
    export_to_dir(list_of_song_names=names, to_dir=tmp_path)
    assert len(list(tmp_path.iterdir())) == LENGTH


def test_update_and_content_collection():
    update_collection(list_of_song_names=names, name="test_pytest", osudict=osudict)
    # it has time() in it
    c, n = get_collections()
    md5s = generate_hashes(osudict)
    assert len(collection_content("tEsT_pyTEST", c, md5s)) == LENGTH
    assert len(collection_content("test_pytest", c, md5s)) == LENGTH

    update_collection(list_of_song_names=names[:3], name="test_pytest", osudict=osudict)
    c, n = get_collections()
    md5s = generate_hashes(osudict)
    assert len(collection_content("tEsT_pyTEST", c, md5s)) == 3
    assert len(collection_content("TeSt_PYtest", c, md5s)) == 3


def test_chain_functions():
    l = apply_daterange(names, ">2020.1.1",osudict=osudict)
    assert len(l) > 1
    l1 = filter_tags(list_of_song_names=l, osudict=osudict, regtag="piano")
    assert len(l1) == 1
