"""
Hyperliquid Rebalancer V2 - Config Generator
==================================================
Génère config_wallet_X.json pour chaque wallet configuré.
Détecte les tokens Spot et les positions Futures ouvertes.

Usage:
    python autoconfig.py
"""

import os
import json
import requests
from typing import Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# =============================================================================
# CONFIGURATION ET UTILITAIRES
# =============================================================================

API_URL = "https://api.hyperliquid.xyz/info"

def api_call(payload: Dict) -> Any:
    """Appel API Hyperliquid pour l'endpoint info"""
    r = requests.post(API_URL, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def load_config(wallet_id: int) -> Dict[str, Any]:
    """Charge la configuration depuis config_wallet_X.json"""
    config_file = f"config_wallet_{wallet_id}.json"
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Retourne une structure de base si le fichier n'existe pas
        return {
            "settings": {
                "order_size_usd": 15,
                "cooldown_minutes": 15,
                "default_fee_pct": 0.07,
                "check_interval_seconds": 100,
                "dry_run": False
            },
            "spot_tokens": {},
            "perpetuals": {}
        }

def save_config(config: Dict[str, Any], wallet_id: int) -> None:
    """Sauvegarde la configuration dans config_wallet_X.json"""
    config_file = f"config_wallet_{wallet_id}.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

# =============================================================================
# API HYPERLIQUID - DONNÉES
# =============================================================================

def get_all_mids() -> Dict[str, float]:
    """Récupère tous les mid prices (Spot et Perpétuels)"""
    data = api_call({"type": "allMids"})
    return {k: float(v) for k, v in data.items()}

def get_spot_balances(address: str) -> Dict[str, float]:
    """Récupère les balances spot (sans l'USDC retirable des perps pour la config)"""
    data = api_call({"type": "spotClearinghouseState", "user": address})
    balances = {}
    for bal in data.get("balances", []):
        token = bal.get("coin", "")
        total = float(bal.get("total", 0))
        if total > 0 and token != "USDC":
            balances[token] = total
    return balances

def get_spot_meta() -> Dict[str, Any]:
    """Récupère les métadonnées spot (pour szDecimals)"""
    return api_call({"type": "spotMeta"})

def get_token_info(token: str, spot_meta: Dict) -> Tuple[Optional[int], int, int]:
    """
    Retourne (pair_index, sz_decimals, tick_decimals) pour un token spot.
    """
    token_idx = None
    sz_decimals = 2
    tick_decimals = 6
    
    for t in spot_meta.get("tokens", []):
        if t.get("name") == token:
            token_idx = t.get("index")
            sz_decimals = t.get("szDecimals", 2)
            tick_decimals = t.get("tickDecimals", 6)
            break
    
    pair_index = None
    if token_idx is not None:
        for pair in spot_meta.get("universe", []):
            tokens = pair.get("tokens", [])
            if len(tokens) >= 1 and tokens[0] == token_idx:
                pair_index = pair.get("index")
                break
    
    return pair_index, sz_decimals, tick_decimals

def get_perp_account_summary(address: str, dex_name: str = "") -> Dict[str, Any]:
    """Récupère le résumé du compte perpétuel de l'utilisateur (positions) pour un DEX spécifique"""
    payload = {"type": "clearinghouseState", "user": address}
    if dex_name:
        payload["dex"] = dex_name
    return api_call(payload)

def get_all_perp_positions(address: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Récupère toutes les positions futures de tous les DEX (main + HIP-3).
    Retourne une liste de tuples (dex_name, position_data)
    """
    dexs_to_check = ["", "flx", "hyna", "vntl", "xyz"]
    all_positions = []
    
    for dex_name in dexs_to_check:
        try:
            perp_summary = get_perp_account_summary(address, dex_name)
            positions = perp_summary.get("assetPositions", [])
            if positions:
                for asset_pos in positions:
                    pos = asset_pos.get("position", {})
                    szi = float(pos.get("szi", 0))
                    if abs(szi) > 1e-8:  # Ignorer les positions vides
                        all_positions.append((dex_name if dex_name else "main", pos))
        except Exception as e:
            # Continuer même si un DEX échoue
            print(f"   ⚠️  Erreur lors de la récupération du DEX '{dex_name if dex_name else 'main'}': {e}")
            continue
    
    return all_positions

def get_perp_meta_and_contexts() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Récupère les métadonnées et les contextes d'actifs (prix, etc.) depuis tous les DEXs"""
    
    # Récupérer depuis le main DEX
    payload = {"type": "metaAndAssetCtxs"}
    data = api_call(payload)
    
    perp_meta = data[0]
    asset_contexts = data[1]
    
    asset_ctx_map = {}
    for ctx in asset_contexts:
        # CORRECTION: Vérifier si 'sName' existe avant d'y accéder
        if "sName" in ctx:
            asset_ctx_map[ctx["sName"]] = ctx
    
    # Aussi récupérer depuis les DEXs HIP-3
    hip3_dexs = ["flx", "hyna", "vntl", "xyz"]
    for dex_name in hip3_dexs:
        try:
            dex_data = api_call({"type": "metaAndAssetCtxs", "dex": dex_name})
            dex_meta = dex_data[0]
            dex_contexts = dex_data[1]
            
            # Ajouter au perp_meta.universe les assets HIP-3
            for asset in dex_meta.get("universe", []):
                asset_name = asset.get("name", "")
                if asset_name and asset_name not in [a.get("name") for a in perp_meta.get("universe", [])]:
                    perp_meta.setdefault("universe", []).append(asset)
            
            # Ajouter les contextes
            for ctx in dex_contexts:
                if "sName" in ctx and ctx["sName"] not in asset_ctx_map:
                    asset_ctx_map[ctx["sName"]] = ctx
        except Exception:
            continue
    
    # Aussi récupérer depuis allMids pour les tokens qui ne sont pas dans assetContexts
    try:
        mids = get_all_mids()
        for coin, price in mids.items():
            # Ajouter seulement si pas déjà présent (allMids peut avoir des clés différentes)
            if coin not in asset_ctx_map and not coin.startswith("@"):
                try:
                    # Créer un contexte minimal avec le prix
                    asset_ctx_map[coin] = {"sName": coin, "markPx": float(price)}
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass
    
    return perp_meta, asset_ctx_map

def get_perp_info(asset_name: str, perp_meta: Dict) -> Tuple[Optional[int], int]:
    """
    Retourne (asset_index, sz_decimals) pour un actif perpétuel.
    Cherche dans le perp_meta (qui inclut maintenant les HIP-3)
    """
    asset_index = None
    sz_decimals = 3  # Valeur par défaut plus adaptée aux HIP-3
    
    for asset in perp_meta.get("universe", []):
        if asset.get("name") == asset_name:
            asset_index = asset.get("index")
            sz_decimals = asset.get("szDecimals", 3)
            break
    
    # Si pas trouvé dans universe principal, chercher dans les DEXs HIP-3
    if asset_index is None and ":" in asset_name:
        dex_name = asset_name.split(":")[0]
        try:
            dex_data = api_call({"type": "metaAndAssetCtxs", "dex": dex_name})
            dex_meta = dex_data[0]
            for asset in dex_meta.get("universe", []):
                if asset.get("name") == asset_name:
                    asset_index = asset.get("index")
                    sz_decimals = asset.get("szDecimals", 3)
                    break
        except Exception:
            pass
    
    return asset_index, sz_decimals

# Cache pour les métadonnées
_metadata_cache: Dict[str, Any] = {}

def get_token_id_to_name() -> Dict[int, str]:
    """Récupère le mapping token_id -> nom depuis spotMeta (cache)"""
    global _metadata_cache
    
    if "token_mapping" not in _metadata_cache:
        spot_meta = api_call({"type": "spotMeta"})
        _metadata_cache["token_mapping"] = {
            t["index"]: t["name"] for t in spot_meta.get("tokens", [])
        }
    return _metadata_cache["token_mapping"]

def get_dex_quote_asset(dex_name: str) -> str:
    """
    Récupère dynamiquement le quote asset (collateral) pour un DEX HIP-3.
    - flx, vntl -> USDH
    - xyz -> USDC
    - hyna -> USDE
    """
    global _metadata_cache
    
    cache_key = f"dex_quote_{dex_name}"
    if cache_key not in _metadata_cache:
        try:
            dex_data = api_call({"type": "metaAndAssetCtxs", "dex": dex_name})
            collateral_id = dex_data[0].get("collateralToken", 0)
            token_mapping = get_token_id_to_name()
            _metadata_cache[cache_key] = token_mapping.get(collateral_id, "USDC")
        except Exception:
            # Fallback basé sur les DEX connus
            fallback = {"flx": "USDH", "vntl": "USDH", "xyz": "USDC", "hyna": "USDE"}
            _metadata_cache[cache_key] = fallback.get(dex_name, "USDC")
    
    return _metadata_cache[cache_key]

def get_spot_pair_quote_asset(pair_index: int) -> str:
    """Récupère dynamiquement le quote asset pour une paire spot"""
    global _metadata_cache
    
    cache_key = f"spot_quote_{pair_index}"
    if cache_key not in _metadata_cache:
        try:
            spot_meta = api_call({"type": "spotMeta"})
            token_mapping = get_token_id_to_name()
            
            for pair in spot_meta.get("universe", []):
                if pair.get("index") == pair_index:
                    tokens = pair.get("tokens", [])
                    if len(tokens) > 1:
                        quote_id = tokens[1]  # Le 2ème token est le quote
                        _metadata_cache[cache_key] = token_mapping.get(quote_id, "USDC")
                    else:
                        _metadata_cache[cache_key] = "USDC"
                    break
            else:
                _metadata_cache[cache_key] = "USDC"
        except Exception:
            _metadata_cache[cache_key] = "USDC"
    
    return _metadata_cache[cache_key]

def get_quote_asset_for_coin(coin: str, pair_index: Optional[int] = None) -> str:
    """
    Retourne le quote asset pour un coin donné.
    Récupère dynamiquement depuis l'API.
    
    - Spot (@pair_index) : Dépend de la paire (USDC, USDT, USDH...)
    - Perp Main : USDC
    - Perp HIP-3 (dex:asset) : Dépend du DEX (flx/vntl=USDH, xyz=USDC, hyna=USDE)
    """
    # Perp HIP-3 : contient ":"
    if ":" in coin:
        dex_name = coin.split(":")[0]
        return get_dex_quote_asset(dex_name)
    
    # Perp Main : USDC
    return "USDC"

# =============================================================================
# LOGIQUE DE GÉNÉRATION
# =============================================================================

def generate_config_file(wallet_id: int) -> None:
    """Génère la config pour un wallet spécifique, incluant Spot et Futures"""
    
    address = os.getenv(f"HL_ADDRESS_{wallet_id}")
    if not address:
        raise ValueError(f"❌ HL_ADDRESS_{wallet_id} non trouvé!")
    
    print(f"📊 Scanning wallet {wallet_id}: {address[:10]}...")
    
    # 1. Récupérer les données
    try:
        balances = get_spot_balances(address)
        spot_meta = get_spot_meta()
        perp_meta, asset_ctx_map = get_perp_meta_and_contexts()
        mids = get_all_mids()
        all_perp_positions = get_all_perp_positions(address)
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion à l'API Hyperliquid: {e}")
        return
    
    # Charger config existante ou créer nouvelle
    config = load_config(wallet_id)
    
    # 2. Mettre à jour les tokens Spot
    print("\n" + "="*50)
    print("TOKENS SPOT DÉTECTÉS:")
    print("="*50)
    
    for token, amount in balances.items():
        if token == "USDC":
            continue
            
        pair_index, sz_decimals, tick_decimals = get_token_info(token, spot_meta)
        
        # Récupérer le prix (essayer d'abord avec pair_index, puis directement avec le nom)
        price = 0
        if pair_index is not None:
            price_key = f"@{pair_index}"
            price = mids.get(price_key, 0)
        if price == 0:
            # Essayer directement avec le nom du token
            price = mids.get(token, 0)
        value_usd = amount * price
        
        # Déterminer le quote asset pour cette paire spot
        spot_quote_asset = get_spot_pair_quote_asset(pair_index) if pair_index is not None else "USDC"
        
        print(f"\n💰 {token} (/{spot_quote_asset}):")
        print(f"   Balance: {amount:.6f}")
        print(f"   Prix: ${price:.6f}")
        print(f"   Valeur: ${value_usd:.2f}")
        
        if token not in config["spot_tokens"]:
            # Nouveau token - ajouter avec valeur actuelle comme target
            config["spot_tokens"][token] = {
                "enabled": False,
                "hold_usd": max(round(value_usd, 0), 100),
                "buy_enabled": True,
                "sell_enabled": True,
                "buy_threshold_pct": 16,
                "sell_threshold_pct": 16,
                "fee_pct": 0.07,
                "pair_index": pair_index,
                "sz_decimals": sz_decimals,
                "price_decimals": tick_decimals,
                "quote_asset": spot_quote_asset
            }
            print(f"   ➕ Ajouté à la config (quote = {spot_quote_asset})")
        else:
            # Token existant - mettre à jour les métadonnées
            config["spot_tokens"][token]["pair_index"] = pair_index
            config["spot_tokens"][token]["sz_decimals"] = sz_decimals
            config["spot_tokens"][token]["price_decimals"] = tick_decimals
            config["spot_tokens"][token]["quote_asset"] = spot_quote_asset
            print(f"   ✓ Métadonnées mises à jour (quote = {spot_quote_asset})")
            
    # 3. Mettre à jour les positions Futures (tous DEX inclus)
    print("\n" + "="*50)
    print("POSITIONS FUTURES DÉTECTÉES (Main + HIP-3):")
    print("="*50)
    
    if not all_perp_positions:
        print("\n   Aucune position future détectée")
    else:
        for dex_name, pos in all_perp_positions:
            asset_name = pos.get("coin")
            szi = float(pos.get("szi", 0))
            
            if not asset_name or abs(szi) < 1e-8:
                continue
            
            # Récupérer les métadonnées
            asset_index, sz_decimals = get_perp_info(asset_name, perp_meta)
            
            # Récupérer le prix pour calculer la valeur notionnelle actuelle
            # Essayer d'abord depuis asset_ctx_map, puis depuis la position elle-même
            mark_price = 0
            if asset_name in asset_ctx_map:
                mark_price = float(asset_ctx_map[asset_name].get("markPx", 0))
            
            if mark_price == 0:
                # Essayer depuis la position directement
                mark_from_pos = pos.get("markPx", 0)
                if mark_from_pos and mark_from_pos != "N/A":
                    try:
                        mark_price = float(mark_from_pos)
                    except (ValueError, TypeError):
                        pass
            
            # Si toujours pas de prix, utiliser le prix d'entrée comme approximation
            if mark_price == 0:
                entry_price = float(pos.get("entryPx", 0))
                mark_price = entry_price if entry_price > 0 else 0
            
            current_notional_usd = abs(szi * mark_price) if mark_price > 0 else abs(szi * float(pos.get("entryPx", 0)))
            
            dex_label = f"[{dex_name}]" if dex_name != "main" else "[Main]"
            print(f"\n📈 {asset_name} {dex_label}:")
            print(f"   Position (szi): {szi:.6f}")
            print(f"   Prix Mark: ${mark_price:.6f}")
            print(f"   Valeur Notionnelle: ${current_notional_usd:.2f}")
            
            # Déterminer le quote asset
            quote_asset = get_quote_asset_for_coin(asset_name)
            
            if asset_name not in config["perpetuals"]:
                # Nouveau perpétuel - ajouter avec valeur notionnelle actuelle comme target
                config["perpetuals"][asset_name] = {
                    "enabled": False,
                    "hold_usd": max(round(current_notional_usd, 0), 100),
                    "buy_enabled": True,
                    "sell_enabled": True,
                    "buy_threshold_pct": 16,
                    "sell_threshold_pct": 16,
                    "fee_pct": 0.07,
                    "asset_name": asset_name,
                    "sz_decimals": sz_decimals,
                    "price_decimals": 6,  # Par défaut pour les perps
                    "dex": dex_name if dex_name != "main" else "",  # Stocker le DEX pour référence
                    "quote_asset": quote_asset  # USDC ou USDH
                }
                print(f"   ➕ Ajouté à la config (hold_usd = valeur notionnelle, quote = {quote_asset})")
            else:
                # Perpétuel existant - mettre à jour les métadonnées
                config["perpetuals"][asset_name]["sz_decimals"] = sz_decimals
                config["perpetuals"][asset_name]["quote_asset"] = quote_asset
                if "dex" not in config["perpetuals"][asset_name]:
                    config["perpetuals"][asset_name]["dex"] = dex_name if dex_name != "main" else ""
                print(f"   ✓ Métadonnées mises à jour (quote = {quote_asset})")
            
    # Sauvegarder
    save_config(config, wallet_id)
    
    print("\n" + "="*50)
    print(f"✅ config_wallet_{wallet_id}.json sauvegardé!")
    print("="*50)
    print("\n📝 Prochaines étapes:")
    print("   1. Ouvre le fichier de config.")
    print("   2. Ajuste 'hold_usd' dans les sections 'spot_tokens' et 'perpetuals'.")
    print("   3. Lance le bot principal avec 'python bot.py'.")

# =============================================================================
# MAIN
# =============================================================================

def main():
    # Déterminer les wallets à traiter
    wallet_ids = []
    i = 1
    while os.getenv(f"HL_ADDRESS_{i}"):
        wallet_ids.append(i)
        i += 1
    
    if not wallet_ids:
        print("❌ Aucun wallet trouvé. Assurez-vous que HL_ADDRESS_1, HL_PRIVATE_KEY_1, etc., sont définis dans vos variables d'environnement.")
        return

    print("--- Mode Génération de Configuration ---")
    for wid in wallet_ids:
        try:
            generate_config_file(wid)
        except Exception as e:
            print(f"❌ Erreur lors de la génération pour Wallet {wid}: {e}")

if __name__ == "__main__":
    main()
