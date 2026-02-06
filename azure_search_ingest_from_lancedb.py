import os
import uuid
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import OpenAI
import lancedb

load_dotenv()

oai = OpenAI(
    api_key=os.getenv("AZURE_FDRY_KEY"),
    base_url=os.getenv("AZURE_FDRY_ENDPOINT").rstrip("/") + "/openai/v1/"
)
embed_deployment = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY"))
)

# Load LanceDB table
db = lancedb.connect("data/lancedb")
table = db.open_table("docling")
df = table.to_pandas()   # contains 'text' and 'metadata' (your current structure)

batch = []
for i, row in df.iterrows():
    text = row["text"]
    md = row.get("metadata", {}) or {}
    source = md.get("url") or md.get("filename") or "unknown"
    title = md.get("title") or ""

    emb = oai.embeddings.create(model=embed_deployment, input=text).data[0].embedding

    batch.append({
        "id": str(uuid.uuid4()),
        "text": text,
        "source": source,
        "title": title,
        "embedding": emb
    })

    if len(batch) >= 100:
        search_client.upload_documents(batch)
        batch = []

if batch:
    search_client.upload_documents(batch)

print("Done uploading.")