from osuplaylist.osuplaylist import get_songs, Playlist, get_collections
from pathlib import Path
import pytest


names, namedict, osudict, tagdict, hashdict, datedict = get_songs()
_osuplaylist = Playlist(names, namedict, osudict, tagdict, hashdict, datedict)


def test_integrity():
    len_1 = len(osudict)
    len_2 = len(names)
    len_3 = len(namedict)
    assert len_1 == len_2 == len_3


def test_reg_tag():
    _len = len(_osuplaylist.filter_tags(regtag="step",))
    assert _len > 0


def test_get_collections():
    c, n = get_collections()
    assert type(c) == dict


def test_apply_daterange():
    l = len(_osuplaylist.apply_daterange(names, ">2020.5.1"))
    assert l > 0 and l <= 999999999999


@pytest.mark.xfail
def test_get_songs_no_path():
    a, b, c = get_songs(pathlib_object=Path(""))
    assert all([a, b, c])


def test_export_to_dir(tmp_path):
    _osuplaylist.export_to_dir(list_of_song_names=names[:5], to_dir=tmp_path)
    assert len(list(tmp_path.iterdir())) > 0


def test_update_and_content_collection():
    _osuplaylist.update_collection(
        list_of_song_names=names, name="test_pytest",
    )
    # it has time() in it
    c, n = get_collections()
    md5s = hashdict
    assert len(_osuplaylist.collection_content("tEsT_pyTEST", c, md5s)) > 0
    assert len(_osuplaylist.collection_content("test_pytest", c, md5s)) > 0

    _osuplaylist.update_collection(
        list_of_song_names=names[:3], name="test_pytest",
    )
    c, n = get_collections()
    md5s = hashdict
    assert len(_osuplaylist.collection_content("tEsT_pyTEST", c, md5s)) == 3
    assert len(_osuplaylist.collection_content("TeSt_PYtest", c, md5s)) == 3


def test_chain_functions():
    l = _osuplaylist.apply_daterange(names, ">2020.1.1",)
    assert len(l) > 0
    l1 = _osuplaylist.filter_tags(list_of_song_names=l, regtag="piano")
    assert len(l1) > 0
