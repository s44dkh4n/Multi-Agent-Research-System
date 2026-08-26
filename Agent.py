from tool import scraper_tool,search_tool
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

parser = StrOutputParser()
llm = ChatMistralAI(model_name= "mistral-large-latest",temperature=0.3)

def scraper_Agent():
    agent = create_agent(
        model= llm,
        tools= [scraper_tool]
    )
    return agent

def search_Agent():
    agent = create_agent(
        model= llm,
        tools= [search_tool]
    )
    return agent

writer_prompt = ChatPromptTemplate.from_messages([
    ("system","You are an expert research writer. Write clear, structured and insightful reports"),
    ("human","""Write a detailed research report on the topic below from the research gathered. 
     
    Topic : {topic} 
     
    Research Gathered : {research}  
    Report structure should be:
    - Introduction
    - Key Findings (atleast 5 well explained Points)
    - Conclusion
    - Sources (list the URLs found in research)

    Be Detailed and professional.
    """)
])

critic_prompt = ChatPromptTemplate.from_messages([
    ("system","You are a constructive research critic. be honest and specific."),
    ("human","""Review the below research report below and exaluate it
    Report : {report}

    Respond in the format below :

    Score : X/10

    Strengths: (minimum 3 strengths in bullet points)
    Areas to improve: ( minimum 3 strengths in bullet points)
    Verdict : (one line)
    """)
])

writer_chain = writer_prompt | llm | parser
critic_chain = critic_prompt | llm | parser