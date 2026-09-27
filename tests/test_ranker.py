from alkamusic import naming, ranker
from alkamusic.engine import parse_input


def r(id, title, channel, duration):
    return {"id": id, "title": title, "channel": channel, "duration": duration}


OLYMPIC = [  # real "ytsearch6:olympic davno" results
    r("a", "Olympic - Dávno HQ", "David Petřík", 252),
    r("topic", "Dávno", "Olympic - Topic", 250),
    r("b", "Olympic - Dávno (1994) (HD Klip)", "Síla hudby", 252),
    r("long", "Olympic - Dávno", "KIRIROCK", 3074),
    r("live", "Olympic - Dávno (live)", "Kobroslav", 260),
]


def test_prefers_topic_channel_studio_version():
    top, uncertain = ranker.best("olympic davno", OLYMPIC)
    assert top["id"] == "topic"
    assert not uncertain


def test_live_allowed_when_asked():
    top, _ = ranker.best("olympic davno live", OLYMPIC)
    assert top["id"] == "live"


def test_penalises_bad_versions_with_typo_query():
    results = [
        r("cover", "Bohemian Rhapsody (cover by Some Guy)", "Some Guy", 355),
        r("karaoke", "Queen - Bohemian Rhapsody Karaoke", "Sing King", 360),
        r("official", "Queen – Bohemian Rhapsody (Official Video Remastered)", "Queen Official", 359),
        r("hour", "Bohemian Rhapsody 1 hour", "Loops", 3600),
    ]
    top, uncertain = ranker.best("queen bohemian rapsody", results)
    assert top["id"] == "official"
    assert not uncertain


def test_nonsense_is_uncertain():
    top, uncertain = ranker.best("nesmyslxyz123", [r("x", "Minecraft let's play #54", "Gamer", 900)])
    assert uncertain


def test_no_results():
    assert ranker.best("cokoli", []) == (None, True)


def song(id, title):
    return {"id": id, "title": title}


def test_best_song_with_typos():  # real YouTube Music results
    songs = [song("a", "Stairway to Heaven (Remaster)"), song("b", "Stairway to Heaven (Live at MSG 1973)")]
    assert ranker.best_song("ledbetr stairway to heven", songs)["id"] == "a"
    assert ranker.best_song("olympic davno", [song("d", "Dávno"), song("j", "Jednou")])["id"] == "d"


def test_best_song_skips_live_and_unrelated():
    songs = [song("live", "Amerika (Opera Live 2003)"), song("ok", "Amerika")]
    assert ranker.best_song("lucie amerika", songs)["id"] == "ok"
    junk = [song("x", "Naruto AMV - Grateful (NEFFEX)"), song("y", "Ex's & Oh's")]
    assert ranker.best_song("nesmyslxyz123qqq", junk) is None


def test_artist_title_from_title():
    assert naming.artist_title("Olympic - Dávno (1994) (HD Klip)", "Síla hudby") == ("Olympic", "Dávno")
    assert naming.artist_title("Queen – Bohemian Rhapsody (Official Video Remastered)", "Queen Official") == (
        "Queen", "Bohemian Rhapsody")
    assert naming.artist_title("Lucie - Amerika [Official Audio] | Lucie 1995", "x") == ("Lucie", "Amerika")


def test_artist_title_from_topic_channel():
    assert naming.artist_title("Dávno", "Olympic - Topic") == ("Olympic", "Dávno")
    assert naming.artist_title("Shape of You", "EdSheeranVEVO") == ("EdSheeran", "Shape of You")


def test_keeps_meaningful_brackets():
    assert naming.artist_title("Queen - Don't Stop Me Now (feat. Brian)", "x") == ("Queen", "Don't Stop Me Now (feat. Brian)")


def test_display_name_is_song_first():
    assert naming.display_name("Olympic", "Dávno") == "Dávno - Olympic"
    assert naming.display_name("", "Dávno") == "Dávno"


def test_safe_filename():
    assert naming.safe_filename('AC/DC - What? "Yes"') == "ACDC - What Yes"


def test_parse_input():
    text = " olympic dávno; lucie amerika ;;\nqueen bohemian\n Olympic Davno ;  "
    assert parse_input(text) == ["olympic dávno", "lucie amerika", "queen bohemian"]
