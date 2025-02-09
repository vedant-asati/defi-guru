# Cell 1: Import required modules and load environment variables
import import_ipynb
import load_env
from load_env import *

# Import agent toolkit and initialize the CDP agent kit wrapper
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

# Import pretty print
from helpers import print_message_nicely

# Import custom actions
from approve_token import get_approve_token_tool
from increase_liquidity import get_increase_liquidity_tool
from mint_new_position import get_mint_new_position_tool

import os

load_dotenv()

# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"
# Configure CDP Agentkit Langchain Extension.
wallet_data = None

if os.path.exists(wallet_data_file):
    with open(wallet_data_file) as f:
        wallet_data = f.read()

values = {}

mnemonic_phrase = os.getenv("MNEMONIC_PHRASE")
if wallet_data is not None:
    # If there is a persisted agentic wallet, load it and pass to the CDP Agentkit Wrapper.
    # values = {"cdp_wallet_data": wallet_data}
    values = {"mnemonic_phrase": mnemonic_phrase}

cdp = CdpAgentkitWrapper(**values)

# persist the agent's CDP MPC Wallet Data.
wallet_data = cdp.export_wallet()
with open(wallet_data_file, "w") as f:
    f.write(wallet_data)

# Initialize CDP Agentkit Toolkit and get tools.    
toolkit = CdpToolkit.from_cdp_agentkit_wrapper(cdp)
tools_blockchain = toolkit.get_tools()

# Adding custom actions to the tools list
approve_token_tool = get_approve_token_tool(cdp)
mint_new_position_tool = get_mint_new_position_tool(cdp)
increase_liquidity_tool = get_increase_liquidity_tool(cdp)

tools_blockchain = tools_blockchain + [approve_token_tool, mint_new_position_tool, increase_liquidity_tool]

# Import LLM and create an instance using the Google GenAI model "gemini-2.0-flash"
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Import LangGraph’s helper to create react agents
from langgraph.prebuilt import create_react_agent

# Cell 2: Create our three agents

# Create the blockchain agent using the blockchain toolkit.
blockchain_agent = create_react_agent(llm, tools=tools_blockchain)

# For Twitter, use the ArcadeToolManager to load the X toolkit (assumes ARCADE_API_KEY is defined in the environment).
from langchain_arcade import ArcadeToolManager
tool_manager = ArcadeToolManager(api_key=ARCADE_API_KEY)
tools_twitter = tool_manager.get_tools(toolkits=["X"])
twitter_agent = create_react_agent(llm, tools=tools_twitter)

# Create the assistant agent.
# This agent’s sole work is to review the full conversation state and generate a confirmation or general query response.
# It no longer requires external internet access.
assistant_agent_prompt = (
    "You are an assistant agent whose job is to analyze the entire conversation state and, if a confirmation is needed, "
    "generate a concise confirmation message starting with 'Yes, please'. Otherwise, generate a helpful response to clarify "
    "or resolve any ambiguity."
)
assistant_agent = create_react_agent(llm, tools=[])  # No extra tools are needed.

# Cell 3: Define the supervisor's system prompt with explicit message naming and an example flow.
# The team now includes the assistant_agent.
members = ["blockchain_agent", "twitter_agent", "assistant_agent"]
options = members + ["FINISH"]

AGENT_CAPABILITIES = f"""
## Blockchain Agent Capabilities
- Deploy smart contracts (ERC20/ERC721)
- Manage crypto assets (ETH/USDC/NFT transfers)
- DeFi interactions (Morpho vault deposits/withdrawals)
- Price oracle queries (Pyth Network)
- Handle testnet faucet requests
- Uniswap add liquidity and mint new liquidity positions
- ERC20 token approvals

## Twitter Agent Capabilities
- Post tweets (requires authentication)
- Search recent tweets by keywords/username
- Lookup tweet details by ID
- Delete existing tweets
- User profile lookups

## Assistant Agent Capabilities
- Review the entire conversation state.
- Generate confirmation messages or clarifying responses when needed
- Produce responses starting with "Yes, please" when a confirmation is required.

## Routing Rules
1. Use 'twitter_agent' for any request containing: tweet, post, search, lookup, delete.
2. Use 'blockchain_agent' for: deploy, transfer, balance, deposit, withdraw, nft.
3. Use 'assistant_agent' to generate a confirmation or answer a general query when the supervisor is unsure.
4. FINISH after one complete operation unless the user requests multiple steps.
"""

