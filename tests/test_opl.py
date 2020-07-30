from osuplaylist.osuplaylist import namedict, osudict, names, p
from osuplaylist.osuplaylist import apply_daterange, filter_tags, get_collections, get_songs
from osuplaylist.osuplaylist import export_to_dir
from osuplaylist.osuplaylist import update_collection, generate_hashes, collection_content
from pathlib import Path
import pytest

# create new directory, add beatmaps there, set it osu_playlist_config.ini as path
# one beatmap with regex matching "step" is needed
# tweak len  to length matching all valid beatmaps in that directory
LENGTH = 8


def test_integrity():
    len_1 = len(osudict)
    len_2 = len(names)
    len_3 = len(namedict)
    assert len_1 == len_2 == len_3 == LENGTH


def test_reg_tag():
    assert (
        len(filter_tags(osudict=osudict, list_of_song_names=names, regtag="step"))
        == LENGTH - 7
    )
    assert (
        len(
            filter_tags(
                osudict=osudict, list_of_song_names=names, regtag="step", inverse=True
            )
        )
        == LENGTH - 1
    )


def test_get_collections():
    c, n = get_collections()
    assert type(c) == dict


def test_apply_daterange():
    assert len(apply_daterange(names, ">2020.5.1")) == LENGTH - 7
    assert len(apply_daterange(names, "<2020.5.1")) == LENGTH - 1


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
    assert len(collection_content("tEsT_pyTEST", c, md5s)) == LENGTH - 5
    assert len(collection_content("TeSt_PYtest", c, md5s)) == LENGTH - 5


def test_chain_functions():
    l = apply_daterange(names, "<2020.5.1")
    assert len(l) == LENGTH - 1
    l1 = filter_tags(list_of_song_names=l, osudict=osudict, regtag="step")
    assert len(l1) == LENGTH - 7
