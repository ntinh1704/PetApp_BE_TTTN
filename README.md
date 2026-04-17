# 🐾 Pet App Backend API (Khoa Luan Tot Nghiep)

This is the backend repository for the Pet App project (Khóa luận tốt nghiệp). It provides RESTful APIs built with **FastAPI**, managing data with **PostgreSQL**, and integrating advanced features like an **AI Chatbot** using **Langchain** and **FAISS**.

## 🚀 Technologies Used

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL with [SQLAlchemy](https://www.sqlalchemy.org/) (ORM) & psycopg2
- **Data Validation**: Pydantic
- **Authentication**: JWT (JSON Web Tokens) with PyJWT and bcrypt
- **AI/Chatbot Integration**: Langchain, Google Generative AI (Gemini), Sentence-Transformers, FAISS
- **Server**: Uvicorn

## 📁 Project Structure

```bash
📦 KLTN_BE
 ┣ 📂 controller     # Handles business logic and processing requests
 ┣ 📂 crud           # Database CRUD (Create, Read, Update, Delete) operations
 ┣ 📂 db             # Database connection and session management
 ┣ 📂 router         # API route definitions
 ┣ 📂 schemas        # Pydantic models for request/response validation
 ┣ 📂 setting        # Configuration and environment variables
 ┣ 📂 faiss_index    # Local vector database for AI chatbot 
 ┣ 📂 uploads        # Uploaded files and media
 ┣ 📜 main.py        # Application entry point
 ┣ 📜 scheduler.py   # Background tasks scheduling (e.g., auto-cancel bookings)
 ┣ 📜 ingest_data.py # Script for ingesting data into the vector database
 ┣ 📜 requirements.txt # Project dependencies
 ┗ 📜 .env           # Environment configuration (ignored in version control)
```

## 🛠️ Installation & Setup

1. **Clone the repository** (or navigate to the folder):
   ```bash
   cd KLTN_BE
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up Environment Variables**:
   Create a `.env` file in the root directory and add the necessary configurations:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/dbname
   SECRET_KEY=your_secret_key
   # Add other required API keys (e.g., Google Gemini API key, email settings)
   ```

## 🏃 Running the Application

To start the FastAPI development server, run:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- The API will be accessible at: `http://localhost:8000`
- Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API Documentation (ReDoc): `http://localhost:8000/redoc`

## 🤖 AI Chatbot Setup

To update or ingest the custom knowledge base for the AI Chatbot via FAISS:
```bash
python ingest_data.py
```
This script reads the data (e.g., `knowledge.txt` / `hdsd.txt`) and generates vector embeddings stored in the `faiss_index` directory.

## 🤝 Contribution

This backend was built as part of a Graduation Thesis (Khóa luận tốt nghiệp). Code modifications should be made strictly following the `controller` -> `crud` -> `router` software architecture pattern established in the project.
