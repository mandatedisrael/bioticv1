import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from models import Models
from langchain.chains import create_retrieval_chain


# Load environment variables from .env file
load_dotenv()

models = Models()
embeddings = models.embeddings_ollama
llm = models.model_ollama

vector_store = Chroma(
    collection_name="documents",
    embedding_function=embeddings,
    persist_directory="./db/chroma_db"
)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful and friendly Symbiotic assistant. Your responses should vary based on the type of message received:

1. For greetings (hello, hi, good morning, etc.):
   - Respond with a friendly greeting appropriate to the time of day
   - Don't attempt to provide information from the context

2. For acknowledgments (thank you, ok, thanks, etc.):
   - Respond with a brief acknowledgment (e.g., "You're welcome!" or "Glad I could help!")
   - Don't attempt to provide information from the context

3. For questions or information requests:
   - Answer directly and confidently based on the retrieved CONTEXT
   - Add additional relevant details like link if available
   - Don't make up answers or use knowledge beyond the retrieved context
   - If the context doesn't contain relevant information, state that you don't have that information
     
IMPORTANT: NEVER state what type of message you think you're responding to. Just give the appropriate response directly.
IMPORTANT: Dont mention the context or codebase provided!"""),
    ("human", """You are an assistant who uses simple, clear and natural human language expressively for question-answering tasks. Use the following pieces of retrieved context to answer the question expressively. If you don't know the answer, just say that you don't know.  Remember not to mention anything relating to the context abd if the message is just a greeting or acknowledgement, just respond naturally
Question: {input} 
Context: {context} 
Answer:""")])

retriever = vector_store.as_retriever(kwargs={"k":10})
combine_docs_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

# User Conversation State
class ConversationState(TypedDict):
    messages: List[BaseMessage]
    user_id: int
    max_messages: int

# Memory Management Class
class UserMemoryManager:
    def __init__(self, max_messages=10):
        self.user_memories = {}
        self.max_messages = max_messages

    def add_message(self, user_id: int, message: BaseMessage):
        # Initialize user memory if not exists
        if user_id not in self.user_memories:
            self.user_memories[user_id] = []
        
        # Add message to user's memory
        self.user_memories[user_id].append(message)
        
        # Trim messages if exceeding max
        if len(self.user_memories[user_id]) > self.max_messages:
            self.user_memories[user_id] = self.user_memories[user_id][-self.max_messages:]
        
        return self.user_memories[user_id]

    def get_user_history(self, user_id: int) -> List[BaseMessage]:
        return self.user_memories.get(user_id, [])

# Create User Memory Manager
user_memory_manager = UserMemoryManager()

# LangGraph Workflow for Conversational AI
def create_conversational_graph():
    def initialize(state: ConversationState):
        # Initial state setup
        # @todo Check if user exists in chromadb, get the top messsages, user_id
        return {"messages": [], "user_id": state.get('user_id', 0), "max_messages": 10}

    def generate_response(state: ConversationState):
        # Combine context from memory and current conversation
        # @todo Get user load  messages from chromadb and use in addition to the current message so AI can remember the current user
        lastMessage = user_memory_manager.get_user_history(state['user_id'])
        
        # # Prepare messages with context
        # state['messages'] == current ques/message from discord
        messages = lastMessage + state['messages']
    
        # # Generate response using LLM
        # response = llm.invoke(messages)
        
        try:
            # Invoke the retrieval chain
            if messages and len(messages) > 0:
                last_message_content = messages[-1].content
            else:
                last_message_content = ""
            result = retrieval_chain.invoke({"input": last_message_content})
            # Send the answer
            response = result["answer"]
        # Return updated state with new AI message
            return {"messages": [AIMessage(content=response)]}
        except Exception as e:
            # @todo handle the error and return the error in a well formatted way
            print(f"Error generating response: {e}")
            pass


    # Define the graph workflow ( GRAPH )
    workflow = StateGraph(ConversationState)
    workflow.add_node("initialize", initialize)
    workflow.add_node("generate", generate_response)
    
    # Define edges
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "generate")
    workflow.add_edge("generate", END)
    
    # Compile the graph
    return workflow.compile()

# Create the conversational graph
conversational_graph = create_conversational_graph()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Respond to all messages in channels (except DMs and threads)
    if message.guild and not message.author.bot:
        # Remove any bot mentions from the message content
        query = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        # Send a typing indicator
        async with message.channel.typing():
            try:
                # Prepare conversation state
                user_message = HumanMessage(content=query)
                
                # Add message to user's memory
                # @todo add this to the chromadb and check if doesnt exceed the max messages
                user_memory_manager.add_message(message.author.id, user_message)
                
                # Prepare state for the graph
                initial_state = {
                    "messages": [user_message],
                    "user_id": message.author.id
                }
                
                # Run the conversational graph
                result = await asyncio.to_thread(
                    conversational_graph.invoke, 
                    initial_state
                )
                
                # Get the AI response
                response = result['messages'][-1].content
                
                # Add AI response to user's memory
                # @todo Add this to the chromadb and check if doesnt exceed the max messages
                ai_response = AIMessage(content=response)
                user_memory_manager.add_message(message.author.id, ai_response)
                
                # Discord has a message length limit of 2000 characters
                if len(response) > 2000:
                    # Split long responses into multiple messages
                    first_message = await message.reply(response[:2000], mention_author=False)
                    for i in range(2000, len(response), 2000):
                        await first_message.reply(response[i:i+2000], mention_author=False)
                else:
                    await message.reply(response, mention_author=False)
            
            except Exception as e:
                await message.reply(f"An error occurred: {str(e)}", mention_author=False)

def main():
    """Main function to run the Discord bot"""
    # Retrieve the token from environment variable
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # Check if token is set
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set in .env file.")
        print("Please ensure your .env file contains: DISCORD_BOT_TOKEN=your_token_here")
        return
    
    # Run the bot
    bot.run(TOKEN)

if __name__ == "__main__":
    main()