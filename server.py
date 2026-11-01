from fastmcp import FastMCP
import library

mcp = FastMCP("Campus Library Assistant")

@mcp.tool
def search_books(query: str) -> dict:
  """Search book titles and authors without changing data.
  
  Args: 
      query: Text to match against a book's title or author.
  
  Returns: 
    A dictionary with success, message, and books.
    Each book includes its current availability.
  """
  return library.search_books(query)


@mcp.tool
def reserve_book(book_id: str, student_id: str) -> dict:
  """Reserve a specific available book for a student.
  
  Write a reservation to disk on success.
  Rejects unknown, unavailable, or already-reserved books.
  
  Args:
      book_id: Catalog ID of the book, such as B001.
      student_id: Non-empty identifier of the student.
      
  Returns:
      A dictionary with success and message.
      Successful results also include the reservation.
  """
  return library.reserve_book(book_id, student_id)


@mcp.tool
def find_and_reserve_book(query: str, student_id: str) -> dict:
  """Find and reserve a single available matching book.
  
  Searches first, then reserves if exactly one available book matches.
  If several match, returns choices without creating a reservation.
  
  Args:
      query: Text to match against a book's title or author.
      student_id: Non-empty identifier of the student.
  
  Returns:
    A dictionary with success and message, plus choices or a reservation when applicable.
  """
  return library.find_and_reserve_book(query, student_id)


if __name__ == "__main__":
  mcp.run(transport='stdio')
