from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import BaseCallbackHandler
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

class PipelineDebugHandler(BaseCallbackHandler):
    def on_chat_model_start(self, serialized, messages, **kwargs):
        logger.info("Model call started")

    def on_llm_end(self, response, **kwargs):
        logger.info("Model call finished")

    def on_llm_error(self, error, **kwargs):
        logger.error("Model call failed: %s", error)

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = (serialized or {}).get("name", "unknown")
        logger.info("Tool started: %s", tool_name)

    def on_tool_end(self, output, **kwargs):
        logger.info("Tool finished")

    def on_tool_error(self, error, **kwargs):
        logger.error("Tool failed: %s", error)


#creating base function
def run_reasearch_pipeline(topic: str) -> dict:
    state = {} #shared memory

    logger.info("Step 1/4: search agent started")
    started_at = time.perf_counter()

    try:
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [
                HumanMessage(
                    content=f"Find recent, reliable and detailed information about: {topic}"
                )
            ]},
        config={"callbacks": [PipelineDebugHandler()]},
    )

    except Exception:
        logger.exception("Step 1/4: search agent failed")
        raise

    logger.info(
        "Step 1/4: search agent completed in %.2f seconds",
        time.perf_counter() - started_at,
    )

    state["search_result"] = search_result["messages"][-1].content
    logger.info(
        "Step 1/4: saved search result (%d characters)",
        len(state["search_result"]),
    )
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


    #why choosing last 800 words? because all the links might be present there only
    
    #step 3 - writer chain 

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    #lets combine research and detailed scrapped research and send it to writer chain to 
    # get report
    research_combined = (
        f"SEARCH RESULTS : \n {state['search_result']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['reader_result']}"
    )

    #writer chain needs 2 val, so use dict{}
    #store in state dict
    state["report"] = writer_chain.invoke({
        "topic": topic, #this came as arg from run_research_pipeline
        "research": research_combined
    })
    print("\n Final Report\n",state['report'])

    #critic chain
    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\n critic report \n", state['feedback'])

    return state
       
if __name__ == "__main__":
    topic = input("\n Enter a research topic: ")
    run_reasearch_pipeline(topic)