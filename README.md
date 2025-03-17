Peacy - The AI Mediator
=======================

Peacy is an AI-powered mediator designed for group chats. Built using Python, Peacy uses OpenAI’s language models (via the Groq API) to generate thoughtful, empathetic responses while maintaining a persistent memory of conversations using ChromaDB and PostgreSQL. Peacy is designed to listen to conversations, learn from interactions, and respond only when activated with a wake word (such as "Peacy", "PC", etc.)—all while growing its understanding of the community over time.

Features
--------

*   **Persistent Memory:**Peacy stores conversation data in a vector index using ChromaDB, so that previous interactions are remembered across restarts.
    
*   **Structured User Profiles:**Peacy uses PostgreSQL to store critical structured data (like user profiles) so that it can personalize responses without explicitly echoing that information.
    
*   **Dynamic Context-Aware Responses:**By integrating conversation history into the response prompt, Peacy generates smooth, context-aware replies.
    
*   **Wake Word Activation:**Peacy only responds when a wake word (e.g., “Peacy”, “PC”, “Peacccy”) is present in a message, ensuring it doesn’t interfere with every conversation.
    
*   **Background Tasks:**The bot periodically summarizes group chat conversations via background tasks.
    

Requirements
------------

See the requirements.txt file for the list of dependencies:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   textCopy codepython-telegram-bot  openai  chromadb  psycopg2-binary  sentence_transformers  APScheduler  rich  python-dotenv  nest_asyncio   `

Installation
------------

1.  bashCopy codegit clone https://github.com/yourusername/peacy.gitcd peacy
    
2.  bashCopy codepython -m venv venvsource venv/bin/activate # On Windows use \`venv\\Scripts\\activate\`
    
3.  bashCopy codepip install -r requirements.txt
    

Configuration
-------------

Create a .env file (or update your config.py file) with the following environment variables:

*   TELEGRAM\_TOKEN: Your Telegram bot API token.
    
*   GROQ\_API\_KEY: Your API key for the Groq (OpenAI) service.
    
*   PG\_CONNECTION\_STRING: The connection string for your PostgreSQL database (e.g., dbname=peacy\_db user=peacy\_admin password=admin host=localhost port=5432).
    
*   CHROMA\_PERSIST\_DIRECTORY: The folder where ChromaDB will persist the vector index (e.g., ./chroma\_db).
    

Example .env file:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   envCopy codeTELEGRAM_TOKEN=your_telegram_bot_token_here  GROQ_API_KEY=your_groq_api_key_here  PG_CONNECTION_STRING=dbname=peacy_db user=peacy_admin password=admin host=localhost port=5432  CHROMA_PERSIST_DIRECTORY=./chroma_db   `

Usage
-----

To run the bot, simply execute:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   bashCopy codepython bot.py   `

Peacy will:

*   Initialize the PostgreSQL database (creating tables for messages and user profiles if they don’t exist).
    
*   Seed the initial memory if the vector index is empty.
    
*   Start background tasks (e.g., conversation summarization).
    
*   Listen for messages that contain any of the specified wake words.
    
*   Update user profiles silently when users introduce themselves.
    
*   Generate smooth, context-aware responses based on conversation history.
    

Project Structure
-----------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   bashCopy codepeacy/  ├── bot.py                 # Main bot file (Telegram bot integration and core logic)  ├── config.py              # Configuration file for environment variables  ├── db_manager.py          # Database management: initializing and logging to PostgreSQL  ├── memory_manager.py      # Persistent memory handling with ChromaDB and SentenceTransformer  ├── background_tasks.py    # Background tasks (e.g., conversation summarization using APScheduler)  ├── requirements.txt       # Python package dependencies  └── README.md              # This file   `

Customization
-------------

*   **Response Generation:**You can modify the sync\_generate\_response function in bot.py to adjust the system prompt or the model parameters for different response styles.
    
*   **Memory & Profile Integration:**The bot silently updates and retrieves user profile data from PostgreSQL and integrates that into the memory context for responses. Adjust this logic in the handle\_message function as needed.
    
*   **Wake Words:**Update the WAKE\_WORDS list in bot.py to change the keywords that trigger Peacy.
    

Graceful Shutdown
-----------------

Peacy uses asynchronous programming with asyncio and nest\_asyncio for smooth operation. If you need to stop the bot, use Ctrl+C. The code attempts to handle shutdown gracefully, though you might see a message like "Cannot close a running event loop" if the event loop is still active. This is expected behavior during a forced shutdown.

License
-------

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.