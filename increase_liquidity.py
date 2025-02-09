# increase_liquidity.py

from cdp import Wallet
from pydantic import BaseModel, Field

# Import CdpTool
from cdp_langchain.tools import CdpTool

from helpers import parse_token_amount, TOKENS, CONTRACTS, UNISWAP_V3_LIQUIDITY_ABI

INCREASE_LIQUIDITY_DESCRIPTION = """
Add liquidity to an existing Uniswap V3 position identified by a token ID, increasing your stake and potential fee share.

**Usage Examples:**
- "Increase liquidity for token ID 35 with 100 VED and 10,000 STK."
- "Add liquidity to position 42: 50 VED + 5,000 STK."

**Parameters:**
- **token_id**: ID of your existing Uniswap V3 position.(e`g., 35).
- **tokenA_amount**: Amount and symbol of the first token (e.g., "100 VED").
- **tokenB_amount**: Amount and symbol of the second token (e.g., "10,000 STK").

**Important Notes:**
- **Token Approval Required**: Approve the liquidity contract to spend both tokens using `approve_token` if not already approved. Assume approval is done by default and if txn fails with error might mean that approval is not done for the token pair. Use approve_token tool to approve the token pair.
- **Valid Token ID**: `token_id` must correspond to a position you own. Valid tokenids are: 35-40. If not provided, it will take 35 by default.
- **Network Support**: Supported only on 'base-sepolia' network.
- **No Addresses Needed**: Contract and token addresses are predefined.
"""

class IncreaseLiquidityInput(BaseModel):
    """Input argument schema for increasing liquidity."""
    token_id: int = Field(
        ..., description="The ID of the existing Uniswap V3 position."
    )
    tokenA_amount: str = Field(
        ...,
        description='The amount and symbol of the first token, e.g., "100 VED".'
    )
    tokenB_amount: str = Field(
        ...,
        description='The amount and symbol of the second token, e.g., "10000 STK".'
    )

def increase_liquidity(wallet: Wallet, token_id: int, tokenA_amount: str, tokenB_amount: str) -> str:
    """Increase liquidity of an existing position."""
    try:
        print("-"*20 + "Invoking increase liquidity"+ "-"*20)
        symbolA, amountA = parse_token_amount(tokenA_amount)
        symbolB, amountB = parse_token_amount(tokenB_amount)
        tokenA_address = TOKENS[symbolA]['address']
        tokenB_address = TOKENS[symbolB]['address']

        # The address of your UniswapV3Liquidity contract
        liquidity_contract_address = CONTRACTS["UNISWAP_V3_LIQUIDITY_CONTRACT"]

        invocation = wallet.invoke_contract(
            contract_address=liquidity_contract_address,
            method='increaseLiquidityCurrentRange',
            abi=UNISWAP_V3_LIQUIDITY_ABI,
            args={
                'token0Address': tokenA_address,
                'token1Address': tokenB_address,
                'tokenId': str(token_id),
                'amount0ToAdd': str(amountA),  # Convert to string
                'amount1ToAdd': str(amountB),  # Convert to string
            },
            asset_id='wei',
        )
        result = invocation.wait()
        # print("result:", result, "\n")
        print(f"🛠 Liquidity increased! Transaction hash: {result.transaction.transaction_hash}")
        
        return f"🛠 Liquidity increased! Transaction hash: {result.transaction.transaction_hash}"
    except Exception as e:
        return f"❌ Increasing liquidity failed: {str(e)}"

# Create the tool instance
def get_increase_liquidity_tool(agentkit):
    return CdpTool(
        name="increase_liquidity",
        description=INCREASE_LIQUIDITY_DESCRIPTION,
        cdp_agentkit_wrapper=agentkit,
        args_schema=IncreaseLiquidityInput,
        func=increase_liquidity,
    )