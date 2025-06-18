# ⚖️ LegalChat – AI-Powered Legal Chatbot with Gemini

**LegalChat** is an intelligent chatbot designed to provide accurate, context-aware answers to legal queries by utilizing user-uploaded legal documents. It combines local semantic search with Google's Gemini AI to deliver reliable responses based on real legal text.

---

## 🚀 Key Features

- 📚 **Document-Aware**: Understands and responds using your uploaded legal documents.
- 🧠 **Semantic Search**: Uses FAISS and Sentence Transformers for retrieving the most relevant content.
- 💬 **Gemini AI Integration**: Generates smart, natural language answers based on legal context.
- 🧾 **Customizable**: Plug in your own legal content for personalized assistance.

---

## ⚙️ How It Works

1. **Document Upload** – User provides legal documents (e.g., Constitution, IPC).
2. **Chunking & Embedding** – Backend converts documents into vector representations using embeddings.
3. **Semantic Retrieval** – When a query is submitted, relevant sections are retrieved using FAISS.
4. **Answer Generation** – Gemini AI generates a structured, legally informed response from retrieved content.

---

## 🛠️ Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/legalchat.git
cd legalchat

2. Backend Setup

cd backend
pip install -r requirements.txt

Create a .env file with your Gemini API key:
    GOOGLE_API_KEY=your_gemini_api_key


Start the backend server:
    uvicorn app.main:app --reload


3. Frontend Setup

cd ../frontend
streamlit run app.py


🧠 Tech Stack
FastAPI – API Framework for backend

Streamlit – Frontend UI

FAISS – Vector similarity search

Sentence Transformers – Document embeddings

Gemini AI – LLM for natural language response generation

📈 Future Enhancements
🔍 Hybrid search (keyword + semantic)

🗃️ Multi-document support

🧩 PDF/DOCX file ingestion

🔐 User authentication

📊 Analytics dashboard for admin



Developed with 🧠⚖️ by Shubham Paikrao
