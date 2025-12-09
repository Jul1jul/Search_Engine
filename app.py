from flask import Flask, render_template, request, send_from_directory
import mysql.connector
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from nltk.corpus import stopwords
import string
import os

app = Flask(__name__)

# Setup nltk
nltk.download('punkt')
nltk.download('stopwords')

factory = StemmerFactory()
stemmer = factory.create_stemmer()
stop_words = set(stopwords.words("indonesian")) | set(stopwords.words("english"))

def preprocess(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = nltk.word_tokenize(text)
    tokens = [stemmer.stem(word) for word in tokens if word not in stop_words]
    return " ".join(tokens)

# --- Koneksi ke MySQL ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",           
        password="",
        database="searche_db"   
    )

# --- Load dokumen dari database ---
def load_from_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT filename, content FROM documents")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# --- Load dokumen dari folder ---
def load_from_folder():
    docs_dir = "documents"
    rows = []
    for file in os.listdir(docs_dir):
        if file.endswith(".txt"):
            with open(os.path.join(docs_dir, file), "r", encoding="utf-8") as f:
                content = f.read()
                rows.append({"filename": file, "content": content})
    return rows

# --- Gabungkan sumber data ---
all_rows = load_from_db() + load_from_folder()

documents = [preprocess(r["content"]) for r in all_rows]
filenames = [r["filename"] for r in all_rows]

# --- TF-IDF ---
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(documents)

def search(query):
    query_processed = preprocess(query)
    query_vec = vectorizer.transform([query_processed])
    cosine_sim = cosine_similarity(query_vec, tfidf_matrix).flatten()
    ranking = sorted(list(enumerate(cosine_sim)), key=lambda x: x[1], reverse=True)
    results = [(filenames[idx], cosine_sim[idx]) for idx, score in ranking if score > 0]
    return results

@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    results = []
    if request.method == "POST":
        query = request.form["query"]
        results = search(query)
    return render_template("index.html", query=query, results=results)

# --- Route untuk membuka dokumen dari folder ---
@app.route("/document/<filename>")
def open_document(filename):
    docs_dir = "documents"
    if os.path.exists(os.path.join(docs_dir, filename)):
        return send_from_directory(docs_dir, filename)
    else:
        # kalau tidak ada di folder, coba ambil dari database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT content FROM documents WHERE filename = %s", (filename,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return f"<h1>{filename}</h1><pre>{row['content']}</pre>"
        else:
            return "❌ Dokumen tidak ditemukan", 404

if __name__ == "__main__":
    app.run(debug=True)
