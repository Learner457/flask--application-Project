from flask import Flask, render_template, request, session, redirect, jsonify, send_file
import dropbox
from firebase_admin import credentials, initialize_app
import os
from rag_pipeline import process_query
from datetime import datetime
import io
import chromadb
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
app.secret_key = 'gfghfghfjtf'

# Initialize Dropbox
DROPBOX_ACCESS_TOKEN = 'W0VfQG8s9XIBS"   #This is sample token
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Initialize Firebase Admin
cred = credentials.Certificate('config/admin-dashboard-portal-firebase-adminsdk-fbsvc-cff7413f3c.json')
initialize_app(cred)


# Initialize ChromaDB client using the new API
client = chromadb.PersistentClient(path="db")
collection = client.get_or_create_collection(name="student_reports")

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def store_embeddings_in_chroma(text, metadata):
    embedding = embedding_model.encode([text])[0]
    doc_id = metadata.get("email", "unknown") + "_report"
    collection.add(documents=[text], embeddings=[embedding], metadatas=[metadata], ids=[doc_id])
    return "Embedding stored successfully!"


def get_embeddings(text):
    return embedding_model.encode([text])[0]

def query_chroma(query_text):
    """
    Query ChromaDB using the embedding of the input query and return the closest matching document.
    """
    query_embedding = get_embeddings(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=1
    )

    return results['documents'][0] if results['documents'] else "No relevant information found."


@app.route('/')
def home():
    return redirect('/admin-login')

@app.route('/admin-login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/set-session-admin', methods=['POST'])
def set_session_admin():
    data = request.get_json()
    session['admin_email'] = data.get('email')
    return jsonify({"message": "Session set"}), 200

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_email' not in session:
        return redirect('/admin-login')
    return render_template('admin_dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin-login')

@app.route('/list-dropbox-folders')
def list_dropbox_folders():
    try:
        result = dbx.files_list_folder(path="")
        folders = [entry.name for entry in result.entries if isinstance(entry, dropbox.files.FolderMetadata)]
        return jsonify(folders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list-pdfs/<folder_name>')
def list_pdfs(folder_name):
    folder_path = f"/{folder_name}"
    try:
        result = dbx.files_list_folder(folder_path)
        pdfs = []
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.lower().endswith('.pdf'):
                link = dbx.files_get_temporary_link(entry.path_lower).link
                pdfs.append({
                    'name': entry.name,
                    'upload_time': entry.client_modified.strftime("%Y-%m-%d %H:%M:%S"),
                    'download_link': link
                })
        return jsonify(pdfs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_pdf(filename):
    try:
        dropbox_path = f'/Apprentice Training report 2024/{filename}'
        metadata, res = dbx.files_download(path=dropbox_path)
        return send_file(
            io.BytesIO(res.content),
            mimetype='application/pdf',
            download_name=filename,
            as_attachment=False
        )
    except Exception as e:
        return f"Error: {str(e)}", 500




@app.route('/ask-bot', methods=['POST'])
def ask_bot():
    user_query = request.json.get('question')

    if not user_query:
        return jsonify({"answer": "Please provide a valid question."})

    # Use RAG (process query) from rag_pipeline to get the answer
    answer = process_query(user_query)

    return jsonify({"answer": answer})







#import requests needed for this code
# Test LLaMA integration
import requests

def query_llama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2",  # or "llama3" if that's how it's tagged locally
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error from LLaMA: {response.text}"
    except Exception as e:
        return f"Exception while calling LLaMA: {str(e)}"


# Testing embedding model (RAG) Working using postman
@app.route('/test-store-embedding', methods=['POST'])
def test_store():
    data = request.json
    text = data.get('text')
    metadata = data.get('metadata', {})
    result = store_embeddings_in_chroma(text, metadata)
    return jsonify({"message": result})



if __name__ == '__main__':
    app.run(debug=True)

