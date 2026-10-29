from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
#to create chain we need import prompt tem
from langchain_core.prompts import ChatPromptTemplate
#outout parser
from langchain_core.output_parsers import StrOutputParser
from tool import web_search, scrape_url
import os
from dotenv import load_dotenv

load_dotenv()

#model setup
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0,  #for serious replies
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# create 1st agent for searching
def build_search_agent():
    """ uses tavily to search content"""
    return create_agent(
        model=llm,
        tools=[web_search]
    )

#create 2nd agent for reading url
def build_reader_agent():
    """ uses beautifulsoup python lib to scrape the url given by tavily"""
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )

#lets create chain
#we call it chain but in real its runnable only

# writer chain 
""" uses model LCEL pipe syntax which takes all research and writes a full
    full report. prompt | llm | stroutputparser()
"""
write_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = write_prompt | llm | StrOutputParser()
#when you invoke writer chain, in writer_prompt you will have to give 2 values
#{topic} and {research}


# critic chain
""" again uses LCEL pipe which reads the report and gives
    a score and a feedback.
 """
critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
#critic prompt has a placevalue holder 'report' which comes from build_search_agent