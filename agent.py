# Cell 1: Import required modules and load environment variables
import import_ipynb
import load_env
from load_env import *

# Import agent toolkit and initialize the CDP agent kit wrapper
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

# Import pretty print
from helpers import print_message_nicely, ASCII_ART

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
    values = {"cdp_wallet_data": wallet_data}
else:
    # If there is no persisted wallet, pass the mnemonic phrase to the CDP Agentkit Wrapper.
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
from langgraph.checkpoint.memory import MemorySaver

# Store buffered conversation history in memory.
memory = MemorySaver()

# Cell 2: Create our three agents

# Create the blockchain agent using the blockchain toolkit.
blockchain_agent = create_react_agent(llm, tools=tools_blockchain, checkpointer=memory)

# For Twitter, use the ArcadeToolManager to load the X toolkit (assumes ARCADE_API_KEY is defined in the environment).
from langchain_arcade import ArcadeToolManager
tool_manager = ArcadeToolManager(api_key=ARCADE_API_KEY)
tools_twitter = tool_manager.get_tools(toolkits=["X"])
twitter_agent = create_react_agent(llm, tools=tools_twitter, checkpointer=memory)

# Create the assistant agent.
# This agent’s sole work is to review the full conversation state and generate a confirmation or general query response.
# It no longer requires external internet access.
assistant_agent_prompt = (
    "You are an assistant agent whose job is to analyze the entire conversation state and, if a confirmation is needed, "
    "generate a concise confirmation message starting with 'Yes, please'. Otherwise, generate a helpful response to clarify "
    "or resolve any ambiguity."
)
assistant_agent = create_react_agent(llm, tools=[], checkpointer=memory)  # No extra tools are needed.

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
4. FINISH after one complete operation unless the user requests multiple steps. Except when the blockchain agent successfully completes a task, then route to the twitter_agent for posting the tweet.
"""

system_prompt = f"""
You are a supervisor of a DeFi portfolio manager(DeFi Guru) bot tasked with managing a conversation between the following workers: {members}. Their capabilities are: {AGENT_CAPABILITIES}.
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
    If the current result does not require further action, do not re-route the conversation to the same agent. Instead, update the state with the result and, if no further action is needed, respond with FINISH.
    For actions performed by the blockchain agent, if the result is a success, need to post the result on Twitter, for this you need to route to the assistant_agent for confirmation and more details. And when sufficient information is present route to the twitter_agent for posting the tweet.
    

Task Delegation:
    Delegate tasks only when additional work is required. 
    If the current result fully addresses the request, instruct FINISH.

General Assistance:
    If the human user is asking for general assistance or information, and no specific action is required, you can respond directly with the answer and respond with FINISH.
    Examples: 
        1. If users asks about what are the capabilities of the agents, you can respond with the capabilities and respond with FINISH.
        2. If the user asks about how to earn money in DeFi, you can respond with the general ways to earn in DeFi and the DeFi tools and capabilities supported by the following workers: {members}. You can route to blockchain agent for specific actions only if the intent of the user feels like he really wants to earn money, otherwise for genreal queries respond suitably and respond with FINISH.

