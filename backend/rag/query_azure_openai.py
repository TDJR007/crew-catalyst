import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Azure OpenAI config (from .env)
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv(
    "AZURE_OPENAI_API_VERSION",
    "2024-02-15-preview"
)

# Toggle streaming here
USE_STREAMING = True

# Hyperparameters (Azure-supported only)
TEMPERATURE = 0.5
MAX_TOKENS = 1024
TOP_P = 0.9

# Azure OpenAI client (singleton-style, cheap to reuse)
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
)

def query_azure_openai(prompt: str) -> str:

    print(f"☁️ Querying Azure OpenAI deployment: {AZURE_OPENAI_DEPLOYMENT}")
    print(f"\n\n🔸 Prompt:\n{prompt}\n")

    try:
        if USE_STREAMING:
            return _query_streaming(prompt)
        else:
            return _query_blocking(prompt)

    except Exception as e:
        print(f"❌ LLM Query Failed: {e}")
        return "ERROR"

def _query_blocking(prompt: str) -> str:
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=TOP_P,
    )

    return response.choices[0].message.content.strip()

def _query_streaming(prompt: str) -> str:
    stream = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=TOP_P,
        stream=True,
    )

    content = ""

    for chunk in stream:
        # Azure sometimes sends empty control chunks
        if not chunk.choices:
            continue

        choice = chunk.choices[0]

        # delta may exist without content
        delta = getattr(choice, "delta", None)
        if not delta:
            continue

        token = getattr(delta, "content", None)
        if token:
            content += token

    return content.strip()


if __name__ == "__main__":
    print(query_local_llm("List 5 uses of AI in finance."))
