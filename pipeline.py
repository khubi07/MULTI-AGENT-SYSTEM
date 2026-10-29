from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from langchain_core.messages import HumanMessage

#creating base function
def run_reasearch_pipeline(topic: str) -> dict:
    state = {} #shared memory

    #search agent working 
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [HumanMessage(content=f"Find recent, reliable and detailed information about: {topic}")]
    })

    #when search_agent is invoked, internal loop run and return a list of msg
    #from that list the content of AI msg is our use, so only store that in search_res key

    #created a key called search_result inside empty state dict
    state["search_result"] = search_result['messages'][-1].content

    print("\n search reuslt ",state['search_result'])

    #now lets connect research agent to reader agent when deeply reads the link and fine tune our content
    # remember we never connected them earlier anywhere (tools or agent)
    # pipeline is used to conect everythin, earlier everything was independent

    # Use the search results to find and scrape the most relevant source.
    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [HumanMessage(
            content=(
                f"Based on the following search results about '{topic}', "
                "pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_result'][:800]}"
            )
        )]
    })
    state["reader_result"] = reader_result['messages'][-1].content

    return state

    #why choosing last 800 words? because all the links might be present there only
    