Ending Conversation:
    If the assistant agent indicates that no further action is needed, respond with FINISH.
    If the user explicitly asks to end the conversation, respond with a goodbye message and end the conversation.


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
    prompt = (
        f"""You may follow the following formats for the tweet: 
            "Task completed! The price of ETH is $2609.37. Check out the capabilities of our agents: {AGENT_CAPABILITIES} #DeFi #Crypto #Blockchain",
            "Just added liquidity to a new position with 1 VED and 10 STK! Exciting to be part of the DeFi space. Check out the transaction: https://sepolia.basescan.org/tx/0x67e903a1d8c952d29fb9e4b693586ca652bb7f98da94c8c761263baeac107202 #DeFi #Liquidity #Crypto",
            "🔥 DeFi Guru just made a power move! Just dropped a fresh liquidity position with 1 VED & 10 STK 🚀. See the action in real time: https://sepolia.basescan.org/tx/0x67e903a1d8c952d29fb9e4b693586ca652bb7f98da94c8c761263baeac107202. Ready to level up your crypto game? With DeFi Guru, your portfolio is always on point. #DeFi #Crypto #Liquidity #DeFiGuru".
        """)
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
    # prompt = (
    #     f"Given the full conversation context: '{conversation_context}', "
    #     "if a confirmation is needed for the current action (e.g., fetching ETH, approving for erc20 token or posting a tweet), "
    #     "firstly infer from the context and user intent and then, if not clear,"
    #     "think about yourselves generate a concise confirmation message starting with 'Yes, please', Otherwise, provide your brief opinion to accomplish the task/goal."
    # )
    prompt = (
        f""" Given the full conversation context: '{conversation_context}', if a confirmation is needed for the current action (e.g., fetching ETH or posting a tweet), infer from the context and user intent if confirmation can be given then, generate a concise confirmation message starting with 'Yes, please'. Otherwise, provide a clarifying response to the question so that further tasks could be done.

        If at some stage, important inputs are needed from the user and from the user intent its not clear, and further tasks cant be done without user intervention, only in this case you can make random choices(only so that tasks can be taken forward).
        
        After some task is done by blockchain_agent successfully, it needs to be posted on twitter so that DeFi guru gets fame and recognition. Respond that we need to tweet this to get fame. Also respond that the transaction link (eg. https://sepolia.basescan.org/tx/<txn_hash>, where you need to replace <txn_hash> with the actual transaction hash ) need to be included in the tweet.

        When you have doubt whether to create new liquidity or add liquidity to existing pool, always choose to add liquidity to existing pool. This is because the user has already provided the tokens and the user might have already added liquidity to the pool. So, adding liquidity to existing pool is the best choice.

        When you need some genuine input from the user and you cant deduce then respond that user input is needed and respond to supervisor to FINISH. 

        Analyse the conversation context to deduce that if the user is asking for general assistance or information, and no specific action is required, you can respond with the answer and the relevant supported capabilities: {AGENT_CAPABILITIES} and respond that the supervisor can further respond with FINISH.       
        """
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

# Examples:
    # initial_message = [HumanMessage(content="help me earning money. do both add liquidity to existing pool and create new liquidity. i have 16 stk and 1 ved token. after completing the operations you can post a cool message on twitter about this and add the txn link with format: https://sepolia.basescan.org/tx/${txnhash}. Dont forget to provide the tweet url.", name="User")]
    # initial_message = [HumanMessage(content="help me earning money. i have 10 stk and .1 ved token", name="User")]

# Print the last few messages for clarity
# for m in result_state["messages"][-4:]:
#     m.pretty_print()

# print("\n....................")
# print("\n....................")
# print("result_state: ", result_state)

# Print the conversation nicely
# print_conversation_nicely(result_state["messages"])

def run_chat_mode(graph, config):
    """Run the agent interactively based on user input."""
    print("\n" + "="*50)
    print("🤖 Welcome to DeFi Guru!".center(50))
    print("="*50)
    print("\nType 'exit' to end the conversation.")
    
    while True:
        try:
            user_input = input("\n💬 Your message: ")
            if user_input.lower() == 'exit':
                print("\nGoodbye! Thanks for using DeFi Guru! 👋")
                break

            # Create initial message and invoke graph
            initial_message = HumanMessage(content=user_input, name="User")
            print_message_nicely(initial_message)
            
            initial_messages = [initial_message]
            result_state = graph.invoke(
                {"messages": initial_messages}, 
                config=config, 
                stream_mode="values"
            )

            print("\n" + "-"*50)
            print("✅ Conversation complete for this request!")
            print("-"*50)

        except KeyboardInterrupt:
            print("\n\nGoodbye! Thanks for using DeFi Guru! 👋")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please try again.")

def main():
    """Initialize and run the DeFi Guru."""

    print(ASCII_ART)

    try:
        # Your existing initialization code here
        config = {"configurable": {"thread_id": "1", "user_id": "user@example.com"}}
        
        # Run the chat mode
        run_chat_mode(graph, config)

    except Exception as e:
        print(f"\n❌ Initialization error: {str(e)}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    print("\nInitializing DeFi Guru...")
    main()