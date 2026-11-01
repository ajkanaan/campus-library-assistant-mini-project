import json

import pytest

import library


@pytest.fixture
def reservations(tmp_path, monkeypatch):
    path = tmp_path / "reservations.json"
    monkeypatch.setattr(library, "RESERVATIONS_PATH", path)
    return path


def test_search_is_read_only_and_case_insensitive(reservations):
    result = library.search_books(" pYtHoN ")
    assert result["success"]
    assert {b["id"] for b in result["books"]} == {"B002", "B003"}
    assert not reservations.exists()


def test_empty_and_no_match_search(reservations):
    assert not library.search_books(" ")["success"]
    assert library.search_books("no-such-title")["books"] == []


def test_reservation_persists_and_changes_reported_availability(reservations):
    before = library.CATALOG_PATH.read_bytes()
    result = library.reserve_book(" b001 ", " S001 ")
    assert result["success"]
    assert json.loads(reservations.read_text()) == [{"book_id": "B001", "student_id": "S001"}]
    assert not library.search_books("Modern Approach")["books"][0]["available"]
    assert library.CATALOG_PATH.read_bytes() == before


@pytest.mark.parametrize("book,student", [("B999", "S001"), ("B004", "S001"), ("", "S001"), ("B001", " ")])
def test_invalid_reservation_does_not_write(reservations, book, student):
    result = library.reserve_book(book, student)
    assert not result["success"]
    assert result["message"]
    assert not reservations.exists()


def test_duplicate_does_not_change_saved_data(reservations):
    library.reserve_book("B001", "S001")
    before = reservations.read_bytes()
    assert not library.reserve_book("B001", "S002")["success"]
    assert reservations.read_bytes() == before


def test_orchestration_ambiguous_then_single_match(reservations):
    result = library.find_and_reserve_book("Python", "S001")
    assert not result["success"]
    assert len(result["choices"]) == 2
    assert not reservations.exists()
    assert library.find_and_reserve_book("Pragmatic", "S001")["success"]
    assert json.loads(reservations.read_text())[0]["book_id"] == "B006"


@pytest.mark.parametrize("query,student", [("", "S001"), ("Pragmatic", " "), ("no-such-title", "S001"), ("Algorithms", "S001")])
def test_orchestration_failure_does_not_write(reservations, query, student):
    assert not library.find_and_reserve_book(query, student)["success"]
    assert not reservations.exists()
