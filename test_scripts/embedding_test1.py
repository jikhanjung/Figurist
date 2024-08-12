import httpx
from huggingface_hub import HfApi, HfFolder
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import os

import warnings

# Suppress insecure request warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
# Load pre-trained model (you might want to fine-tune this on bibliographic data)
#tokenizer = AutoTokenizer.from_pretrained("allenai/specter")
#model = AutoModel.from_pretrained("allenai/specter")
client = httpx.Client(verify=False)
def custom_prepare_request(self, method, url, headers=None, data=None, files=None, **kwargs):
    headers = headers or {}
    kwargs["headers"] = headers
    return client.request(method, url, data=data, files=files, **kwargs)

HfApi._prepare_request = custom_prepare_request

model_path = "./local_models/specter"
tokenizer_path = "./local_models/specter"

# Check if model is already downloaded
if not os.path.exists(model_path):
    print("Downloading model for the first time...")
    tokenizer = AutoTokenizer.from_pretrained("allenai/specter")
    model = AutoModel.from_pretrained("allenai/specter")
    
    # Save model and tokenizer locally
    os.makedirs(model_path, exist_ok=True)
    model.save_pretrained(model_path)
    tokenizer.save_pretrained(tokenizer_path)
else:
    print("Loading model from local storage...")



# Load model and tokenizer from local path
#tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
#model = AutoModel.from_pretrained(model_path)

try:
    tokenizer = AutoTokenizer.from_pretrained("allenai/specter")
    model = AutoModel.from_pretrained("allenai/specter")
    print("Model and tokenizer loaded successfully!")
except Exception as e:
    print(f"An error occurred: {str(e)}")

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

# Example bibliographic entries
entries = [
    "Smith, J. (2020). The impact of AI on society. Journal of AI Ethics, 5(2), 123-145.",
    "J. Smith. The impact of AI on society. J. AI Ethics, 2020, 5(2):123-145",
    "Smith, John. 'The Impact of AI on Society.' Journal of AI Ethics 5.2 (2020): 123-145.",
    "Smith J. The impact of AI on society. Journal of AI Ethics. 2020;5(2):123-145."
]

# Get embeddings for all entries
embeddings = [get_embedding(entry) for entry in entries]

# Compare similarities
for i in range(len(entries)):
    for j in range(i+1, len(entries)):
        similarity = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
        print(f"Similarity between entry {i+1} and entry {j+1}: {similarity:.4f}")

# Function to find most similar entry
def find_most_similar(query, entries, embeddings):
    query_embedding = get_embedding(query)
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    most_similar_index = similarities.argmax()
    return entries[most_similar_index], similarities[most_similar_index]

# Example query
query = "Smith, J. The impact of AI on society. 2020. J. of AI Ethics."
most_similar_entry, similarity = find_most_similar(query, entries, embeddings)
print(f"\nMost similar to query:\n{most_similar_entry}\nSimilarity: {similarity:.4f}")