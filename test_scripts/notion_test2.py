import os
from notion_client import Client
import requests
from decouple import config

#https://www.notion.so/antarctictrilobites/a619f6b3d9fe4d588911ff1a7d0cd411?v=aa47b82fde2b4beaa52568d776c0526c&pvs=4
#https://www.notion.so/antarctictrilobites/Fig-06-2-Gen-et-Sp-indet-A-12bc4623627049838b100fa1899ee783?pvs=4
# Load the API key (best practice: use environment variables)
notion_token = config('NOTION_TOKEN') #"" #os.getenv("NOTION_API_TOKEN")
database_id = "a619f6b3d9fe4d588911ff1a7d0cd411" #os.getenv("NOTION_DATABASE_ID")  # The ID of your Notion database

# Initialize the Notion client
notion = Client(auth=notion_token)

# Query the database 
results = notion.databases.query(database_id=database_id)

for page in results["results"]:
    page_id = page["id"]
    page_title = page["properties"]["Name"]["title"][0]["text"]["content"]
    print(f"Searching for image in page: {page_title}")

    # Get all blocks in the page
    blocks = notion.blocks.children.list(block_id=page_id)

    for block in blocks["results"]:
        if block["type"] == "image":
            image_url = block["image"]["file"]["url"]
            print(f"Found image: {image_url}")
            # Here you can download the image if needed
        elif block["type"] == "file":
            file_url = block["file"]["file"]["url"]
            print(f"Found file: {file_url}")
        # download and save image using the page_title as the filename
        response = requests.get(image_url)
        if response.status_code == 200:
            with open("./download/" +page_title + ".png", "wb") as f:
                f.write(response.content)
            print(f"Downloaded {page_title}.png")

        

    print("---")


exit()
for page in results["results"]:


    print(page["properties"]["Name"]["title"][0]["text"]["content"])
    for key in page.keys():
        print(key, page[key])
    #print(page.keys())
    for key in page["properties"].keys():
        print(key, page["properties"][key])
    #print(page["properties"].keys())
    #for key in page["properties"].keys():
    #    print(page["propertieskey)
    #print(page["properties"].keys())
    continue
    image_property = page["properties"]["Image"]  # Replace "Image" with your image property name

    if image_property["type"] == "files":
        for image_file in image_property["files"]:
            image_url = image_file["file"]["url"]
            image_name = page["properties"]["Name"]["title"][0]["text"]["content"] + ".jpg"  # Or the file extension you need
            response = requests.get(image_url)

            if response.status_code == 200:
                with open(image_name, "wb") as f:  # Save image to file
                    f.write(response.content)
                print(f"Downloaded {image_name}")
            else:
                print(f"Error downloading image from {image_url}")
    else:
        print(f"No image found for {page['properties']['Name']['title'][0]['text']['content']}")