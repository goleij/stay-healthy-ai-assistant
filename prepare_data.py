import os
from glob import glob

from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# ---- Paths ----
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
DB_DIR = os.path.join(ROOT_DIR, "chroma_db")

def load_documents():
    """Load data from PDFs, CSVs, text files, and URLs."""
    docs = []

    if not os.path.isdir(DATA_DIR):
        print(f"⚠️ data directory not found: {DATA_DIR}")
        return docs

    # PDFs, CSVs, TXT/MD
    for path in glob(os.path.join(DATA_DIR, "*")):
        if path.lower().endswith(".pdf"):
            try:
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
                print(f"Loaded PDF: {os.path.basename(path)}")
            except Exception as e:
                print("PDF load error:", path, e)
        elif path.lower().endswith((".csv",)):
            try:
                loader = CSVLoader(path)
                docs.extend(loader.load())
                print(f"Loaded CSV: {os.path.basename(path)}")
            except Exception as e:
                print("CSV load error:", path, e)
        elif path.lower().endswith((".txt", ".md")):
            try:
                loader = TextLoader(path, encoding="utf-8")
                docs.extend(loader.load())
                print(f"Loaded text: {os.path.basename(path)}")
            except Exception as e:
                print("Text load error:", path, e)

    # URLs from urls.txt (one URL per line)
    urls_file = os.path.join(DATA_DIR, "urls.txt")
    if os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as fh:
            for line in fh:
                url = line.strip()
                if not url:
                    continue
                try:
                    loader = WebBaseLoader(url)
                    docs.extend(loader.load())
                    print(f"Loaded URL: {url}")
                except Exception as e:
                    print("URL load error:", url, e)

    print(f"✅ Total documents loaded: {len(docs)}")
    return docs

def split_documents(docs):
    """Split documents into smaller chunks for embedding."""
    if not docs:
        return []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"✅ Split into {len(chunks)} chunks")
    return chunks

def create_vector_db(chunks):
    """Create persistent Chroma vector database with Ollama embeddings."""
    os.makedirs(DB_DIR, exist_ok=True)
    if not chunks:
        print("⚠️ No chunks to index.")
        return

    # choose embedding model (env override possible)
    emb_model = os.environ.get("OLLAMA_EMBEDDING_MODEL", "gemma2:2b")
    try:
        embeddings = OllamaEmbeddings(model=emb_model)
    except Exception as e:
        print(f"Failed to init OllamaEmbeddings with model '{emb_model}': {e}")
        raise

    vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory=DB_DIR)
    try:
        vectordb.persist()
    except Exception:
        pass
    print(f"✅ Chroma DB created/updated at: {DB_DIR}")
    return vectordb

def main():
    docs = load_documents()
    if not docs:
        print(f"⚠️ No documents found in {DATA_DIR}. Please add files or URLs.")
        return
    chunks = split_documents(docs)
    create_vector_db(chunks)

if __name__ == "__main__":
    main()
