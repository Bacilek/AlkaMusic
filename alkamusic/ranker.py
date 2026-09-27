"""Picks the best YouTube search result for a (possibly misspelled) song name."""

import difflib
import re
import unicodedata

# Words that usually mean "not the studio version" - penalised unless the user asked for them.
BAD_WORDS = [
    "live", "koncert", "concert", "zive", "zivak", "cover", "remix", "karaoke",
    "instrumental", "reaction", "slowed", "sped up", "8d", "nightcore", "1 hour",
    "10 hours", "hodina", "tutorial", "lesson", "how to play", "bass boosted",
    "mashup", "full album", "reverb", "parodie", "parody",
]
GOOD_WORDS = {"official audio": 10, "official video": 6, "official music video": 6, "oficialni": 5}

UNCERTAIN_MATCH = 0.5


def normalize(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def match_ratio(query, text):
    """Average of best fuzzy match for every query word within the text (0..1)."""
    q_words = normalize(query).split()
    t_words = normalize(text).split()
    if not q_words or not t_words:
        return 0.0
    total = 0.0
    for q in q_words:
        total += max(difflib.SequenceMatcher(None, q, t).ratio() for t in t_words)
    return total / len(q_words)


def score(query, result, position=0):
    title = result.get("title") or ""
    channel = result.get("channel") or result.get("uploader") or ""
    q = f" {normalize(query)} "
    t = f" {normalize(title)} "

    s = match_ratio(query, f"{title} {channel}") * 50
    s += max(0, 6 - position) * 3  # YouTube's own relevance order is a good signal

    if channel.endswith(" - Topic"):
        s += 15
    elif "vevo" in channel.lower():
        s += 5
    for word, bonus in GOOD_WORDS.items():
        if f" {word} " in t:
            s += bonus
    for word in BAD_WORDS:
        in_title, in_query = f" {word} " in t, f" {word} " in q
        if in_title and not in_query:
            s -= 40
        elif in_query and not in_title:
            s -= 25  # the user explicitly wants e.g. a live version

    duration = result.get("duration")
    if duration:
        if duration < 60 or duration > 900:
            s -= 60
        elif duration > 600:
            s -= 30
    return s


def _has_unwanted_word(query, title):
    q, t = f" {normalize(query)} ", f" {normalize(title)} "
    return any(f" {w} " in t and f" {w} " not in q for w in BAD_WORDS)


def best_song(query, songs, top_n=3):
    """Picks from YouTube Music 'songs' results (they have no artist, only the song title).

    A song is accepted when (almost) every word of its title appears in the query, so the
    query 'olympic davno' accepts 'Dávno'. Returns None when nothing fits - then a normal
    YouTube search is used instead.
    """
    q_words = normalize(query).split()
    for song in songs[:top_n]:
        core = re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", song.get("title") or "")
        words = normalize(core).split()
        if not words or _has_unwanted_word(query, song.get("title")):
            continue
        coverage = sum(
            max(difflib.SequenceMatcher(None, w, q).ratio() for q in q_words) for w in words
        ) / len(words)
        if coverage >= 0.8:
            return song
    return None


def best(query, results):
    """Returns (result, uncertain) or (None, True) when nothing usable was found."""
    if not results:
        return None, True
    scored = [(score(query, r, i), i, r) for i, r in enumerate(results)]
    _, _, top = max(scored, key=lambda x: (x[0], -x[1]))
    channel = top.get("channel") or top.get("uploader") or ""
    uncertain = match_ratio(query, f"{top.get('title', '')} {channel}") < UNCERTAIN_MATCH
    return top, uncertain
