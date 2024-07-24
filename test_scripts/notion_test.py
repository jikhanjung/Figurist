import os
from notion_client import Client


#https://www.notion.so/antarctictrilobites/a619f6b3d9fe4d588911ff1a7d0cd411?v=aa47b82fde2b4beaa52568d776c0526c&pvs=4

# Load the API key (best practice: use environment variables)
notion_token = "secret_o4yQHZiLjDz7vNUBc3hMu3UaA9zl6ERPTC0ApNBG32W" #os.getenv("NOTION_API_TOKEN")
database_id = "a619f6b3d9fe4d588911ff1a7d0cd411" #os.getenv("NOTION_DATABASE_ID")  # The ID of your Notion database

# Initialize the Notion client
notion = Client(auth=notion_token)

# Query the database 
results = notion.databases.query(database_id=database_id)

# Process the results (each item in `results` is a page in your database)
#for page in results.get("results#"):
#    print("Page Title:", page["properties"]["Title"]["title"][0]["text"]["content"])
    # Access other properties as needed (replace "Title" with the actual property name)

for page in results["results"]:
    print(page["properties"]["Name"]["title"][0]["text"]["content"])
    #print(page["properties"]["Date"]["date"]["start"])
    print(page["properties"]["Tags"]["multi_select"])
    #print(page["properties"]["URL"]["url"])
    #print(page["properties"]["File"]["files"])
    #print(page["properties"]["Notes"]["rich_text"])
    #print(page["properties"]["Authors"]["people"])
