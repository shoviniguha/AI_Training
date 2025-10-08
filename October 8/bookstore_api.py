from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

#create FastAPI instance
app=FastAPI()

class Book(BaseModel):
    id: int
    title: str
    author: str
    price: float
    in_stock: bool

books=[
    {"id":1,"title":"Animal Farm","author":"George Orwell","price":500,"in_stock":True},
    {"id":2,"title":"Harry Potter","author":"J.K. Rowling","price":700,"in_stock":True},
    {"id":3,"title":"Twilight","author":"Stephanie Meyer","price":600,"in_stock":False}
]

@app.get("/books")
def get_all_books():
    return {"books": books}

@app.get("/books/search")
def search_books(author: Optional[str] = Query(None), max_price: Optional[int] = Query(None)):
    if author is None and max_price is None:
        raise HTTPException(status_code=400,
                            detail="At least one query parameter (author or max_price) must be provided.")
    results = books
    if author:
        results = [b for b in results if b["author"]== author]
    if max_price is not None:
        results = [b for b in results if b["price"] <= max_price]

    if not results:
        raise HTTPException(status_code=404, detail="No books found matching the criteria.")
    return results

@app.get("/books/available")
def get_available_books():
    lst=[]
    for i in books:
        if i["in_stock"]:
            lst.append(i)
    return {"books available": lst}

@app.get("/books/count")
def get_count():
    return {"number of books": len(books)}

@app.get("/books/{id}")
def get_book(id: int):
    for b in books:
        if b["id"] == id:
            return b
    raise HTTPException(status_code=404, detail="book not found")

@app.post("/books",status_code=201)
def add_book(book: Book):
    b=book.dict()
    if b['price'] <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than zero.")
    else:
        books.append(book.dict())
        return {"message":"book added succesfully","book":book}

@app.put("/books/{book_id}")
def update_book(book_id: int, updated_book: Book):
    for i, b in enumerate(books):
        if b["id"] == book_id:
            books[i] = updated_book.dict()
            return{"message":"book updated succesfully","book":updated_book}
    raise HTTPException(status_code=404, detail="book not found")

@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    for i, b in enumerate(books):
        if b["id"] == book_id:
            books.pop(i)
            return {"message": "book deleted succesfully"}
    raise HTTPException(status_code=404, detail="book not found")


