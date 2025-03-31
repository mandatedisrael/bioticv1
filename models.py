import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings


class Models:
    def __init__(self):

        self.embeddings_ollama = OllamaEmbeddings(
            model="mxbai-embed-large"
        )
        
        self.model_ollama = ChatOllama(
            model="llama3.2",
            temperature=0
        )

        # self.embeddings_openai= AzureOpenAIEmbeddings(
        #     model="text-embedding-3-large",
        #     dimensions=1536,
        #     azure_endpoint=os.environ.get("AZURE_OPENAI_EMBEDDINGS_ENDPOINT"),
        #     api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        #     api_version=os.environ.get("AZURE_OPENAI_EMBEDDINGS_API_VERSION"),
        # )

        # self.model_openai = AzureChatOpenAI(
        #     azure_deployment=os.environ.get("AZURE_OPENAI_API_DEPLOYMENT_NAME"),
        #     api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
        #     temperature=0,
        #     max_tokens=none,
        #     timeout=none,
        #     max_retries=2
        # )