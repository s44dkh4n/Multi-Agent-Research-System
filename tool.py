from langchain.tools import tool
from bs4 import BeautifulSoup
from tavily import TavilyClient
from rich import print
import requests
import os
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(api_key= os.getenv("TAVILY_API_KEY"))

### Search Tool
@tool
def search_tool(query: str) -> str :
    """This tool is used to Search up Topics and it returns the title and url"""

    response = tavily.search(query= query,max_results= 5)
    all_results = []
    for r in response["results"]:
        all_results.append(
            f"Title : {r['title']} \nUrl : {r['url']}\n"
        )
    return "\n-----\n".join(all_results)

### Scraper Tool
@tool
def scraper_tool(url: str) -> str:
    """This tool scrapes url for content and return the HTML Parsed Content"""
    try:
        resp = requests.get(url= url, timeout= 8, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script","style","nav","footer"]):
            tag.decompose()
        return soup.get_text(separator=" ",strip=True)[:3000]
    except Exception as e:
        return f"Url cannot be scraped : {e}"

