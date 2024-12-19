Develop the project below

# Purpose and Features
- AI content webscraping agent.
- Will be integrated into a custom CMS to gather and store content to my CMS database.
- The webscraper will receive commands and instructions all in natural language.
- If the AI is tasked with gathering content that doesn't appear in the given URL, it will search the web or generate the content itself.
- The agent can engage the user in dialogue, for example to tell them to take actions, such as with provide a iMessage passcode for two-factor authentication, question the user, or receive commands by the user.
- Image recognition for image-type content fields, e.g. logos for company content-type

# Stack
- Pydantic AI for framework
    - Type-safe and structure response validation so LLM output conforms to expected data structure
    - Dependency injection for customization of proxy behavior & evaluation-driven development
    - Model agnostic architecture to support any LLM
    - Streaming response processing to process and validate streaming responses in real-time, including structured data validation during streaming (viz. for table output or storage to Cassandra DB)
    - Implementation example at https://pub.towardsai.net/pydantic-ai-web-scraper-llama-3-3-python-powerful-ai-research-agent-6d634a9565fe
- Nodriver for Web Scraping
    - Use for detailed content extraction of authenticated or dynamic websites 
    - Documentation: https://ultrafunkamsterdam.github.io/nodriver/nodriver/quickstart.html
    - Handle authentication and login processes with credential providing
    - Element interaction within pages
    - Manage dynamic content through asynchronous operations
    - If site has cookies, grab cookies and pass them into a request session, to impersonate whilst loading the cookies from the browser that have been gathered into the session object
    - Stealth capabilities for protected content
- Tavily for Web Searching
    - Initial URL discovery
    - Researching tasks
    - Aggregate multiple sites
    - Implementation example at https://pub.towardsai.net/pydantic-ai-web-scraper-llama-3-3-python-powerful-ai-research-agent-6d634a9565fe
    - Requires Tavily API key
- Llama-3.3-70B-Instruct
    - Main LLM
    - Dynamic webscraping and web searching
    - Identifies content to gather
    - Generates content
    - Navigates page to take actions (e.g. click on see more button or go to next page)
    - Dialogue with user    
    - Implementation example at https://pub.towardsai.net/pydantic-ai-web-scraper-llama-3-3-python-powerful-ai-research-agent-6d634a9565fe
    - Gated model, so requires HF access token
- Llama-3.2-11B-Vision-Instruct
    - Image processing for image recognition tasks
    - Text recognition from images
    - Gated model, so requires HF access token
- Cassandra
    - Database
- Synergies:
    - Combine Nodriver and Tavily for...
        - A robust content gathering solution where Tavily will be used for search and discovery, and Nodriver will be used for deep scraping of protected or dynamic content
        - Example use case: Tavily discovers multiple URLs to scrape, and Nodriver will scrape these sites
    - Combine llama 3.3 and Google Vision AI for complete content processing, where llama 3.3 is used in text-based tasks and content generation, and google vision AI will be used for image content-type extraction
    - Combine Pydantic AI with Cassandra for structured data handling

# Deployment
- GitHub remote repo at https://github.com/jshinodea/content_gatherer
- Entire project is a docker container which I will use as a microservice
- Will build, run, and test the container on a rented GPU from vast.ai

# Frontend
- Simple UI where user provides their instructions to the agent
- Tavily key and HF access token are provided in the frontend UI in text boxes
- After user clicks button to start the task, a dialogue UI box is opened for the agent to engage the user in dialogue
- Gathered content is outputted as a table where the user can double left-click cells to manually change them, or shift + left-click to highlight cells, then the user can click a button to provide the LLM instructions on how to modify the highlighted cells.
- Button to accept table, which stores it in Cassandra DB

# Prompts
- When generating a prompt, use prompt engineering best practices found at https://cloud.google.com/discover/what-is-prompt-engineering, specifically set clear goals and objectives, provide context and background info, include few-shot examples, be specific, and include chain of thought reasoning pathways in the prompt.

---

# Use Case
    1. In a UI with one text box, the user will provide a URL and content gathering specifications (i.e. what content to gather or generate) in natural language as one prompt.
    2. When I enter the inputs, a chatbot dialogue box is opened in the UI, where the agent may ask the user questions or validation check with the user. 
    3. The agent will scrape from the provided URL, or may search the web on URL's not provided by the user, in order to gather information for the requested content, e.g. research each company and generate a description on their mission
    4. If the chatbot finds that a login is required, it may ask me to provide one in the dialogue box. 
    5. After all content is gathered or generated, the output will be content structured as a table.
    6. If the table's content meets the user's expectations, then they can confirm the table, which stores it to my CMS database.

# Example Use Case
    1. User input: "Scrape {Aggie Experts URL} using the following login info {CAS login username and password}. Once on the main page, gather the following information from the Grants section: title, award recipient, award giver, and description. Also for each grant, find a company or brand logo representing the award giver."
    2. The dialogue UI is opened. The agent recognizes the Grants section, and a "See All Grants" button, so it clicks this and sees all 39 grants. Each grant will represent the row in the output DB, with the following fields for each grant: title, award recipient, award giver, description, and logo. 
    3. The agent has no questions right now, so it begins performing its task.
    4. Agent has issue so tells user in dialogue box the following: "I am unable to find the award giver and description information."
    5. User responds with "Click on the title of each grant to get award giver information on it. For the description, generate a concise three sentence description of the award."
    6. The agent will then follow the new instructions by clicking on the grant for its award giver info and researching each grant on the web to learn about it, then generate a description. For the first description generated, the agent outputs it to the user to see if it meets expectations.
    7. Then all fields are filled for all grants and the table for the grants content-type is outputted to the user. The user can highlight specific cells and prompt the agent on them, for example if revisions or modifications should be made.
    8. The user is satisfied and sends the table to the database to be stored.

# Important
- Analyze and understand .cursorrules first
- Document the necessary info in development_log.md as you develop
- After development...
    - Tell me how to push to the remote repo at @https://github.com/jshinodea/content_retriever 
    - Tell me how to run this project as a docker container using a GPU instance on vast.ai