#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('Database.db')
c = conn.cursor()
print ("Opened database successfully")

cursor = c.execute("SELECT * from Websites")
print (cursor.fetchall()[0][0])
print ("Records created successfully")
conn.close()