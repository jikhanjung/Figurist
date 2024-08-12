import requests
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def normalize_entry(entry):
    entry = entry.lower()
    authors = re.findall(r'([a-z]+,?\s+[a-z]\.)', entry)
    authors = sorted([author.strip() for author in authors])
    title_match = re.search(r'(["\'])(.+?)\1', entry)
    title = title_match.group(2) if title_match else ""
    year_match = re.search(r'\b(19|20)\d{2}\b', entry)
    year = year_match.group(0) if year_match else ""
    return f"{' '.join(authors)} {title} {year}".strip()

def get_ollama_embedding(text, model="nomic-embed-text"):
    response = requests.post("http://172.16.116.98:11434/api/embeddings", 
                             json={"model": model, "prompt": text})
    if response.status_code == 200:
        embedding = response.json()['embedding']
        if not embedding:
            print(f"Warning: Empty embedding returned for text: {text}")
            return None
        return embedding
    else:
        print(f"Error from Ollama API: {response.text}")
        return None

class BibliographicDatabase:
    def __init__(self):
        self.entries = []
        self.embeddings = []

    def add_entry(self, entry):
        normalized_entry = normalize_entry(entry)
        embedding = get_ollama_embedding(normalized_entry)
        if embedding is not None:
            self.entries.append(entry)
            self.embeddings.append(embedding)
            print(f"Added entry with embedding of length {len(embedding)}")
        else:
            print(f"Failed to add entry: {entry}")

    def find_similar_entries(self, query, n=2):
        query_embedding = get_ollama_embedding(normalize_entry(query))
        if query_embedding is None or not self.embeddings:
            print("Unable to perform similarity search due to missing embeddings.")
            return []
        
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        top_indices = similarities.argsort()[-n:][::-1]
        results = []
        for idx in top_indices:
            results.append({
                "document": self.entries[idx],
                "similarity": similarities[idx]
            })
        return results

    def get_distance_matrix(self):
        if not self.embeddings:
            print("No embeddings available to calculate distance matrix.")
            return None
        return 1 - cosine_similarity(self.embeddings)

# Extended list of 20 bibliographic entries
entries = [
    "Smith, J. (2020). The impact of AI on society. Journal of AI Ethics, 5(2), 123-145.",
    "Johnson, A. & Brown, B. (2019). Machine learning applications in healthcare. Medical AI Journal, 3(1), 45-60.",
    "Lee, C., & Park, D. (2021). Natural language processing in legal tech. Computational Law Review, 8(3), 201-220.",
    "Garcia, M.R. (2018). Blockchain technology and its potential in education. Journal of Educational Technology, 12(4), 332-350.",
    "Wilson, E.T., & Thompson, K.L. (2022). The ethics of autonomous vehicles. Transportation Ethics Quarterly, 7(1), 15-32.",
    "Brown, B., Johnson, A., & Smith, J. (2023). A comprehensive review of AI in healthcare. Annual Review of Medical AI, 2, 78-105.",
    "Chen, Y. (2017). Deep learning algorithms for image recognition. Computer Vision Journal, 29(2), 187-205.",
    "Anderson, R.J., & Davis, S.T. (2019). Cybersecurity in the age of IoT. Network Security Today, 14(3), 98-112.",
    "Taylor, M.L. (2020). Quantum computing: A new era of computation. Quantum Information Processing, 15(4), 267-289.",
    "Lopez, S., & Kim, J. (2021). The role of big data in smart cities. Urban Technology Review, 6(2), 178-195.",
    "Williams, P.R. (2018). Augmented reality in education: A systematic review. Educational Technology Research, 22(1), 45-63.",
    "Harris, E.M., & Clark, T.B. (2022). The future of work: AI and automation. Journal of Labor Economics, 40(3), 312-330.",
    "Nakamoto, S. (2008). Bitcoin: A peer-to-peer electronic cash system. Decentralized Business Review, 21000(1), 1-9.",
    "Turing, A.M. (1950). Computing machinery and intelligence. Mind, 59(236), 433-460.",
    "Hawking, S.W. (1988). A brief history of time: From the big bang to black holes. Bantam Dell Publishing Group.",
    "Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep learning. MIT Press.",
    "Kurzweil, R. (2005). The singularity is near: When humans transcend biology. Viking.",
    "O'Neil, C. (2016). Weapons of math destruction: How big data increases inequality and threatens democracy. Crown.",
    "Harari, Y.N. (2015). Sapiens: A brief history of humankind. Harper.",
    "Tegmark, M. (2017). Life 3.0: Being human in the age of artificial intelligence. Knopf."
]

# Create and populate the database
db = BibliographicDatabase()
for i, entry in enumerate(entries):
    print(f"Adding entry {i+1}...", entry)
    db.add_entry(entry)

# Calculate pairwise distance matrix
distance_matrix = db.get_distance_matrix()

if distance_matrix is not None:
    print("\nPairwise Distance Matrix:")
    print("  ", end="")
    for i in range(len(db.entries)):
        print(f"{i:4d}", end="")
    print()
    for i, row in enumerate(distance_matrix):
        print(f"{i:2d}", end="")
        for value in row:
            print(f"{value:.2f}", end=" ")
        print()

# Print entry index, corresponding entry, and embedding
print("\nEntry Index, Entry, and Embedding:")
for i, (entry, embedding) in enumerate(zip(db.entries, db.embeddings)):
    print(f"\n{i}: {entry}")
    print(f"Embedding (first 10 dimensions): {embedding[:10]}")
    print(f"Embedding shape: {len(embedding)}")

# Perform some example queries
example_queries = [
    "Impact of artificial intelligence on society",
    "Machine learning in healthcare applications",
    "Blockchain technology in education",
    "Ethics of self-driving cars",
    "Quantum computing advancements"
]

print("\nExample Queries:")
for query in example_queries:
    print(f"\nQuery: {query}")
    similar_entries = db.find_similar_entries(query, n=3)
    for i, result in enumerate(similar_entries):
        print(f"{i+1}. {result['document']}")
        print(f"   Similarity: {result['similarity']:.4f}")