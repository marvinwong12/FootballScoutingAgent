import os
import unicodedata
import chromadb
from chromadb.utils import embedding_functions

# 💡 Reuse your exact pipeline normalizer
def normalize_name(name):
    if not isinstance(name, str): return str(name)
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def initialize_vector_db():
    # 1. Point Chroma to a local folder inside your cache
    db_path = "./scout_cache/vector_db"
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # 2. Use a free, local embedding model
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # 3. Create or fetch the collection
    collection = chroma_client.get_or_create_collection(
        name="player_narratives", 
        embedding_function=embedding_fn
    )
    
    # 4. Read and ingest your mock files
    source_dir = "./scouting_reports"
    if not os.path.exists(source_dir):
        print(f"Directory {source_dir} not found!")
        return

    print("🚀 Vectorizing scouting reports into local storage...")
    
    for filename in os.listdir(source_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(source_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Map filename to a clean player name key
            # e.g., "benoit_badiashile.txt" -> "benoit badiashile"
            player_raw_name = filename.replace(".txt", "").replace("_", " ")
            player_key = normalize_name(player_raw_name)
            
            # Upsert into Chroma (Metadata allows filtering strictly by player name)
            collection.upsert(
                documents=[content],
                metadatas=[{"player_match_name": player_key}],
                ids=[player_key]
            )
            print(f"✅ Ingested narrative profile for: {player_key}")

if __name__ == "__main__":
    initialize_vector_db()