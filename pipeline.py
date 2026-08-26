from Agent import critic_chain, writer_chain, scraper_Agent, search_Agent


def research_pipeline(topic: str, status_callback=None) -> dict:
    """
    Runs the full multi-agent research pipeline: Search -> Scrape -> Write -> Critique.

    status_callback: optional callable(str) invoked with short progress messages
    at each stage boundary. Purely additive — the CLI entry point below still
    works exactly as before if it's left as None.
    """

    def notify(message: str):
        if status_callback:
            status_callback(message)

    state = {}

    print("\n", " = " * 43)
    print("Starting Search Agent...")
    notify("Starting Search Agent...")

    search_agent = search_Agent()
    search_resp = search_agent.invoke({
        # Fixed: Passed valid message dictionary schema with 'role' and 'content' keys
        "messages": [{"role": "user", "content": f"Find recent reliable news on the following topic.\n Topic: {topic}"}]
    })

    state["Search Response"] = search_resp['messages'][-1].content
    notify("Search Agent finished.")

    print("\n", " = " * 43)
    print("Starting Scraper Agent...")
    notify("Starting Scraper Agent...")

    scraper_agent = scraper_Agent()
    scrape_response = scraper_agent.invoke({
        # Using tuple representation ("user", "content") is also valid in LangChain
        "messages": [("user", f""" Based on the following search results about topic : {topic}
                                    pick the most relevant URL and scrape it for deeper content.
                                    Search Results: {state["Search Response"]}
                                    """)]
    })

    # Fixed: Extracted content from 'scrape_response' dict instead of calling index on 'scraper_agent'
    state["Scraped Response"] = scrape_response["messages"][-1].content
    notify("Scraper Agent finished.")

    # Fixed: Corrected state key typo from 'Search Respone' to 'Search Response'
    combined_research = (
        f"Searched Results: \n {state['Search Response']}\n"
        f"Scraped Results: \n {state['Scraped Response']}"
    )

    notify("Writing report...")
    state["Report"] = writer_chain.invoke({
        "topic": topic,
        "research": combined_research
    })
    notify("Report drafted.")

    notify("Running critic review...")
    state["Feedback"] = critic_chain.invoke({
        "report": state["Report"]
    })
    notify("Critic review complete.")

    return state


if __name__ == "__main__":
    result = research_pipeline(topic="What are the latest Developments in AI?")

    print("\n" + "=" * 50)
    print("SEARCH RESULTS")
    print("=" * 50)
    print(result.get("Search Response", "No search response found."), "\n")

    print("=" * 50)
    print("SCRAPED CONTENT")
    print("=" * 50)
    print(result.get("Scraped Response", "No scraped response found."), "\n")

    print("=" * 50)
    print("GENERATED REPORT")
    print("=" * 50)
    print(result.get("Report", "No report generated."), "\n")

    print("=" * 50)
    print("CRITIC FEEDBACK")
    print("=" * 50)
    print(result.get("Feedback", "No feedback generated."))