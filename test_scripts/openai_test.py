
import logging
import openai
import ssl
import httpx
# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create a logger for OpenAI
openai_logger = logging.getLogger("openai")
openai_logger.setLevel(logging.DEBUG)

   
from openai import OpenAI, APIError, Timeout, RateLimitError, APIConnectionError
from decouple import config
import os

# Set your API key
api_key = config("OPENAI_KEY")  # Or use your method of storing the key
client = OpenAI(api_key=api_key,http_client=httpx.Client(verify=False))

try:
    # List models
    models = client.models.list()
    print("Connection successful")
    print("Available models:", [model.id for model in models.data])
except APIConnectionError as e:
    print(f"API Connection Error: {e}")
    print(f"Network error details: {e.request}")
except Timeout as e:
    print(f"Request timed out: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except APIError as e:
    print(f"API error occurred: {e}")
    print(f"HTTP status: {e.status}")
    print(f"Error code: {e.code}")
    print(f"Error message: {e.message}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

