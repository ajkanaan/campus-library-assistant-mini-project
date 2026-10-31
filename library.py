import json
from pathlib import Path

DATA_DIR_PATH = Path(__file__).resolve().parent / "data"
CATALOG_PATH = DATA_DIR_PATH / "catalog.json"
RESERVATIONS_PATH = DATA_DIR_PATH / "reservations.json"

def load_catalog() -> list[dict]:
  with CATALOG_PATH.open(encoding='utf-8') as file:
    return json.load(file)
  
def load_reservations():
  with RESERVATIONS_PATH.open(encoding='utf-8') as file:
    return json.load(file)
  
def search_books(query: str):
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
