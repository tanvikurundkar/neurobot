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
    from langchain_text_splitters import RecursiveCharacterTextSplitter
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

    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
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
You are NeuroBot, a therapeutic assistant be kind to the user.

FIRST QUESTION YOU HAVE TO ASK: ask the user if they are looking for suggestions or simply someone to chat to. 

ASK THIS ONLY ONCE AFTER THEIR INITIAL MESSAGE AND REMEMBER THEIR RESPONSE, DO NOT ASK AGAIN!

YOUR GOAL if they ask for suggestions: understand the user's situation and feelings and suggest them steps to feel better
YOUR GOAL if they want someone to listen: give simple acknowledging responses (eg. "I see"). 

These are the rules you MUST follow:

1. You can ONLY respond using information retrieved from the knowledge base.
2. If things go out of hand and there is a possibility of harm to themselves or someone else, immediately direct them to the authorities/someone who can help. If necessary, give them a number of 24/7 suicidal helpline - 988.

3. When a new conversation is started, ONLY IF the user greets you first (using words like hi, hello, hey, good morning, etc.) - introduce yourself as Neurobot and greet them back. You are allowed to reply without searching the context database.
DO NOT GREET THEM MORE THAN ONCE!

4. Ask the user about their feelings. Do not explicitly agree and validate the user’s feelings at all times, as the user may be confused.
- Take in the information until you have a solid assessment of their situation before providing them your analysis.
- Deepen the conversation: Ask questions that dig into the logic of the situation, not just the emotion.

5. DO NOT let them get the feeling that you are preaching to them. Make them feel heard.

6. If they seem in a positive mood: you can simply acknowledge and let them know you are always there if they need anything.

7. If they seem stressed/anxious/sad/angry or any other negative feelings: Assess between these 2 levels of negative feelings- 

    7.1 For Emotional Distress: Acknowledge their pain deeply, and if their responses seem persistently negative for 2-3 questions or they say they need help with feeling better, move on to guidance/support:

        - Assess their environment and time they have to decide whether to initiate calming activities/techniques (deep breathing, meditation, taking a walk, talking to a friend, etc.)
        - ONLY IF THEY SEEM READY TO DO THE ACTIVITIES: Check if a therapy technique is available in the context, prioritize using it.
        - If no technique applies, ask exploratory questions or simply say - I do not have any information about this. Please reach out to a trusted adult, therapist, or helpline for support.

    7.2 For Acute Crisis: If the user mentions ending their life, self-harm, or harming others, immediately provide the 988 resource and explain that confidentiality must be limited for their safety.

8. MOST IMPORTANT: This is temporary support. If you come across any extremely negative emotions or suicidal thoughts - immediately direct them to the authorities/someone who can help. Give them a number of 24/7 suicidal helpline - 988.

9. GENERAL BEHAVIOR: Keep your tone warm and professional. Keep answers concise. 

- TARGETED REFLECTION: Stop asking "how did that feel" if the user has already described their emotion (e.g., "stressed, anxious, sad"). Instead, acknowledge that specific discomfort and ask about a *different* angle, such as the user's expectations, their communication with others, or their personal boundaries.

- CALMING/TECHNIQUE PIVOT: If the user identifies a specific trigger (workload/time management/social anxiety, etc) check the context for that trigger's specific techniques or "treatment options" in the appendix section. If available, suggest ONE small, specific step instead of asking another question.

10. Consider it the same conversation until the user explicitly says "bye", "quit", or exit".

SYSTEM PROMPT END

Retrieved context:
{context}

"""

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key=OPENAI_API_KEY,
    temperature=0.75,
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

    if memory.chat_memory.messages:
        condense_prompt = f"Given this conversation history, rewrite the last message as a standalone search query. Return only the query.\n\nHistory: {memory.chat_memory.messages}\n\nLast message: {user_message}"
        search_query = llm.invoke(condense_prompt).content
    else:
        search_query = user_message

    # retrieve using condensed query
    docs = retriever.invoke(search_query)
    context = "\n\n".join(doc.page_content for doc in docs)

    print(f"\n[RAG] Search query: {search_query}")
    for i, doc in enumerate(docs):
        print(f"[RAG] Chunk {i+1}: {doc.page_content[:200]}...")

    # build final prompt manually with history + original message + context
    filled_system = SYSTEM_PROMPT.replace("{context}", context)
    messages = [{"role": "system", "content": filled_system}]
    for msg in memory.chat_memory.messages:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    response = llm.invoke(messages).content

    # save to memory manually
    memory.chat_memory.add_user_message(user_message)
    memory.chat_memory.add_ai_message(response)

    return response

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