import os
import pickle
import chromadb

# Read paths from environment variables
CHROMA_DB_DIR = os.environ.get("CHROMA_DB_DIR")
PKL_DIR = os.environ.get("PKL_DIR")

if not CHROMA_DB_DIR or not PKL_DIR:
    raise RuntimeError(
        "Environment variables CHROMA_DB_DIR and PKL_DIR must be set"
    )

print("Using Chroma DB dir:", CHROMA_DB_DIR)
print("Reading PKLs from :", PKL_DIR)

client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

BATCH_SIZE = 1024  # safe default

for fname in sorted(os.listdir(PKL_DIR)):
    if not fname.endswith(".pkl"):
        continue

    collection_name = fname[:-4]
    print(f"\n=== Creating collection: {collection_name} ===")

    with open(os.path.join(PKL_DIR, fname), "rb") as f:
        items = pickle.load(f)

    documents = items["documents"]
    metadatas = items["metadatas"]
    embeddings = items["embeddings"]

    if not (len(documents) == len(metadatas) == len(embeddings)):
        raise RuntimeError(
            f"Length mismatch in {fname}: "
            f"{len(documents)=}, {len(metadatas)=}, {len(embeddings)=}"
        )

    # Make sure collection is clean
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(collection_name)

    total = len(documents)
    print(f"Items to add: {total}")

    for i in range(0, total, BATCH_SIZE):
        j = min(i + BATCH_SIZE, total)

        collection.add(
            documents=documents[i:j],
            metadatas=metadatas[i:j],
            embeddings=embeddings[i:j],
            ids=[f"{collection_name}_{k}" for k in range(i, j)],
        )

        if i % (BATCH_SIZE * 20) == 0:
            print(f"  added {j}/{total}")

print("\n✅ Rebuild completed successfully")
print("Collections:", [c.name for c in client.list_collections()])
