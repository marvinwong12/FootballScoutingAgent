import os
import uuid
import chromadb
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import PromptTemplate  # Modern import path
from langchain_google_genai import ChatGoogleGenerativeAI  # Swapped to Gemini

load_dotenv()

# Safety fallback: map your key if it's saved under GOOGLE_API_KEY
if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

# Force a manual bypass write to verify the tool's writing pipeline
print("Connecting to local ChromaDB cache...")
chroma_client = chromadb.PersistentClient(path="./scout_cache/vector_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_or_create_collection(name="player_narratives", embedding_function=embedding_fn)

# Target configuration
player_name = "Mohamed Salah"
clean_name = "mohamed salah"

print(f"Scraping live web data for {player_name}...")
search = DuckDuckGoSearchResults(max_results=4)
raw_web_data = search.run(f"{player_name} football character leadership injury history")

print("Invoking Gemini to synthesize scouting intelligence...")
# Initialize Gemini using the efficient flash model
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

prompt = PromptTemplate(
    input_variables=["player_name", "web_context"],
    template="Write a concise 4-sentence qualitative intelligence profile for {player_name}. Focus on leadership, temperament, and physical robustness based on this context:\n{web_context}"
)

# Run the chain
generated_dossier = (prompt | llm).invoke({"player_name": player_name, "web_context": raw_web_data}).content

print(f"\n--- GENERATED REPORT ---\n{generated_dossier}\n------------------------\n")

# Force insert into database
print("Caching report to ChromaDB...")
collection.add(
    documents=[generated_dossier],
    metadatas=[{"player_match_name": clean_name, "original_name": player_name}],
    ids=[str(uuid.uuid4())]
)

print("✅ Manual patch successful. Try querying your agent about Mohamed Salah again!")