# flask--application-Project

Students proceed to upload their reports in student Dashboard
Uploaded reports are shown in the admin dashboard with the upload time of each student along with link to the report and download option in admin dashboard.

Main aim of this project is to integrate chatbot in admin application. This chatbot can retrieve uploaded student files, can read and understand the file and respond to Admin queries about student uploaded reports.

🛠️ Tech Stack Overview:

**Frontend:**
HTML, CSS, JavaScript
Embedded chatbot (bottom-right) in admin dashboard


**Backend:**
Python (Flask)
Firebase Authentication (frontend)
Dropbox API (for storing and retrieving student PDFs)
Postman (for API testing and debugging)


**AI / RAG Pipeline:**

LangChain

Sentence Transformers (for vector embeddings)

ChromaDB (vector store)

RecursiveCharacterTextSplitter (for chunking PDF content)

LLAMA 3.2 (running locally via Ollama)

pdfplumber (for PDF parsing) 
Excel-based apprentice mapping for name/email resolution


📌 Features:
Student dashboard to upload reports
Admin dashboard to view files, track uploads
Embedded RAG chatbot to query PDFs based on apprentice details
Name-to-email mapping from Excel for contextual responses

⚠️ While retrieval performance is limited due to local LLAMA constraints, this project was a great learning experience in building a functional RAG pipeline from scratch.
