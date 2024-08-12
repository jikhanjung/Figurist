import chromadb
import requests
import re
from collections import defaultdict

def normalize_entry(entry):
    # Convert to lowercase
    entry = entry.lower()
    
    # Extract key elements: authors, title, year
    authors = re.findall(r'([a-z]+,?\s+[a-z]\.)', entry)
    authors = sorted([author.strip() for author in authors])
    
    title_match = re.search(r'(["\'])(.+?)\1', entry)
    title = title_match.group(2) if title_match else ""
    
    year_match = re.search(r'\b(19|20)\d{2}\b', entry)
    year = year_match.group(0) if year_match else ""
    
    # Combine key elements
    return f"{' '.join(authors)} {title} {year}".strip()

def get_ollama_embedding(text, model="nomic-embed-text"):
    response = requests.post("http://localhost:11434/api/embeddings", 
                             json={"model": model, "prompt": text})
    if response.status_code == 200:
        return response.json()['embedding']
    else:
        raise Exception(f"Error from Ollama API: {response.text}")

class OllamaEmbeddingFunction():
    def __call__(self, input: list[str]) -> list[list[float]]:
        return [get_ollama_embedding(normalize_entry(text)) for text in input]

client = chromadb.Client()
ollama_ef = OllamaEmbeddingFunction()
collection = client.create_collection(name="normalized_bibliographic_entries", embedding_function=ollama_ef)

# Example bibliographic entries
entries = [
    "Smith, J. (2020). The impact of AI on society. Journal of AI Ethics, 5(2), 123-145.",
    "J. Smith. The impact of AI on society. J. AI Ethics, 2020, 5(2):123-145",
    "Smith, John. 'The Impact of AI on Society.' Journal of AI Ethics 5.2 (2020): 123-145.",
    "Johnson, A. & Brown, B. (2019). Machine learning applications in healthcare. Medical AI Journal, 3(1), 45-60.",
]

# Add entries to the collection
for i, entry in enumerate(entries):
    print(f"Adding entry {i+1}...", entry)
    collection.add(
        documents=[entry],
        ids=[f"id{i}"]
    )

def find_similar_entries(query, n=2):
    results = collection.query(
        query_texts=[query],
        n_results=n
    )
    return results

# Example queries
queries = [
    "Smith, J. The impact of AI on society. 2020. J. of AI Ethics.",
    "Johnson, A. Machine learning in healthcare. 2019."
]

for query in queries:
    print(f"\nQuery: {query}")
    similar_entries = find_similar_entries(query)
    for i, (document, distance) in enumerate(zip(similar_entries['documents'][0], similar_entries['distances'][0])):
        print(f"{i+1}. {document}")
        print(f"   Similarity: {1 - distance:.4f}")

# Demonstrating deduplication
unique_entries = defaultdict(list)
for i, entry in enumerate(entries):
    normalized = normalize_entry(entry)
    unique_entries[normalized].append(f"id{i}")

print("\nUnique entries:")
for normalized, ids in unique_entries.items():
    print(f"Normalized: {normalized}")
    print(f"Original IDs: {', '.join(ids)}")
    print()