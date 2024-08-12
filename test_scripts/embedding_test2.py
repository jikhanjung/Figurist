import chromadb
import requests
import numpy as np

# Function to get embeddings from Ollama
def get_ollama_embedding(text, model="nomic-embed-text"):
    response = requests.post("http://localhost:11434/api/embeddings", 
                             json={"model": model, "prompt": text})
    if response.status_code == 200:
        return response.json()['embedding']
    else:
        raise Exception(f"Error from Ollama API: {response.text}")

# Custom embedding function for ChromaDB
class OllamaEmbeddingFunction():
    def __call__(self, input: list[str]) -> list[list[float]]:
        return [get_ollama_embedding(text) for text in input]

# Initialize ChromaDB client
client = chromadb.Client()

# Create a collection with Ollama embedding function
ollama_ef = OllamaEmbeddingFunction()
collection = client.create_collection(name="bibliographic_entries", embedding_function=ollama_ef)

# Example bibliographic entries
entries = [
    "Smith, J. (2020). The impact of AI on society. Journal of AI Ethics, 5(2), 123-145.",
    "J. Smith. The impact of AI on society. J. AI Ethics, 2020, 5(2):123-145",
    "Smith, John. 'The Impact of AI on Society.' Journal of AI Ethics 5.2 (2020): 123-145.",
]

# Add entries to the collection
collection.add(
    documents=entries,
    ids=[f"id{i}" for i in range(len(entries))]
)

# Function to find most similar entry
def find_most_similar(query, n=1):
    results = collection.query(
        query_texts=[query],
        n_results=n
    )
    return results

# Example query
query = "Smith, J. The impact of AI on society. 2020. J. of AI Ethics."
similar_entries = find_most_similar(query)

print("\nMost similar to query:")
for i, (document, distance) in enumerate(zip(similar_entries['documents'][0], similar_entries['distances'][0])):
    print(f"{i+1}. {document}")
    print(f"   Similarity: {1 - distance:.4f}")  # Convert distance to similarity

# You can also add new entries easily
new_entry = "Johnson, A. (2021). Ethical considerations in AI development. Tech Ethics Review, 8(3), 78-92."
collection.add(
    documents=[new_entry],
    ids=["id" + str(len(entries))]
)

# And query again
print("\nAfter adding a new entry:")
similar_entries = find_most_similar(query, n=2)
for i, (document, distance) in enumerate(zip(similar_entries['documents'][0], similar_entries['distances'][0])):
    print(f"{i+1}. {document}")
    print(f"   Similarity: {1 - distance:.4f}")