import chromadb
import requests
import re
from collections import defaultdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

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

# Extended list of bibliographic entries
entries = [
    "Smith, J. (2020). The impact of AI on society. Journal of AI Ethics, 5(2), 123-145.",
    "J. Smith. The impact of AI on society. J. AI Ethics, 2020, 5(2):123-145",
    "Smith, John. 'The Impact of AI on Society.' Journal of AI Ethics 5.2 (2020): 123-145.",
    "Johnson, A. & Brown, B. (2019). Machine learning applications in healthcare. Medical AI Journal, 3(1), 45-60.",
    "Lee, C., & Park, D. (2021). Natural language processing in legal tech. Computational Law Review, 8(3), 201-220.",
    "Garcia, M.R. (2018). Blockchain technology and its potential in education. Journal of Educational Technology, 12(4), 332-350.",
    "Wilson, E.T., & Thompson, K.L. (2022). The ethics of autonomous vehicles. Transportation Ethics Quarterly, 7(1), 15-32.",
    "Brown, B., Johnson, A., & Smith, J. (2023). A comprehensive review of AI in healthcare. Annual Review of Medical AI, 2, 78-105.",
    "Chen, Y. (2017). Deep learning algorithms for image recognition. Computer Vision Journal, 29(2), 187-205.",
    "Anderson, R.J., & Davis, S.T. (2019). Cybersecurity in the age of IoT. Network Security Today, 14(3), 98-112.",
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

# Extended list of example queries
queries = [
    "Smith, J. The impact of AI on society. 2020. J. of AI Ethics.",
    "Johnson, A. Machine learning in healthcare. 2019.",
    "Lee, C. Natural language processing and legal technology. 2021.",
    "Garcia, M. Blockchain in education. 2018.",
    "Wilson, E. Ethics of self-driving cars. 2022.",
    "Chen, Y. Deep learning for image recognition. 2017.",
    "Anderson, R. IoT and cybersecurity challenges. 2019.",
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

# Calculate pairwise distance matrix
def calculate_pairwise_distance_matrix(entries):
    embeddings = [get_ollama_embedding(normalize_entry(entry)) for entry in entries]
    similarity_matrix = cosine_similarity(embeddings)
    distance_matrix = 1 - similarity_matrix
    return distance_matrix

distance_matrix = calculate_pairwise_distance_matrix(entries)

print("\nPairwise Distance Matrix:")
print("  ", end="")
for i in range(len(entries)):
    print(f"{i:4d}", end="")
print()
for i, row in enumerate(distance_matrix):
    print(f"{i:2d}", end="")
    for value in row:
        print(f"{value:.2f}", end=" ")
    print()

# Print entry index and corresponding entry
print("\nEntry Index Reference:")
for i, entry in enumerate(entries):
    print(f"{i}: {entry}")