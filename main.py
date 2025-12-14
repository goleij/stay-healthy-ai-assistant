import os
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.chains import RetrievalQA

# ---- Paths ----
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(ROOT_DIR, "chroma_db")

# ---- Singletons / Caches ----
_embeddings = None
_vectordb = None
_qa_cache = {}

# avoid recreating embeddings instance multiple times
def _get_embeddings(model: str = None):
    """Embedder singleton."""
    global _embeddings
    if _embeddings is None:
        emb_model = model or os.getenv("EMBED_MODEL", "mxbai-embed-large")
        _embeddings = OllamaEmbeddings(model=emb_model)
    return _embeddings

# avoid recreating vectordb instance multiple times
def _get_vectordb():
    """Chroma singleton (persisted)."""
    global _vectordb
    if _vectordb is None:
        if not os.path.exists(DB_DIR):
            raise RuntimeError(
                f"Vector DB not found at '{DB_DIR}'. Run `python prepare_data.py` once to build it."
            )
        _vectordb = Chroma(persist_directory=DB_DIR, embedding_function=_get_embeddings())
    return _vectordb

# build and cache RAG chaines
def build_rag(
    model_name: str = "gemma2:2b",
    k: int = 2,
    temperature: float = 0.2,
    num_predict: int = 384,
    num_ctx: int = 2048,
):
    """Build a cached RAG chain using Ollama LLM and Chroma retriever."""
    key = (model_name, k, temperature, num_predict, num_ctx)
    if key in _qa_cache:
        return _qa_cache[key]

    retriever = _get_vectordb().as_retriever(search_kwargs={"k": k})

    llm = OllamaLLM(
        model=model_name,
        temperature=temperature,
        num_predict=num_predict,
        num_ctx=num_ctx,
    )

    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
    )

    _qa_cache[key] = rag_chain
    return rag_chain

# simple test when running this file directly
if __name__ == "__main__":
    qa = build_rag(model_name="gemma2:2b", k=2)
    question = "What are healthy foods for weight gain and weight loss?"
    result = qa({"query": question})
    print("🧠 Question:", question)
    print("💬 Answer:", result["result"])
    print("\n📚 Sources:")
    for doc in result["source_documents"][:3]:
        print("-", doc.metadata.get("source"))
