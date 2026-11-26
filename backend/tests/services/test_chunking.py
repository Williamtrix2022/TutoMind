from app.services.chunking import chunk_pages
from app.services.extraction import Page


def test_short_page_is_a_single_chunk_keeping_its_page():
    chunks = chunk_pages([Page(number=3, text="Texto corto.")], size=100, overlap=10)

    assert [(c.index, c.page, c.content) for c in chunks] == [(0, 3, "Texto corto.")]


def test_no_chunk_exceeds_the_size_and_indexes_are_consecutive():
    text = " ".join(f"palabra{i}" for i in range(400))

    chunks = chunk_pages([Page(number=1, text=text)], size=200, overlap=40)

    assert len(chunks) > 1
    assert all(len(c.content) <= 200 for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_consecutive_chunks_overlap_so_context_is_not_cut():
    text = " ".join(f"w{i}" for i in range(300))

    chunks = chunk_pages([Page(number=None, text=text)], size=120, overlap=30)

    first_tail = chunks[0].content.split()[-2:]
    assert all(word in chunks[1].content.split() for word in first_tail)


def test_all_the_text_is_covered():
    words = [f"term{i}" for i in range(250)]

    chunks = chunk_pages([Page(number=1, text=" ".join(words))], size=150, overlap=30)

    covered = {w for c in chunks for w in c.content.split()}
    assert set(words) <= covered


def test_chunks_do_not_mix_pages():
    pages = [Page(number=1, text="uno " * 50), Page(number=2, text="dos " * 50)]

    chunks = chunk_pages(pages, size=80, overlap=10)

    assert {c.page for c in chunks} == {1, 2}
    assert all(("uno" in c.content) == (c.page == 1) for c in chunks)


def test_blank_pages_produce_no_chunks():
    assert chunk_pages([Page(number=1, text="  \n ")], size=100, overlap=10) == []


def test_a_word_longer_than_the_size_is_split_instead_of_looping_forever():
    chunks = chunk_pages([Page(number=1, text="x" * 500)], size=100, overlap=10)

    assert all(len(c.content) <= 100 for c in chunks)
    assert len(chunks) >= 5


def test_overlap_must_be_smaller_than_size():
    import pytest

    with pytest.raises(ValueError):
        chunk_pages([Page(number=1, text="a b c")], size=10, overlap=10)
