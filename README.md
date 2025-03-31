# BioticV1

BioticV1 is an intelligent AI assistant that provides contextual answers based on your custom documentation. Built with Discord integration, it allows you to interact with your documents through natural conversation, making information retrieval more intuitive and accessible.

## Features
- 🤖 Discord bot interface for easy interaction
- 📚 Custom document ingestion and processing
- 🔍 Semantic search capabilities
- 💬 Natural language querying
- 📄 Support for multiple document formats

## How to use
- setup the python local env `python -m venv venv`
- activate local env `source venv/bin/activate` 
- install requirements `pip install -r requirement.txt`
- Get discord token from the [developer site](https://discord.com/developers/application) and paste in the `.env` file as `DISCORD_BOT_TOKEN`
- Add the bot to your test server
- Get the links of document(s) and paste it in `urls` list in the `htmlToPdf.py`
- run `python htmlToPdf.py` to convert the links to pdfs which get saved in /pdfs dir
- Now, its time to chunk, embed and save doc in chromadb... run `python Ingest.py` 
- wait for some minute and and after chuck is done, start your chat app `python chat.py`

To recap, this is a 3 step installation
- Provide Links to `htmToPdf.py`
- Ingestion to the db
- Spawn up AI bot


