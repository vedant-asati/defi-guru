# approve_token.py
from cdp import Wallet
from typing import Type
from pydantic import BaseModel, Field

# Import CdpTool
from cdp_langchain.tools import CdpTool

from helpers import parse_token_amount, TOKENS, CONTRACTS, ERC20_ABI

APPROVE_TOKEN_DESCRIPTION = """
Approve the Uniswap V3 Liquidity contract to spend a specified amount of your ERC20 tokens on your behalf. This is required before adding liquidity or performing actions involving token transfers by the contract if approval is not already done by the user.

**Usage Examples:**
- "Approve 1,000,000 STK for the liquidity contract."
- "Allow the liquidity contract to spend 100,000 VED."

**Parameters:**
- **token_amount**: The amount and symbol of the token to approve (e.g., "1,000,000 STK").

**Important Notes:**
- **Existing Approval**: Check if sufficient allowance exists to avoid unnecessary transactions.
- If approval requesed for small amount of tokens (<100, eg. 1 STK) then approve for 100 times the amount to avoid multiple approvals in future.
- **Token Support**: Only recognized tokens can be approved.
- **Network Support**: Supported only on 'base-sepolia' network.
- **No Addresses Needed**: Contract and token addresses are predefined.
- ""No need to do again and again unnecessarily, if already approved.
"""

class ApproveTokenInput(BaseModel):
    """Input argument schema for approving tokens."""
    token_amount: str = Field(
        ...,
        description='The amount and symbol of the token to approve, e.g., "1000000 STK".'
    )

def approve_token(wallet: Wallet, token_amount: str) -> str:
    """Approve tokens for the liquidity contract."""
    try:
        print("-"*20 + "Invoking approve_token"+ "-"*20)

        symbol, amount_wei = parse_token_amount(token_amount)
        token_address = TOKENS[symbol]['address']

        # The address of your UniswapV3Liquidity contract
        liquidity_contract_address = CONTRACTS["UNISWAP_V3_LIQUIDITY_CONTRACT"]

        invocation = wallet.invoke_contract(
            contract_address=token_address,
            method='approve',
            abi=ERC20_ABI,
            args={
                '_spender': liquidity_contract_address,
                '_value': str(amount_wei),
            },
            asset_id='wei',  # Assuming 'wei' as the asset ID for ETH network
        )
        result = invocation.wait()
        
        # print("result:", result, "\n")
        print(f"✅ Approval successful! Transaction hash: {result.transaction.transaction_hash}")

        return f"✅ Approval successful! Transaction hash: {result.transaction.transaction_hash}"
    except Exception as e:
        return f"❌ Approval failed: {str(e)}"

# Create the tool instance
def get_approve_token_tool(agentkit):
    return CdpTool(
        name="approve_token",
        description=APPROVE_TOKEN_DESCRIPTION,
        cdp_agentkit_wrapper=agentkit,
        args_schema=ApproveTokenInput,
        func=approve_token,
    )