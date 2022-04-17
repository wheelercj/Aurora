from ssg.zettel import Zettel, get_zettel_by_id_or_file_name


class Zettel_for_testing(Zettel):
    def __init__(self):
        pass


def test___get_zettel_link_with_ID_in_name_and_content():
    assert (
        Zettel_for_testing()._Zettel__get_zettel_link(
            "20210919100142", "20210919100142", "zettel title"
        )
        == "[[20210919100142]] zettel title"
    )


def test___get_zettel_link_with_different_file_name():
    assert (
        Zettel_for_testing()._Zettel__get_zettel_link(
            "file name", "20210919100142", "zettel title"
        )
        == "[[20210919100142]] zettel title"
    )


def test___get_zettel_link_without_ID():
    assert (
        Zettel_for_testing()._Zettel__get_zettel_link("file name", None, "zettel title")
        == "[[file name]]"
    )


def test___get_zettel_name_link():
    assert (
        Zettel_for_testing()._Zettel__get_zettel_name_link("file name")
        == "[[file name]]"
    )


def test_create_html_path():
    assert (
        Zettel_for_testing().create_html_path(
            "C:/Users/chris/Documents/site/pages/20200522233055.md"
        )
        == "C:/Users/chris/Documents/site/pages/20200522233055.html"
    )


def test_get_zettel_by_id():
    z1 = Zettel_for_testing()
    z2 = Zettel_for_testing()
    z1.id = "20210919100142"
    z2.id = "20200522233055"
    assert z2 == get_zettel_by_id_or_file_name("20200522233055", [z1, z2])


def test_get_zettel_by_file_name():
    z1 = Zettel_for_testing()
    z2 = Zettel_for_testing()
    z1.file_name = "positive health"
    z2.file_name = "emergence"
    z1.file_name_and_ext = "positive health.md"
    z2.file_name_and_ext = "emergence.markdown"
    assert z2 == get_zettel_by_id_or_file_name("emergence", [z1, z2])


def test_get_nonexistent_zettel():
    z1 = Zettel_for_testing()
    z2 = Zettel_for_testing()
    z1.id = "20210919100142"
    z2.id = "20200522233055"
    z1.file_name = "positive health"
    z2.file_name = "emergence"
    z1.file_name_and_ext = "positive health.md"
    z2.file_name_and_ext = "emergence.markdown"
    assert None == get_zettel_by_id_or_file_name("20200522233056", [z1, z2])
