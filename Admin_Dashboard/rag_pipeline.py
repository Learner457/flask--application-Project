import os
import requests
import pandas as pd
import pdfplumber 
from io import BytesIO
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from embedding import get_embeddings  # your custom embedding wrapper

EXCEL_PATH = "config/apprentice_list.xlsx"
PDF_BASE_URL = "http://localhost:5000/download/"
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
CHROMA_DB_DIR = "chroma_db"

class CustomEmbedding(Embeddings):
    def embed_documents(self, texts):
        return [get_embeddings(text) for text in texts]
    
    def embed_query(self, text):
        return get_embeddings(text)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

def load_apprentice_list():
    return pd.read_excel(EXCEL_PATH)



def fetch_pdf_text(email):
    pdf_url = f"{PDF_BASE_URL}{email}_report.pdf"
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        pdf_bytes = BytesIO(response.content)

        # Dictionary to store each page's content separately
        page_texts = {}

        with pdfplumber.open(pdf_bytes) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    page_texts[i + 1] = page_text.strip()  # Store by page number

        return page_texts

    except Exception as e:
        print(f"[ERROR] Could not fetch/read PDF with pdfplumber: {e}")
        return None



def build_vector_store(pdf_text, email):
    # Treat each page as a separate chunk
    docs = [Document(page_content=page_text, metadata={"email": email, "page": page_num})
            for page_num, page_text in pdf_text.items()]
    
    db_path = os.path.join(CHROMA_DB_DIR, email)  # keep email as-is
    return Chroma.from_documents(documents=docs, embedding=CustomEmbedding(), persist_directory=db_path)



def query_rag(email, question):
    db_path = os.path.join(CHROMA_DB_DIR, email)
    if not os.path.exists(db_path):
        pdf_text = fetch_pdf_text(email)
        if not pdf_text:
            return "The mentioned apprentice has not uploaded their report yet."
        vector_store = build_vector_store(pdf_text, email)
    else:
        vector_store = Chroma(persist_directory=db_path, embedding_function=CustomEmbedding())

    # Here, instead of general search, we specify that it should look at pages related to Udemy training
    docs = vector_store.similarity_search(question, k=4)
    context = "\n\n".join([doc.page_content for doc in docs])

    return query_llama_with_context(question, context)



def query_llama_with_context(question, context):
    headers = {"Content-Type": "application/json"}
    prompt = f"""You are an assistant that answers strictly based on the retrieved context.

Context:
{context}

Question:
{question}

If the answer is not available in the context, say: 'The answer is not available in the student's report.'
"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, headers=headers)
        return response.json().get("response", "[No response from LLaMA]")
    except Exception as e:
        return f"[Error contacting LLaMA: {e}]"


def process_query(question):
    question_clean = question.strip().lower()
    greetings = ["hi", "hello", "how are you", "hey", "what's up"]
    if any(greet in question_clean for greet in greetings):
        return "Hello! I'm your AI assistant. I'm here to help you with questions about uploaded student reports and apprentice training details."

    df = load_apprentice_list()
    question_lower = question.lower()

    if "how many students uploaded" in question_lower:
        uploaded = []
        for _, row in df.iterrows():
            email = row['Gmail ID']
            try:
                if requests.get(f"{PDF_BASE_URL}{email}_report.pdf").status_code == 200:
                    uploaded.append(row['Name'])
            except:
                pass
        return f"{len(uploaded)} students uploaded their PDFs: {', '.join(uploaded)}"

    if "not uploaded" in question_lower or "who has not uploaded" in question_lower:
        not_uploaded = []
        for _, row in df.iterrows():
            email = row['Gmail ID']
            try:
                if requests.get(f"{PDF_BASE_URL}{email}_report.pdf").status_code != 200:
                    not_uploaded.append(row['Name'])
            except:
                not_uploaded.append(row['Name'])
        return f"{len(not_uploaded)} students have not uploaded PDFs: {', '.join(not_uploaded)}"

    matched_rows = df[df['Name'].str.lower().apply(lambda name: any(token in name for token in question_lower.split()))]
    if matched_rows.empty:
        return "The mentioned apprentice has not uploaded their report or is not in the apprentice list."
    elif len(matched_rows) > 1:
        names = matched_rows['Name'].tolist()
        return f"Multiple apprentices matched: {', '.join(names)}. Please be more specific."

    match = matched_rows.iloc[0]
    email = match["Gmail ID"]
    return query_rag(email, question)


