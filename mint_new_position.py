# mint_new_position.py

from cdp import Wallet
from pydantic import BaseModel, Field

# Import CdpTool
from cdp_langchain.tools import CdpTool

from helpers import parse_token_amount, TOKENS, CONTRACTS, UNISWAP_V3_LIQUIDITY_ABI

MINT_NEW_POSITION_DESCRIPTION = """
Create a new liquidity position on Uniswap V3 using a pair of tokens. This adds liquidity to the pool for the specified token pair.

**Usage Examples:**
- "Mint new position with 100 VED and 10,000 STK."
- "Create liquidity position: 50 VED + 5,000 STK."

**Parameters:**
- **tokenA_amount**: Amount and symbol of the first token (e.g., "100 VED").
- **tokenB_amount**: Amount and symbol of the second token (e.g., "10,000 STK").

**Important Notes:**
- **Token Approval Required**: Approve the liquidity contract to spend both tokens using `approve_token` if not already approved. Assume approval is done by default and if txn fails with error might mean that approval is not done for the token pair. Use approve_token tool to approve the token pair.
- **Sufficient Balance**: Ensure you have enough of both tokens.
- **Network Support**: Supported only on 'base-sepolia' network.
- **No Addresses Needed**: Contract and token addresses are predefined.
- If miniting new position fails then it could also mean that liquidity pool is already created for the token pair. Use one of the default token ids to increase the liquidity using increase_liquidity tool.
"""

class MintNewPositionInput(BaseModel):
    """Input argument schema for minting new position."""
    tokenA_amount: str = Field(
        ...,
        description='The amount and symbol of the first token, e.g., "100 VED".'
    )
    tokenB_amount: str = Field(
        ...,
        description='The amount and symbol of the second token, e.g., "10000 STK".'
    )

def mint_new_position(wallet: Wallet, tokenA_amount: str, tokenB_amount: str) -> str:
    """Mint a new liquidity position."""
    try:
        print("-"*20 + "Invoking mint_new_position" + "-"*20)

        symbolA, amountA = parse_token_amount(tokenA_amount)
        symbolB, amountB = parse_token_amount(tokenB_amount)

        tokenA_address = TOKENS[symbolA]['address']
        tokenB_address = TOKENS[symbolB]['address']

        # The address of your UniswapV3Liquidity contract
        liquidity_contract_address = CONTRACTS["UNISWAP_V3_LIQUIDITY_CONTRACT"]
        print("liquidity_contract_address", liquidity_contract_address)

        invocation = wallet.invoke_contract(
            contract_address=liquidity_contract_address,
            method='mintNewPosition',
            abi=UNISWAP_V3_LIQUIDITY_ABI,
            args={
                'token0Address': tokenA_address,
                'token1Address': tokenB_address,
                'amount0ToAdd': str(amountA),  # Convert to string
                'amount1ToAdd': str(amountB),  # Convert to string
            },
            asset_id='wei',
        )
        result = invocation.wait()
        # print("result", result, "\n")
        print(f"🎉 New liquidity position created! Transaction hash: {result.transaction.transaction_hash}")

        return f"🎉 New liquidity position created! Transaction hash: {result.transaction.transaction_hash}"
    except Exception as e:
        return f"❌ Minting new position failed: {str(e)}"

# Create the tool instance
def get_mint_new_position_tool(agentkit):
    return CdpTool(
        name="mint_new_position",
        description=MINT_NEW_POSITION_DESCRIPTION,
        cdp_agentkit_wrapper=agentkit,
        args_schema=MintNewPositionInput,
        func=mint_new_position,
    )