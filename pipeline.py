from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import BaseCallbackHandler
from rich.console import Console 
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

console = Console()


def run_step(step_name, operation, *args, **kwargs):
    logger.info("%s started", step_name)
    started_at = time.perf_counter()

    try:
        with console.status(f"[cyan]{step_name} is running...[/cyan]"):
            result = operation(*args, **kwargs)
    except Exception:
        elapsed = time.perf_counter() - started_at
        logger.exception("%s failed after %.2f seconds", step_name, elapsed)
        raise

    elapsed = time.perf_counter() - started_at
    logger.info("%s completed in %.2f seconds", step_name, elapsed)
    return result

#creating base function
def run_research_pipeline(topic: str) -> dict:
    state = {}
    callbacks = [PipelineDebugHandler()]

    # Step 1: search
    search_agent = build_search_agent()
    search_result = run_step(
        "Step 1/4: Search agent",
        search_agent.invoke,
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Find recent, reliable and detailed information about: "
                        f"{topic}"
                    )
                )
            ]
        },
        config={"callbacks": callbacks},
    )

    state["search_result"] = search_result["messages"][-1].content
    logger.info(
        "Saved search result (%d characters)",
        len(state["search_result"]),
    )

    #when search_agent is invoked, internal loop run and return a list of msg
    #from that list the content of AI msg is our use, so only store that in search_res key

    #created a key called search_result inside empty state dict
 

    #now lets connect research agent to reader agent when deeply reads the link and fine tune our content
    # remember we never connected them earlier anywhere (tools or agent)
    # pipeline is used to conect everythin, earlier everything was independent

    # Use the search results to find and scrape the most relevant source.
    # Step 2: read a source from the search results
    reader_agent = build_reader_agent()
    reader_result = run_step(
        "Step 2/4: Reader agent",
        reader_agent.invoke,
        {
            "messages": [
                HumanMessage(
                    content=(
                        f"Based on the following search results about '{topic}', "
                        "pick the most relevant URL and scrape it for deeper content.\n\n"
                        f"Search Results:\n{state['search_result'][:800]}"
                    )
                )
            ]
        },
        config={"callbacks": callbacks},
    )

    state["reader_result"] = reader_result["messages"][-1].content

    #why choosing last 800 words? because all the links might be present there only
    
    #step 3 - writer chain 

    #lets combine research and detailed scrapped research and send it to writer chain to 
    # get report
    research_combined = (
        f"SEARCH RESULTS : \n {state['search_result']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['reader_result']}"
    )

    #writer chain needs 2 val, so use dict{}
    #store in state dict
    state["report"] = run_step(
        "Step 3/4: Writer",
        writer_chain.invoke,
        {
            "topic": topic,
            "research": research_combined,
        },
        config={"callbacks": callbacks},
    )
    # Step 4: critique the report
    state["feedback"] = run_step(
        "Step 4/4: Critic",
        critic_chain.invoke,
        {"report": state["report"]},
        config={"callbacks": callbacks},
    )

    print("\nFinal report\n")
    print(state["report"])

    print("\nCritic feedback\n")
    print(state["feedback"])

    return state