import sqlite3

conn = sqlite3.connect('database.db')
print ("Opened database successfully")

cursor = conn.execute("SELECT text from note")
for row in cursor:
   print ("id = ", row[0])
#    print ("text = ", row[1])
#    print ("done = ", row[2])
#    print ("dateAdded = ", row[3], "\n")

print ("Operation done successfully")
conn.close()