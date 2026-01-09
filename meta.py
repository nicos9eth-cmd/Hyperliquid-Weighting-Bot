import json
import requests

HL_INFO_URL = "https://api.hyperliquid.xyz/info"

def fetch_spot_meta():
    r = requests.post(HL_INFO_URL, json={"type": "spotMeta"}, timeout=10)
    r.raise_for_status()
    return r.json()

def consolidate_by_token(spot_meta):
    tokens = {t["index"]: t for t in spot_meta["tokens"]}

    # 🔑 HL spot markets can be under different keys
    markets = (
        spot_meta.get("markets")
        or spot_meta.get("universe")
        or []
    )

    result = {}

    # init tokens
    for token_id, token in tokens.items():
        result[token["name"]] = {
            "token_index": token_id,
            "metadata": token,
            "pairs": []
        }

    # attach pairs to base token
    for market in markets:
        base_id, quote_id = market["tokens"]

        base = tokens[base_id]
        quote = tokens[quote_id]

        result[base["name"]]["pairs"].append({
            "pair_index": market["index"],
            "quote_asset": quote["name"],
            "quote_token_index": quote_id,
            "is_canonical": market.get("isCanonical", False),
            "market_name": market.get("name")
        })

    return result

def main():
    spot_meta = fetch_spot_meta()
    consolidated = consolidate_by_token(spot_meta)

    with open("hl_spot_tokens_with_pairs.json", "w") as f:
        json.dump(consolidated, f, indent=2)

    print(f"{len(consolidated)} tokens consolidés")

if __name__ == "__main__":
    main()
