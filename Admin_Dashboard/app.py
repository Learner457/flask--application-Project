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
DROPBOX_ACCESS_TOKEN = 'sl.u.AFsnW2dLk1ZQv5wb4YRjuZZDMNndt9ZNQiDpI7HRxNaOtaNNUqiNzYAC12NYXRwqPHFQJc_I3zq0zxKRWW4WuNPOJRdRy3KI_vLVctV4YdLrLI2fxv_5Is98wXvhx11oPcIVYfsEGVbHYD-QZbEoTPDXKj7Y1mZXQPzs-bajm1f4Y6QiUCySwg45FgLh4-fbY-BgkptsrYd5h40F2unl6wir4_E0mqmgtOTPZAxub9-GAKQR5otreeKtoRDIjZ7l44-nNm_S8hMjs_TkvxTSrPz5Y2WtW0VfQGbR5zOnh9uzBdWfydTsJ-528DeaLLhwSoWMR9nR2g7ikGalLRk7wLz31EK7uvBN4Qygjet96vr50qDO-vz4dbrDqy0jyrmiecbpwJxtscJtZcO38CqfB53ZyoGvBlO21oc_YO_XagWYOJNhYuDO6tW8khBoVnvWF6dugONhbPZi-o6AEPBa2Dum1d3iaUcb1MbMoRPg-mdAFzxCF1ClM2HtGsC7aBA1_4uZg4pZ4wQs6r4SvY25LZy8ZkCdQnt27uSxvqVMgQezSpdtvd2LkZUjVN88hICdjmR8klJxLwxQRbk2D09-vvaBIKzZBrPpZGRayRt1viEEqiHVu00cDok7QynR1ln6f6hYDVZjXIZNkxx0FeuywHWxFtNH-BKuY_hLAXEPKcYGXadn2t0Na-FbgRsoWnMmBmVt4Ad0NBp54B2a-3rpdbt7LrDYodoquiaknnN8DF4-Q9vn2vksRbEFftUUcOj-5mMlV99VZTPThOfmJ6BYfK_CQMCHi8fG6AIz1xOmvEZE0Q8A81hDxhWUOl3kLYMrlcv1MgNDAejxaX57OkFcIfENunMjByogUoohyBXLdIGtdP7FjxdRvsXdZ_eaIa-8cWeILfYEBuKNrQzoN-7VI3-36m1R519_2ujxZT2wG5oKXHMz7HJVwvJJN7l-JL_NkfxxEUunPo8s9XIBS0UHKBUCje3luANYORjgd05pPXHnUgd0eeNdqvsIVKUXo7QFCbUcPoRJT2jFWQp0nj8IQo1108_JWAmWq0HzUJOJ6mnpBeP5xkduRe_c8Yn3Eg_6rh6opDXAzPAFp0R0Tqq-O-q5Fph9R8SYPEf9ivFDHvQhlPy9kMcSdYsXwyXZUKZRTAAzVMKsC1_he8w9Esr-5SunFFo0XpYpMSMc-M7NdGPe-m0pqsjyfjXnCzoJjlx0WA7b_AEzp-8htCj6jtpq1-idYh3Erj5KunQSWL7TVeAS3VwtHVRIiN6Rub3ABUiZcu1J28dIpH37tH13slzmOwr2h_KIs1Cb_bf4BOIZbVrg7x11MZ8W27zongzgQ5Ea10i9zabPZkP5uXpJo3in_vVUiPOmaXsG1bR4kg0pCsTgroxTH-p-jCzk7o3ISkh0xoyuSjdyl9B9rTdVEANovGQPgdWswrygo-oNIOj95Pck-w'
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

