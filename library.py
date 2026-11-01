import json
import os
from pathlib import Path

DATA_DIR_PATH = Path(__file__).resolve().parent / "data"
CATALOG_PATH = DATA_DIR_PATH / "catalog.json"
RESERVATIONS_PATH = Path(os.getenv("LIBRARY_RESERVATIONS_PATH", str(DATA_DIR_PATH / "reservations.json")))

def load_catalog() -> list[dict]:
  with CATALOG_PATH.open(encoding='utf-8') as file:
    return json.load(file)
  
def load_reservations() -> list[dict]:
  # A fresh checkout has no private reservation data yet. Reading creates nothing.
  if not RESERVATIONS_PATH.exists():
    return []
  with RESERVATIONS_PATH.open(encoding='utf-8') as file:
    return json.load(file)
  
def search_books(query: str) -> dict:
  """Search book titles and authors without changing stored data.
  
  Returns success, message, and a list of matching books.
  Each book includes its current availability.
  """
  
  query = query.strip()
  
  if not query:
    return {
      "success": False,
      "message": "Search query cannot be empty.",
      "books": [],
    }
    
  catalog = load_catalog()
  reservations = load_reservations()
  
  reserved_ids = {
    reservation['book_id']
    for reservation in reservations
  }
  
  matches = []
  
  for book in catalog:
    searchable_text = f"{book['title']} {book['author']}"
    
    if query.casefold() in searchable_text.casefold():
      result = book.copy()
      result['available'] = (
        book['available'] and book['id'] not in reserved_ids
      )
      matches.append(result)
  
  return {
    'success': True,
    'message': f"Found {len(matches)} matching book(s).",
    'books': matches,
  }

def reserve_book(book_id: str, student_id: str) -> dict:
  """Reserve one available book for a student.
  Saves the reservation to disk on success.
  Returns success, message, and the reservation when created.
  """
  
  book_id = book_id.strip().upper()
  student_id = student_id.strip()
  
  if not book_id or not student_id:
    return {
      "success": False,
      "message": "Book ID and student ID are required",
    }
    
  catalog = load_catalog()
  
  book = next(
    (book for book in catalog if book['id'] == book_id),
    None,
  )
  
  if book is None:
    return {
      "success": False,
      "message": f"Book {book_id} does not exist!",
    }
    
  reservations = load_reservations()
  
  if any(
    reservation['book_id'] == book_id 
    for reservation in reservations
  ):
    return {
      "success": False,
      "message": f"Book {book_id} is reserved.",
    }
    
  if book['available'] == False:
    return {
      "success": False,
      "message": f"Book {book_id} is unavailable.",
    }
    
  reservation = {
    "book_id": book_id,
    "student_id": student_id,
  }
  
  reservations.append(reservation)
  
  with RESERVATIONS_PATH.open('w', encoding='utf-8') as file:
    json.dump(reservations, file, indent=2)
  
  return {
    "success": True,
    "message": f"Reserved {book["title"]} for {student_id}.",
    "reservation": reservation,
  }
  
def find_and_reserve_book(query: str, student_id: str) -> dict:
  """Search for a book and reserve a single available match.
  
  If several available books match, returns choices without reserving.
  Returns success, message, and either choices or a reservation.
  """
  
  if not student_id.strip():
    return {
      "success": False,
      "message": "Student ID is required.",
    }
    
  search_result = search_books(query)
  
  if not search_result['success']:
    return search_result
  
  available_books = [
    book 
    for book in search_result["books"]
    if book['available']
  ]
  
  if not available_books:
    return {
      "success": False,
      "message": "No available books match your query.",
    }
    
  if len(available_books) > 1:
    return {
      "success": False,
      "message": (
        "Several available books match. "
        "Choose a book ID to reserve."
      ),
      "choices": available_books,
    }
    
  book = available_books[0]
  
  return reserve_book(book['id'], student_id)
