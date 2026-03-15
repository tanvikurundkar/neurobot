import os
import hashlib
import shutil
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

PERSIST_DIR = "./db"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

TEXT_PATHS = [
    "knowledge/trialtb.txt",
    # "knowledge/textbook.txt",  
]

# -------------------------------------------------------------------------------

def get_embeddings():
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)

def get_file_hash(path: str) -> str:
    return hashlib.md5(open(path, "rb").read()).hexdigest()

def get_combined_hash(text_paths: list[str]) -> str:
    return hashlib.md5(
        "".join(get_file_hash(p) for p in sorted(text_paths)).encode()
    ).hexdigest()

# -------------------------------------------------------------------------------

def db_is_valid(text_paths: list[str], persist_dir: str) -> bool:
    hash_file = os.path.join(persist_dir, ".source_hash")
    if not os.path.exists(persist_dir) or not os.path.exists(hash_file):
        return False
    return open(hash_file).read() == get_combined_hash(text_paths)

def get_curr_db(persist_dir: str = PERSIST_DIR) -> Chroma:
    """Load and return the existing DB from disk."""
    print(f"Loading existing DB from '{persist_dir}'...")
    return Chroma(persist_directory=persist_dir, embedding_function=get_embeddings())

# -------------------------------------------------------------------------------

def rebuild_db(text_paths: list[str], persist_dir: str = PERSIST_DIR) -> Chroma:
    """Wipe the existing DB and rebuild it from the given files."""
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
        print(f"Cleared old DB at '{persist_dir}'")

    all_chunks = []
    for path in text_paths:
        loader = TextLoader(path, encoding="utf-8")
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        print(f"  '{path}' → {len(chunks)} chunks")
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No chunks produced from any file — are they all empty?")

    embeddings = get_embeddings()
    if not embeddings.embed_query("test"):
        raise RuntimeError("Embedding model returned empty vector — check sentence-transformers install")

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )

    with open(os.path.join(persist_dir, ".source_hash"), "w") as f:
        f.write(get_combined_hash(text_paths))

    print(f"DB built — {len(all_chunks)} total chunks from {len(text_paths)} file(s)")
    return vectorstore

# -------------------------------------------------------------------------------

def query_db(vectorstore: Chroma, user_query: str, k: int = 4) -> None:
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(user_query)

    print(f"\nQuery: {user_query}")
    print(f"Top {k} results:\n" + "-" * 40)
    for i, doc in enumerate(docs, 1):
        print(f"[{i}] {doc.page_content[:300]}...")
        print(f"    Source: {doc.metadata.get('source', 'unknown')}\n")

# --------------------------------------------------------------------------------

if __name__ == "__main__":
    if db_is_valid(TEXT_PATHS, PERSIST_DIR):
        vs = get_curr_db()
    else:
        vs = rebuild_db(TEXT_PATHS)

    test_queries = [
        "What is the main topic of this textbook?",
        "Explain the key concepts in chapter one.",
        "I am feeling mentally unwell.",
        "What should i do if I feel suicidal?"
    ]
    for q in test_queries:
        query_db(vs, q)