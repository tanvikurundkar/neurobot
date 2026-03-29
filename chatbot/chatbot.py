"""
NeuroBot - LangChain RAG Chatbot
Converted from n8n NeuroTech workflow

Requirements:
    pip install langchain langchain-openai langchain-pinecone pinecone-client google-api-python-client python-dotenv

Environment variables (.env):
    OPENAI_API_KEY=...
    PINECONE_API_KEY=...
    PINECONE_INDEX_NAME=neurotech2
    GOOGLE_DRIVE_FOLDER_ID=1P3Ps3H9tGHXQlrQuQJmEbOzus_IRlDsi   # for ingestion only
    GOOGLE_CREDENTIALS_JSON=...                                   # for ingestion only
"""
"""google credentials json not given!!!!"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# 1.  Shared clients
# ─────────────────────────────────────────────
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

OPENAI_API_KEY    = os.environ["OPENAI_API_KEY"]
PINECONE_API_KEY  = os.environ["PINECONE_API_KEY"]
INDEX_NAME        = os.getenv("PINECONE_INDEX_NAME", "neurotech2")
MODEL_NAME        = os.getenv("OPENAI_MODEL", "gpt-4o-mini")   # n8n used gpt-5-mini (likely a typo); swap if needed

pc = Pinecone(api_key=PINECONE_API_KEY)

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

vector_store = PineconeVectorStore(
    index=pc.Index(INDEX_NAME),
    embedding=embeddings,
)

# ─────────────────────────────────────────────
# 2.  Optional: Ingest Google Drive → Pinecone
#     (mirrors the manual-trigger ingestion pipeline)
# ─────────────────────────────────────────────
def ingest_google_drive(folder_id=None) -> None:
    """
    Download files from a Google Drive folder and embed them into Pinecone.
    Requires: google-api-python-client, google-auth, langchain-community
    Set GOOGLE_CREDENTIALS_JSON to your service-account JSON path.
    """
    folder_id = folder_id or os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise ValueError("Provide a GOOGLE_DRIVE_FOLDER_ID env var or argument.")

    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    import tempfile, io

    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_CREDENTIALS_JSON"],
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    drive = build("drive", "v3", credentials=creds)

    # List files in folder
    results = drive.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
    ).execute()
    files = results.get("files", [])
    print(f"Found {len(files)} file(s) to ingest.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    all_docs = []

    for file in files:
        fid, fname, mime = file["id"], file["name"], file["mimeType"]
        print(f"  Downloading {fname} …")
        request = drive.files().get_media(fileId=fid)
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = dl.next_chunk()
        buf.seek(0)

        suffix = ".pdf" if "pdf" in mime else ".txt"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(buf.read())
            tmp_path = tmp.name

        loader = PyPDFLoader(tmp_path) if suffix == ".pdf" else TextLoader(tmp_path)
        docs = loader.load()
        chunks = splitter.split_documents(docs)
        all_docs.extend(chunks)
        os.unlink(tmp_path)

    if all_docs:
        vector_store.add_documents(all_docs)
        print(f"Ingested {len(all_docs)} chunk(s) into Pinecone index '{INDEX_NAME}'.")
    else:
        print("No documents to ingest.")


# ─────────────────────────────────────────────
# 3.  RAG chatbot  (mirrors the AI Agent pipeline)
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """SYSTEM PROMPT START
You are NeuroBot, a therapeutic assistant that can ONLY respond using information retrieved from the knowledge base.

GREETING BEHAVIOR (IMPORTANT EXCEPTION TO RAG RULES)
If the user greets you (hi, hello, hey, good morning, etc.), you are allowed to reply without searching.
Respond politely and ALWAYS introduce yourself once as NeuroBot.
Do NOT activate refusal rules for greetings.
Only apply strict RAG rules after the conversation starts.

NON-NEGOTIABLE RULES
You MUST base your entire answer ONLY on the retrieved context provided below.
You MUST quote the relevant retrieved text before giving your answer.
If the retrieved context does not contain the answer, you MUST refuse.
You are forbidden from using outside knowledge, assumptions, reasoning, therapeutic expertise, CBT concepts, or mental health knowledge unless the retrieved text explicitly contains it.

REFUSAL RULE
If relevant information is missing, respond ONLY with:
"I DON'T HAVE THE ANSWER. The knowledge base does not contain the information needed. Please reach out to a trusted adult, therapist, or helpline for support."
Do not add anything else.

SELF-CHECK
Before sending any answer, check:
- Is every sentence grounded in the retrieved context?
- Is no outside information added?
If ANY part violates this, replace your answer with the refusal template.

GENERAL BEHAVIOR
Keep your tone warm and professional.
Keep answers concise.
SYSTEM PROMPT END

Retrieved context:
{context}
"""

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key=OPENAI_API_KEY,
    temperature=0.3,
)

memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer",
    k=10,  # keep last 10 turns (matches n8n Simple Memory buffer window)
)

retriever = vector_store.as_retriever(search_kwargs={"k": 4})

combine_docs_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template("{question}"),
])

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    combine_docs_chain_kwargs={"prompt": combine_docs_prompt},
    return_source_documents=False,
    verbose=False,
)

GREETING_KEYWORDS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy", "sup"}

def is_greeting(text: str) -> bool:
    return text.strip().lower().split()[0] in GREETING_KEYWORDS if text.strip() else False

def chat(user_message: str) -> str:
    """Send a message and get NeuroBot's response."""
    if is_greeting(user_message) and not memory.chat_memory.messages:
        # First message is a greeting → bypass RAG (matches n8n GREETING BEHAVIOR)
        return "Hello! I'm NeuroBot, your therapeutic assistant. How can I support you today?"

    result = qa_chain.invoke({"question": user_message})
    return result["answer"]


# ─────────────────────────────────────────────
# 4.  Interactive CLI  (replaces n8n chat trigger)
# ─────────────────────────────────────────────
def run_cli():
    print("=" * 60)
    print("  NeuroBot — Therapeutic Assistant")
    print("  Type 'quit' or 'exit' to end the session.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "bye"}:
            print("NeuroBot: Take care. Goodbye!")
            break

        response = chat(user_input)
        print(f"\nNeuroBot: {response}")


# ─────────────────────────────────────────────
# 5.  Optional FastAPI server
#     Run with: uvicorn neurobot:app --reload
# ─────────────────────────────────────────────
try:
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="NeuroBot API")

    class Message(BaseModel):
        message: str
        session_id: str = "default"   # extend with per-session memory for multi-user

    @app.post("/chat")
    def chat_endpoint(body: Message):
        reply = chat(body.message)
        return {"reply": reply}

    @app.get("/health")
    def health():
        return {"status": "ok"}

except ImportError:
    app = None  # FastAPI not installed — CLI only


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        # python neurobot.py ingest [optional_folder_id]
        fid = sys.argv[2] if len(sys.argv) > 2 else None
        ingest_google_drive(fid)
    else:
        run_cli()