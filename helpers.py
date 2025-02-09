# helpers.py

import re
from decimal import Decimal
from pydantic import BaseModel

TOKENS = {
    'STK': {
        'address': '0x134B005F1502dcfe95C8b50Bf2e38B446FE7b9cC',
        'decimals': 18,
    },
    'VED': {
        'address': '0x0C0Db17101D6b1Db59E16b05f648D74f0Abc743a',
        'decimals': 18,
    },
}

CONTRACTS = {
#   // UNISWAP_V3_LIQUIDITY_CONTRACT: "0x0",
#   // UNISWAP_V3_LIQUIDITY_CONTRACT: "0x891467ceCeE70c23d111Bd5E8dC4462d75e39106",
#   // UNISWAP_V3_LIQUIDITY_CONTRACT: "0xe2ca5ae07e177ccde25c15ca3521bf9a48406c83", // v2
#   // UNISWAP_V3_LIQUIDITY_CONTRACT: "0x0db365b67FD697Abb0059a263e0914C9e084cC3E", // real
  "UNISWAP_V3_LIQUIDITY_CONTRACT": "0xE568ff42654d48869A138f072D1810EB25145174", # real new
  "BluedexV3Factory": "0x6c2927615c77Ca33400A4326BFDfEb0B30CD6BbF",
  "UniversalRouter": "0x41a2b6Ba1274778F716501aA2F0bF34eBB8c44D6",
  "NonfungiblePositionManager": "0x883993A97D825b98ef9E4522Db6F42e990B8489E",
}

UNISWAP_V3_LIQUIDITY_ABI = [
  {
    "inputs": [],
    "name": "claimOwnwership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "name": "collectAllFees",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "amount0",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amount1",
        "type": "uint256"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "uint128",
        "name": "liquidity",
        "type": "uint128"
      }
    ],
    "name": "decreaseLiquidityCurrentRange",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "amount0",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amount1",
        "type": "uint256"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token0Address",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "token1Address",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amount0ToAdd",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amount1ToAdd",
        "type": "uint256"
      }
    ],
    "name": "increaseLiquidityCurrentRange",
    "outputs": [
      {
        "internalType": "uint128",
        "name": "liquidity",
        "type": "uint128"
      },
      {
        "internalType": "uint256",
        "name": "amount0",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amount1",
        "type": "uint256"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token0Address",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "token1Address",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "amount0ToAdd",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amount1ToAdd",
        "type": "uint256"
      }
    ],
    "name": "mintNewPosition",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "uint128",
        "name": "liquidity",
        "type": "uint128"
      },
      {
        "internalType": "uint256",
        "name": "amount0",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amount1",
        "type": "uint256"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "newAddress",
        "type": "address"
      }
    ],
    "name": "updateNFPM",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getOwner",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "nonfungiblePositionManager",
    "outputs": [
      {
        "internalType": "contract INonfungiblePositionManager",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "operator",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "from",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "tokenId",
        "type": "uint256"
      },
      {
        "internalType": "bytes",
        "name": "",
        "type": "bytes"
      }
    ],
    "name": "onERC721Received",
    "outputs": [
      {
        "internalType": "bytes4",
        "name": "",
        "type": "bytes4"
      }
    ],
    "stateMutability": "pure",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "owner",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
]

def parse_token_amount(input_str):
    """
    Parse amounts like '5 STK' and convert to Wei.
    """
    regex = r'^(\d+(\.\d+)?)\s*([A-Za-z0-9]+)$'
    match = re.match(regex, input_str.strip())
    if not match:
        raise ValueError(f'Invalid token amount format: "{input_str}". Expected format like "5 STK".')

    amount = match.group(1)
    symbol = match.group(3).upper()

    if symbol not in TOKENS:
        raise ValueError(f'Unsupported token symbol: "{symbol}". Supported tokens are {list(TOKENS.keys())}')

    decimals = TOKENS[symbol]['decimals']
    amount_wei = int(Decimal(amount) * (10 ** decimals))

    return symbol, amount_wei

def get_deadline(offset_seconds=600):
    import time
    return int(time.time()) + offset_seconds

# First, define your pretty print function
def print_message_nicely(msg):
    print("\n" + "-"*50)
    if msg.name == "User":
        print("👤  User:")
        print(f"   {msg.content}\n")
    elif msg.name == "blockchain_agent":
        print("⛓️  Blockchain Agent:")
        print(f"   {msg.content}\n")
    elif msg.name == "twitter_agent":
        print("🐦  Twitter Agent:")
        print(f"   {msg.content}\n")
    elif msg.name == "assistant_agent":
        print("🤖  Assistant Agent:")
        print(f"   {msg.content}\n")
    print("-"*50)

ASCII_ART = f"""

    /$$$$$$$            /$$$$$$$$ /$$        /$$$$$$                               
    | $$__  $$          | $$_____/|__/       /$$__  $$                              
    | $$  \ $$  /$$$$$$ | $$       /$$      | $$  \__/ /$$   /$$  /$$$$$$  /$$   /$$
    | $$  | $$ /$$__  $$| $$$$$   | $$      | $$ /$$$$| $$  | $$ /$$__  $$| $$  | $$
    | $$  | $$| $$$$$$$$| $$__/   | $$      | $$|_  $$| $$  | $$| $$  \__/| $$  | $$
    | $$  | $$| $$_____/| $$      | $$      | $$  \ $$| $$  | $$| $$      | $$  | $$
    | $$$$$$$/|  $$$$$$$| $$      | $$      |  $$$$$$/|  $$$$$$/| $$      |  $$$$$$/
    |_______/  \_______/|__/      |__/       \______/  \______/ |__/       \______/ 
                                                                                                                                                                
"""