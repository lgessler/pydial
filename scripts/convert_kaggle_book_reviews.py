import sqlite3
import csv

with open('br.csv','r') as f:
    rows = csv.reader(f,delimiter=',',quotechar='"')
    conn = sqlite3.connect('GoodreadsBooks.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS books")
    c.execute('''CREATE TABLE GoodreadsBooks 
                 (bookid integer,
                  title text,
                  author text,
                  rating text,
                  ratingscount text,
                  reviewscount text,
                  reviewername text,
                  reviewratings text,
                  review text)''')
    for bookid, title, author, rating, ratingscount, reviewscount, reviewername, reviewratings, review in rows:
        if bookid == 'bookID':
            continue

        review = review.replace("'", "''")
        reviewername = reviewername.replace("'", "''")
        author = author.replace("'", "''")
        title = title.replace("'", "''")

        bookid = bookid or 'NULL'
        title = title or 'NULL'
        author = author or 'NULL'
        rating = rating or 'NULL'
        ratingscount = ratingscount or 'NULL'
        reviewscount = reviewscount or 'NULL'
        reviewername = reviewername or 'NULL'
        reviewratings = reviewratings or 'NULL'
        review = review or 'NULL'

        s = "INSERT INTO GoodreadsBooks VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(bookid, title, author, rating, ratingscount, reviewscount, reviewername, reviewratings, review) 
        c.execute(s) 

    conn.commit()
    conn.close()

