from osuplaylist.osuplaylist import (
    namedict,
    osudict,
    names,
    tagdict,
    hashdict,
    datedict,
)
from osuplaylist.osuplaylist import (
    apply_daterange,
    filter_tags,
    get_collections,
    get_songs,
)
from osuplaylist.osuplaylist import export_to_dir
from osuplaylist.osuplaylist import (
    update_collection,
    collection_content,
)
from pathlib import Path
import pytest


def test_integrity():
    len_1 = len(osudict)
    len_2 = len(names)
    len_3 = len(namedict)
    assert len_1 == len_2 == len_3


def test_reg_tag():
    _len = len(
        filter_tags(
            osudict=osudict, list_of_song_names=names, regtag="step", tagdict=tagdict
        )
    )
    assert _len > 0


def test_get_collections():
    c, n = get_collections()
    assert type(c) == dict


def test_apply_daterange():
    l = len(apply_daterange(names, ">2020.5.1", osudict, hashdict, datedict))
    assert l > 0 and l <= 999999999999


@pytest.mark.xfail
def test_get_songs_no_path():
    a, b, c = get_songs(pathlib_object=Path(""))
    assert all([a, b, c])


def test_export_to_dir(tmp_path):
    export_to_dir(list_of_song_names=names[:5], namedict=namedict, to_dir=tmp_path)
    assert len(list(tmp_path.iterdir())) > 0


def test_update_and_content_collection():
    update_collection(
        list_of_song_names=names, name="test_pytest", osudict=osudict, hashdict=hashdict
    )
    # it has time() in it
    c, n = get_collections()
    md5s = hashdict
    assert len(collection_content("tEsT_pyTEST", c, md5s)) > 0
    assert len(collection_content("test_pytest", c, md5s)) > 0

    update_collection(
        list_of_song_names=names[:3],
        name="test_pytest",
        osudict=osudict,
        hashdict=hashdict,
    )
    c, n = get_collections()
    md5s = hashdict
    assert len(collection_content("tEsT_pyTEST", c, md5s)) == 3
    assert len(collection_content("TeSt_PYtest", c, md5s)) == 3


def test_chain_functions():
    l = apply_daterange(names, ">2020.1.1", osudict, hashdict, datedict)
    assert len(l) > 0
    l1 = filter_tags(
        list_of_song_names=l, osudict=osudict, regtag="piano", tagdict=tagdict
    )
    assert len(l1) > 0
