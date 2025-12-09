import mysql.connector
import os

# --- Koneksi ke MySQL ---
conn = mysql.connector.connect(
    host="localhost",      
    user="root",          
    password="",
    database="searche_db"   
)

cursor = conn.cursor()

# --- Memasukkan dokumen dari folder documents/ ---
docs_dir = "documents"  # pastikan folder ini ada di project kamu
for file in os.listdir(docs_dir):
    if file.endswith(".txt"):
        with open(os.path.join(docs_dir, file), "r", encoding="utf-8") as f:
            content = f.read()
            cursor.execute(
                "INSERT INTO documents (filename, content) VALUES (%s, %s)",
                (file, content)
            )

# Simpan perubahan
conn.commit()

cursor.close()
conn.close()

print("✅ Semua dokumen berhasil dimasukkan ke tabel MySQL.")
