# llm_utils.py
import streamlit as st
import ollama
from main import build_rag  # your existing RAG builder

# create and cache Ollama LLM instances just once per model
@st.cache_resource
def get_llm(model_name: str):
    """Return an Ollama LLM with fixed settings."""
    from langchain_ollama import OllamaLLM
    return OllamaLLM(
        model=model_name,
        temperature=0.3,
        num_ctx=4096,
        num_predict=1200
    )

# list available local Ollama models
def list_local_models():
    """List locally available Ollama models."""
    try:
        data = ollama.list()
        models = [m["model"] for m in data.get("models", [])]
        priority = {
            "gemma2:2b": 0,
        }
        models.sort(key=lambda x: priority.get(x, 99))
        return models
    except Exception:
        return []

# get or create RAG QA chain for a model
def get_qa(model_name: str):
    """Get or create RAG QA chain for a model."""
    if "qa_by_model" not in st.session_state:
        st.session_state.qa_by_model = {}
    if model_name not in st.session_state.qa_by_model:
        st.session_state.qa_by_model[model_name] = build_rag(
            model_name=model_name,
            k=2,
        )
    return st.session_state.qa_by_model[model_name]
