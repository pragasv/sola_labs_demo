import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, VectorSearch, VectorSearchProfile,
    HnswAlgorithmConfiguration, VectorSearchAlgorithmKind, SearchField, SearchFieldDataType
)
from openai import OpenAI

load_dotenv()

# Azure OpenAI client (same as in your orchestrator)
oai = OpenAI(
    api_key=os.getenv("AZURE_FDRY_KEY"),
    base_url=os.getenv("AZURE_FDRY_ENDPOINT").rstrip("/") + "/openai/v1/"
)
embed_deployment = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")

# Determine embedding dimension programmatically
test_vec = oai.embeddings.create(model=embed_deployment, input="dimension check").data[0].embedding
EMBED_DIM = len(test_vec)

search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX")

index_client = SearchIndexClient(search_endpoint, AzureKeyCredential(admin_key))

index = SearchIndex(
    name=index_name,
    fields=[
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="text", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="title", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBED_DIM,
            vector_search_profile_name="vitaroute-profile",
        ),
    ],
    vector_search=VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="vitaroute-hnsw",
                kind=VectorSearchAlgorithmKind.HNSW
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vitaroute-profile",
                algorithm_configuration_name="vitaroute-hnsw"
            )
        ],
    )
)

index_client.create_or_update_index(index)
print("Created/updated index:", index_name, "dim=", EMBED_DIM)