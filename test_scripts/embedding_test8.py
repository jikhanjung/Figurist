import requests
import re

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
    try:
        response = requests.post("http://172.16.116.98:11434/api/embeddings", 
                                 json={"model": model, "prompt": text})
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Content: {response.text[:100]}...")  # Print first 100 chars
        if response.status_code == 200:
            result = response.json()
            embedding = result.get('embedding')
            if embedding:
                return embedding, len(embedding)
            else:
                print(f"Warning: Empty embedding returned. Full response: {result}")
                return None, 0
        else:
            print(f"Error from Ollama API: {response.text}")
            return None, 0
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama API: {e}")
        return None, 0

def diagnose_query(query):
    print(f"\nDiagnosing query: {query}")
    print(f"Query length: {len(query)} characters")
    
    normalized_query = normalize_entry(query)
    print(f"Normalized query: {normalized_query}")
    print(f"Normalized query length: {len(normalized_query)} characters")
    
    embedding, embedding_length = get_ollama_embedding(normalized_query)
    if embedding:
        print(f"Successfully generated embedding of length {embedding_length}")
    else:
        print("Failed to generate embedding")
    
    print("\nTrying without normalization:")
    embedding, embedding_length = get_ollama_embedding(query)
    if embedding:
        print(f"Successfully generated embedding of length {embedding_length}")
    else:
        print("Failed to generate embedding")

# Example usage
test_queries = [
    "Smith, J. (2020). The impact of AI on society.",
    "Machine learning in healthcare",
    "Nakamoto Bitcoin 2008",
    "Journal of Labor Economics, 2022",
    "A very short query"
]

for query in test_queries:
    diagnose_query(query)
    print("-" * 50)