system_prompt = f"""
You are a supervisor tasked with managing a conversation between the following workers: {members}. Their capabilities are: {AGENT_CAPABILITIES}.
Your job is to carefully review the entire conversation history and determine which worker should act next or whether the task is complete.

Important:

Message Source Distinction:
    The conversation history is structured so that the very first message is the original query from the human user.
    All subsequent messages are generated by AI agents.
    Only genuine human input (messages with name "User") is to be treated as confirmation.

Confirmation and Routing:
    If an action requires confirmation (for example, confirming that faucet ETH should be fetched or that a tweet should be posted) and no genuine user confirmation is present, route the query to the Assistant Agent.
    The Assistant Agent will then analyze the full conversation state and generate an appropriate confirmation message (e.g., "Yes, please fetch the price of ETH in USD." or "Yes, please post the tweet.").
    You are responsible for both routing the conversation and ensuring that confirmations come from the Assistant Agent.

Avoid Re-Routing:
    Once a confirmed action has been executed and a final result (e.g., the price of ETH or a posted tweet) is obtained, do not route the conversation back to the same agent.
    Instead, update the state with the result and, if no further action is needed, respond with FINISH.

Task Delegation:
    Delegate tasks only when additional work is required.
    If the current result fully addresses the request, instruct FINISH.

Example Flow for the Query "What is the price of ETH in USD and post it on Twitter?":

Step 1: User Query
    - The conversation begins with a single human message:
      User: "What is the price of ETH in USD and post it on Twitter?"

Step 2: Agent Response and Assistant-Generated Confirmation
    - The supervisor routes to the Blockchain Agent.
    - Blockchain Agent: "Sorry, I cannot post to Twitter. However, I can fetch the price of ETH in USD for you. Do you want me to do that?"
    - Since no genuine user confirmation is present, you (as the supervisor) route to the Assistant Agent.
    - Assistant Agent: "Yes, please fetch the price of ETH in USD."
    - Then, you route back to the Blockchain Agent.

Step 3: Blockchain Agent Executes the Task
    - Blockchain Agent (Follow-up): "The price of ETH is $2609.37."

Step 4: Routing to the Next Agent
    - The supervisor then routes to the Twitter Agent.
    - Twitter Agent: "I am sorry, I cannot get the price of ETH in USD. However, I can post a tweet to X(Twitter). Do you want to post a tweet?"
    - Again, if no genuine user confirmation is present, you route to the Assistant Agent.
    - Assistant Agent: "Yes, please post the tweet. The price of ETh is $2609.37"
    - Then, you route to the Twitter Agent to execute the tweet.

Step 5: Completion
    - Once the tweet is posted or an appropriate response is obtained, the supervisor updates the state and responds with FINISH.

Based on these rules and the example above, analyze the conversation history and respond with the next worker to act or with FINISH if the overall task is complete.
"""

# Cell 4: Define a pydantic model for the Router, the State type, and the supervisor_node function

from typing import Literal
from pydantic import BaseModel
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage

class Router(BaseModel):
    next: Literal["blockchain_agent", "twitter_agent", "assistant_agent", "FINISH"]

class State(MessagesState):
    next: str

def supervisor_node(state: State) -> Command[Literal["blockchain_agent", "twitter_agent", "__end__"]]:
    # Combine the system prompt with the conversation history
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    # print(f"State in supervisor: {state}")
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response.next
    print("\n")
    print(f"Routing to {goto}...")
    # print("."*50)
    # print("\n" + "."*50)
    if goto == "FINISH":
        goto = END
    return Command(goto=goto, update={"next": goto})

# Cell 5: Define nodes for the blockchain, twitter, and assistant agents.

def blockchain_node(state: State) -> Command[Literal["supervisor"]]:
    result = blockchain_agent.invoke(state)
    content = result["messages"][-1].content
    message = HumanMessage(content=content, name="blockchain_agent")
    print_message_nicely(message)
    return Command(
        update={
            "messages": [message],
            "next": "supervisor"
        },
        goto="supervisor",
    )

def twitter_node(state: State) -> Command[Literal["supervisor"]]:
    result = twitter_agent.invoke(state)
    content = result["messages"][-1].content
    message = HumanMessage(content=content, name="twitter_agent")
    print_message_nicely(message)
    return Command(
        update={
            "messages": [message],
            "next": "supervisor"
        },
        goto="supervisor",
    )

def assistant_node(state: State) -> Command[Literal["supervisor"]]:
    # Build a conversation context string from all messages.
    conversation_context = " ".join([msg.content for msg in state["messages"]])
    prompt = (
        f"Given the full conversation context: '{conversation_context}', "
        "if a confirmation is needed for the current action (e.g., fetching ETH, approving for erc20 token or posting a tweet), "
        "firstly infer from the context and user intent and then, if not clear,"
        "think about yourselves generate a concise confirmation message starting with 'Yes, please', Otherwise, provide your brief opinion to accomplish the task/goal."
    )
    # IMPORTANT: Pass the prompt under the 'contents' key as required.
    # result = llm.invoke({"contents": [prompt]})
    result = llm.invoke(prompt)
    content = result.content
    message = HumanMessage(content=content, name="assistant_agent")
    print_message_nicely(message)
    return Command(
        update={
            "messages": [message],
            "next": "supervisor"
        },
        goto="supervisor",
    )

# Cell 6: Build the conversation graph using LangGraph's StateGraph

from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
builder.add_node("supervisor", supervisor_node)
builder.add_node("blockchain_agent", blockchain_node)
builder.add_node("twitter_agent", twitter_node)
builder.add_node("assistant_agent", assistant_node)
builder.add_edge(START, "supervisor")

graph = builder.compile()

# # Optionally, display the graph using mermaid visualization
# from IPython.display import Image, display
# display(Image(graph.get_graph(xray=True).draw_mermaid_png()))

# Cell 7: Invoke the graph with a sample conversation

from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "1", "user_id": "user@example.com"}}

print("\n" + "="*50)
print("🤖 Welcome to DeFi Guru!".center(50))
print("="*50 + "\n")

# Get user input
user_message = input("Your message: ")
# initial_message = [HumanMessage(content=user_message, name="User")]

initial_message = [HumanMessage(content="help me earning money. i have 16 stk and 1 ved token. after completing the operations you can post a cool message on twitter about this and add the txn link with format: https://sepolia.basescan.org/tx/${txnhash}. Dont forget to provide the tweet url.", name="User")]
# initial_message = [HumanMessage(content="help me earning money. i have 10 stk and .1 ved token", name="User")]

# print_message_nicely(initial_message)

result_state = graph.invoke({"messages": initial_message}, config=config, stream_mode="values")

# Optional: Print end of conversation
print("\n" + "="*50)
print("Conversation Complete".center(50))
print("="*50 + "\n")

# Print the last few messages for clarity
# for m in result_state["messages"][-4:]:
#     m.pretty_print()

# print("\n....................")
# print("\n....................")
# print("result_state: ", result_state)

# Print the conversation nicely
# print_conversation_nicely(result_state["messages"])