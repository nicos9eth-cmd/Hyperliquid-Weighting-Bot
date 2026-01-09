"""
Hyperliquid Rebalancer V2 - Bot Principal
==================================================
Version V2 : Multi-wallet, Spot et Futures (Perpetuals) avec levier x1.

Usage:
    python bot.py              # Lance tous les wallets configurés
    python bot.py --dry-run    # Mode simulation (pas d'ordres réels)
    python bot.py --wallet 1   # Lance uniquement le wallet 1
"""

import os
import json
import time
import math
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# --- Importations spécifiques à Hyperliquid ---
# Ces dépendances doivent être installées (pip install hyperliquid-python-sdk eth-account)
try:
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from hyperliquid.utils import constants
    from eth_account import Account
except ImportError:
    print("❌ Erreur: Les dépendances 'hyperliquid-python-sdk' et 'eth-account' ne sont pas installées.")
    print("   Veuillez exécuter : pip install hyperliquid-python-sdk eth-account")
    exit(1)
# -----------------------------------------------------------------------

# =============================================================================
# CONFIGURATION ET UTILITAIRES
# =============================================================================

API_URL = "https://api.hyperliquid.xyz/info"

# Liste des DEXs HIP-3 connus (nécessaire pour initialiser Exchange correctement)
HIP3_DEXS = ["flx", "hyna", "vntl", "xyz"]

# Cache global pour l'Exchange initialisé (évite de recréer à chaque ordre)
_exchange_cache: Dict[str, Exchange] = {}

# Cache pour les métadonnées des marchés (quote assets, tick sizes, etc.)
_market_metadata_cache: Dict[str, Any] = {}

def api_call(payload: Dict) -> Any:
    """Appel API Hyperliquid pour l'endpoint info"""
    r = requests.post(API_URL, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def load_config(wallet_id: int) -> Dict[str, Any]:
    """Charge la configuration depuis config_wallet_X.json"""
    config_file = f"config_wallet_{wallet_id}.json"
    with open(config_file, "r") as f:
        return json.load(f)

# =============================================================================
# API HYPERLIQUID - DONNÉES
# =============================================================================

def get_all_mids() -> Dict[str, float]:
    """Récupère tous les mid prices (Spot et Perpétuels)"""
    data = api_call({"type": "allMids"})
    return {k: float(v) for k, v in data.items()}

def get_spot_balances(address: str) -> Dict[str, float]:
    """Récupère les balances spot + USDC perp withdrawable"""
    # Balances spot (inclut USDC, USDH, et tous les tokens)
    data = api_call({"type": "spotClearinghouseState", "user": address})
    balances = {}
    for bal in data.get("balances", []):
        token = bal.get("coin", "")
        total = float(bal.get("total", 0))
        if total > 0:
            balances[token] = total
    
    # Ajouter USDC withdrawable depuis perp (main DEX)
    perp_data = get_perp_account_summary(address)
    withdrawable = float(perp_data.get("withdrawable", 0))
    if withdrawable > 0:
        balances["USDC"] = balances.get("USDC", 0) + withdrawable
    
    return balances

def get_token_id_to_name() -> Dict[int, str]:
    """Récupère le mapping token_id -> nom depuis spotMeta (cache)"""
    global _market_metadata_cache
    
    if "token_mapping" not in _market_metadata_cache:
        spot_meta = api_call({"type": "spotMeta"})
        _market_metadata_cache["token_mapping"] = {
            t["index"]: t["name"] for t in spot_meta.get("tokens", [])
        }
    return _market_metadata_cache["token_mapping"]

def get_dex_quote_asset(dex_name: str) -> str:
    """
    Récupère dynamiquement le quote asset (collateral) pour un DEX HIP-3.
    - flx, vntl -> USDH
    - xyz -> USDC
    - hyna -> USDE
    """
    global _market_metadata_cache
    
    cache_key = f"dex_quote_{dex_name}"
    if cache_key not in _market_metadata_cache:
        try:
            dex_data = api_call({"type": "metaAndAssetCtxs", "dex": dex_name})
            collateral_id = dex_data[0].get("collateralToken", 0)
            token_mapping = get_token_id_to_name()
            _market_metadata_cache[cache_key] = token_mapping.get(collateral_id, "USDC")
        except Exception:
            # Fallback basé sur les DEX connus
            fallback = {"flx": "USDH", "vntl": "USDH", "xyz": "USDC", "hyna": "USDE"}
            _market_metadata_cache[cache_key] = fallback.get(dex_name, "USDC")
    
    return _market_metadata_cache[cache_key]

def get_spot_pair_quote_asset(pair_index: int) -> str:
    """Récupère dynamiquement le quote asset pour une paire spot"""
    global _market_metadata_cache
    
    cache_key = f"spot_quote_{pair_index}"
    if cache_key not in _market_metadata_cache:
        try:
            spot_meta = api_call({"type": "spotMeta"})
            token_mapping = get_token_id_to_name()
            
            for pair in spot_meta.get("universe", []):
                if pair.get("index") == pair_index:
                    tokens = pair.get("tokens", [])
                    if len(tokens) > 1:
                        quote_id = tokens[1]  # Le 2ème token est le quote
                        _market_metadata_cache[cache_key] = token_mapping.get(quote_id, "USDC")
                    else:
                        _market_metadata_cache[cache_key] = "USDC"
                    break
            else:
                _market_metadata_cache[cache_key] = "USDC"
        except Exception:
            _market_metadata_cache[cache_key] = "USDC"
    
    return _market_metadata_cache[cache_key]

def get_quote_asset_for_coin(coin: str, pair_index: Optional[int] = None) -> str:
    """
    Retourne le quote asset pour un coin donné.
    Récupère dynamiquement depuis l'API.
    
    - Spot (@pair_index) : Dépend de la paire (USDC, USDT, USDH...)
    - Perp Main : USDC
    - Perp HIP-3 (dex:asset) : Dépend du DEX (flx/vntl=USDH, xyz=USDC, hyna=USDE)
    """
    # Spot : commence par "@"
    if coin.startswith("@"):
        if pair_index is not None:
            return get_spot_pair_quote_asset(pair_index)
        return "USDC"
    
    # Perp HIP-3 : contient ":"
    if ":" in coin:
        dex_name = coin.split(":")[0]
        return get_dex_quote_asset(dex_name)
    
    # Perp Main : USDC
    return "USDC"

def get_spot_meta() -> Dict[str, Any]:
    """Récupère les métadonnées spot (pour szDecimals)"""
    return api_call({"type": "spotMeta"})

def get_perp_account_summary(address: str, dex_name: str = "") -> Dict[str, Any]:
    """Récupère le résumé du compte perpétuel de l'utilisateur (positions, marge) pour un DEX spécifique"""
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
        except Exception:
            # Continuer même si un DEX échoue
            continue
    
    return all_positions

def get_perp_meta_and_contexts() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Récupère les métadonnées et les contextes d'actifs (prix, funding, etc.)"""
    payload = {"type": "metaAndAssetCtxs"}
    data = api_call(payload)
    
    perp_meta = data[0]
    asset_contexts = data[1]
    
    asset_ctx_map = {}
    for ctx in asset_contexts:
        if "sName" in ctx:
            asset_ctx_map[ctx["sName"]] = ctx
    
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

# =============================================================================
# EXECUTION DES ORDRES ET LOGIQUE DE REBALANCING
# =============================================================================

def round_price_to_tick(price: float, tick_size: Optional[float] = None) -> float:
    """
    Arrondit le prix au tick size valide.
    Si tick_size est fourni, l'utilise. Sinon, utilise la règle des 5 significant figures.
    """
    if price <= 0:
        return price
    
    if tick_size and tick_size > 0:
        # Arrondir au tick size
        rounded = round(price / tick_size) * tick_size
        # Déterminer le nombre de décimales pour éviter les erreurs de float
        if tick_size >= 1:
            decimals = 0
        else:
            decimals = -int(math.floor(math.log10(tick_size) - 0.001))
        return round(rounded, decimals)
    
    # Fallback: 5 significant figures
    magnitude = math.floor(math.log10(price))
    tick = 10 ** (magnitude - 4)
    rounded = round(price / tick) * tick
    
    if tick >= 1:
        decimals = 0
    else:
        decimals = -int(math.floor(math.log10(tick)))
    
    return round(rounded, decimals)

def get_asset_tick_size(exchange: Exchange, coin: str) -> Optional[float]:
    """
    Récupère le tick size pour un asset depuis le SDK.
    Retourne None si non trouvé.
    """
    try:
        asset_id = exchange.info.name_to_asset(coin)
        # Le SDK stocke les prix decimals qui permettent de calculer le tick size
        px_decimals = exchange.info.asset_to_px_decimals.get(asset_id)
        if px_decimals is not None:
            return 10 ** (-px_decimals)
    except Exception:
        pass
    return None

def get_exchange(private_key: str, use_hip3: bool = False) -> Exchange:
    """
    Retourne une instance Exchange initialisée.
    - use_hip3=False: pour le main DEX (BTC, ETH, HYPE, etc.)
    - use_hip3=True: pour les DEXs HIP-3 (flx:TSLA, vntl:X, etc.)
    
    Utilise un cache pour éviter de recréer l'instance à chaque appel.
    """
    global _exchange_cache
    
    # Créer une clé unique incluant le type d'exchange (main vs hip3)
    cache_key = f"{private_key[:10]}_{'hip3' if use_hip3 else 'main'}"
    
    if cache_key not in _exchange_cache:
        account = Account.from_key(private_key)
        if use_hip3:
            # Exchange pour les DEXs HIP-3
            _exchange_cache[cache_key] = Exchange(
                wallet=account,
                base_url=constants.MAINNET_API_URL,
                perp_dexs=HIP3_DEXS
            )
        else:
            # Exchange pour le main DEX (sans perp_dexs)
            _exchange_cache[cache_key] = Exchange(
                wallet=account,
                base_url=constants.MAINNET_API_URL
            )
    
    return _exchange_cache[cache_key]

def place_order(
    private_key: str,
    coin: str, # Pour spot: "@pair_index", Pour perp: "ASSET_NAME" ou "DEX:ASSET_NAME"
    is_buy: bool,
    size_tokens: float,
    limit_price: float,
    sz_decimals: int,
    is_perp: bool,
    dry_run: bool = False,
    dex: str = ""  # DEX name pour les positions HIP-3 (flx, vntl, etc.)
) -> Tuple[bool, str]:
    """
    Place un ordre spot ou perpétuel IOC.
    Retourne (success, message)
    """
    action = "BUY" if is_buy else "SELL"
    market_type = "PERP" if is_perp else "SPOT"
    dex_label = f"[{dex}]" if dex else ""
    
    try:
        # Déterminer si c'est un asset HIP-3 (contient ":" comme "flx:TSLA")
        is_hip3 = ":" in coin
        
        # Récupérer le bon exchange selon le type d'asset
        exchange = get_exchange(private_key, use_hip3=is_hip3)
        
        # Récupérer sz_decimals et tick_size depuis le SDK (plus fiable)
        sdk_sz_decimals = sz_decimals
        tick_size = None
        try:
            asset_id = exchange.info.name_to_asset(coin)
            sdk_sz_decimals = exchange.info.asset_to_sz_decimals.get(asset_id, sz_decimals)
            tick_size = get_asset_tick_size(exchange, coin)
        except Exception:
            pass
        
        # Arrondir la taille au bon nombre de décimales
        size_rounded = round(size_tokens, sdk_sz_decimals)
        
        # Prix avec 1% de buffer pour garantir l'exécution IOC
        price_with_buffer = limit_price * 1.01 if is_buy else limit_price * 0.99
        
        # Arrondir le prix au tick size (utilise le tick_size du SDK si disponible)
        price_rounded = round_price_to_tick(price_with_buffer, tick_size)
        
        if dry_run:
            return True, f"[DRY RUN] {market_type} {action} {size_rounded} {coin} {dex_label}@ ${price_rounded}"
        
        order_type = {"limit": {"tif": "Ioc"}}
        
        # Pour les positions HIP-3, le coin doit être au format "DEX:ASSET" (ex: "flx:TSLA")
        # Le SDK Hyperliquid détecte automatiquement spot/perp selon le format du coin
        # (spot commence par "@", perp est le nom de l'asset)
        result = exchange.order(
            name=coin,                      # name (peut être "flx:TSLA" pour HIP-3 ou "@pair_index" pour spot)
            is_buy=is_buy,                  # is_buy
            sz=size_rounded,                # sz (float)
            limit_px=price_rounded,         # limit_px (float)
            order_type=order_type,          # order_type IOC
            reduce_only=False               # reduce_only
        )
        
        # Vérifier le résultat
        if result.get("status") == "ok":
            # Vérifier si l'ordre a été rempli ou s'il y a une erreur dans les statuses
            response = result.get("response", {})
            statuses = response.get("data", {}).get("statuses", [])
            if statuses and "error" in statuses[0]:
                return False, f"❌ Erreur {market_type}: {statuses[0]['error']}"
            return True, f"✅ {market_type} {action} exécuté: {result}"
        else:
            return False, f"❌ Erreur {market_type}: {result}"
            
    except Exception as e:
        return False, f"❌ Exception {market_type}: {e}"

class CooldownManager:
    """Gère les cooldowns par token/actif"""
    
    def __init__(self, minutes: int):
        self.cooldown = timedelta(minutes=minutes)
        self.last_orders: Dict[str, datetime] = {}
    
    def can_trade(self, key: str) -> bool:
        if key not in self.last_orders:
            return True
        return datetime.now() - self.last_orders[key] >= self.cooldown
    
    def record(self, key: str):
        self.last_orders[key] = datetime.now()
    
    def remaining(self, key: str) -> float:
        if key not in self.last_orders:
            return 0
        elapsed = datetime.now() - self.last_orders[key]
        return max(0, (self.cooldown - elapsed).total_seconds())

def check_rebalance(current_usd: float, target_usd: float, 
                    buy_threshold: float, sell_threshold: float,
                    buy_enabled: bool, sell_enabled: bool) -> Optional[str]:
    """
    Vérifie si un rebalance est nécessaire.
    Retourne "buy", "sell" ou None.
    """
    if target_usd <= 0:
        return None
    
    buy_trigger = target_usd * (1 - buy_threshold / 100)
    sell_trigger = target_usd * (1 + sell_threshold / 100)
    
    if current_usd <= buy_trigger and buy_enabled:
        return "buy"
    if current_usd >= sell_trigger and sell_enabled:
        return "sell"
    
    return None

# =============================================================================
# WALLET MANAGER
# =============================================================================

class WalletBot:
    """Bot pour un wallet individuel"""
    
    def __init__(self, wallet_id: int, config: Dict, dry_run: bool = False):
        self.wallet_id = wallet_id
        self.config = config
        self.dry_run = dry_run
        
        # Récupération des clés/adresses
        self.address = os.getenv(f"HL_ADDRESS_{wallet_id}")
        self.private_key = os.getenv(f"HL_PRIVATE_KEY_{wallet_id}")
        
        if not self.address or not self.private_key:
            raise ValueError(f"HL_ADDRESS_{wallet_id} ou HL_PRIVATE_KEY_{wallet_id} non configuré dans les variables d'environnement.")
        
        settings = config.get("settings", {})
        self.order_size = settings.get("order_size_usd", 11)
        self.cooldown_min = settings.get("cooldown_minutes", 15)
        self.check_interval = settings.get("check_interval_seconds", 60)
        
        self.cooldowns = CooldownManager(self.cooldown_min)
    
    def run_cycle(self):
        """Exécute un cycle de rebalancing (Spot et Futures)"""
        print(f"\n{'='*60}")
        print(f"🔄 Wallet {self.wallet_id} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"   {self.address[:10]}...{self.address[-6:]}")
        print(f"{'='*60}")
        
        # 1. Récupérer les données de marché (Spot et Perpétuels)
        try:
            mids = get_all_mids()
            spot_meta = get_spot_meta()
            all_perp_positions = get_all_perp_positions(self.address)
            perp_meta, asset_ctx_map = get_perp_meta_and_contexts()
            balances = get_spot_balances(self.address)
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion à l'API Hyperliquid: {e}")
            return
        
        # Afficher les balances des stablecoins disponibles
        usdc = balances.get("USDC", 0)
        usdh = balances.get("USDH", 0)
        usde = balances.get("USDE", 0)
        usdt = balances.get("USDT", 0)
        stables = []
        if usdc > 0: stables.append(f"USDC: ${usdc:.2f}")
        if usdh > 0: stables.append(f"USDH: ${usdh:.2f}")
        if usde > 0: stables.append(f"USDE: ${usde:.2f}")
        if usdt > 0: stables.append(f"USDT: ${usdt:.2f}")
        print(f"\n💵 Balances: {' | '.join(stables) if stables else 'Aucun stablecoin'}")
        
        # 2. Gérer le rebalancing Spot
        self._rebalance_spot(balances, mids, spot_meta)
        
        # 3. Gérer le rebalancing Futures (tous DEX inclus)
        self._rebalance_perpetuals(all_perp_positions, perp_meta, asset_ctx_map, balances, mids)
        
    def _rebalance_spot(self, balances: Dict, mids: Dict, spot_meta: Dict):
        """Logique de rebalancing pour les tokens Spot"""
        print("\n--- Rebalancing Spot ---")
        
        tokens_config = self.config.get("spot_tokens", {})
        
        for token, tc in tokens_config.items():
            if not tc.get("enabled", False):
                continue
            
            # Récupérer les infos du token
            pair_index = tc.get("pair_index")
            sz_decimals = tc.get("sz_decimals")
            
            if pair_index is None or sz_decimals is None:
                print(f"\n⚠️  {token}: Métadonnées manquantes, lancez autoconfig.py. Skip.")
                continue
            
            # Calculer la valeur actuelle
            amount = balances.get(token, 0)
            price_key = f"@{pair_index}"
            price = mids.get(price_key, mids.get(token, 0))
            current_usd = amount * price
            
            target_usd = tc.get("hold_usd", 0)
            deviation = ((current_usd - target_usd) / target_usd * 100) if target_usd > 0 else 0
            
            # Récupérer le quote asset pour cette paire
            coin_key = f"@{pair_index}"
            quote_asset = get_quote_asset_for_coin(coin_key, pair_index)
            quote_balance = balances.get(quote_asset, 0)
            
            # Affichage status
            emoji = "🟢" if abs(deviation) <= 10 else ("🟡" if abs(deviation) <= 30 else "🔴")
            print(f"\n{emoji} {token} (Spot / {quote_asset}):")
            print(f"   {amount:.6f} @ ${price:.4f} = ${current_usd:.2f} | Target: ${target_usd:.2f} ({deviation:+.1f}%)")
            
            # Vérifier cooldown
            if not self.cooldowns.can_trade(token):
                remaining = self.cooldowns.remaining(token) / 60
                print(f"   ⏳ Cooldown: {remaining:.1f}min")
                continue
            
            # Vérifier si action nécessaire
            action = check_rebalance(
                current_usd, target_usd,
                tc.get("buy_threshold_pct", 50),
                tc.get("sell_threshold_pct", 50),
                tc.get("buy_enabled", False),
                tc.get("sell_enabled", True)
            )
            
            if action:
                is_buy = action == "buy"
                
                # Vérifier les balances pour l'achat (utilise le bon quote asset)
                if is_buy and quote_balance < self.order_size:
                    print(f"   ⚠️  {quote_asset} insuffisant (${quote_balance:.2f} < ${self.order_size})")
                    continue
                
                # Calculer la taille de l'ordre
                size_tokens = self.order_size / price
                
                # Placer l'ordre
                success, msg = place_order(
                    self.private_key,
                    coin_key,
                    is_buy,
                    size_tokens,
                    price,
                    sz_decimals,
                    is_perp=False,
                    dry_run=self.dry_run
                )
                print(f"   🎯 {action.upper()} {size_tokens:.6f} {token} ({quote_asset}): {msg}")
                if success:
                    self.cooldowns.record(token)
            else:
                print(f"   ✓ OK")

    def _rebalance_perpetuals(self, all_perp_positions: List[Tuple[str, Dict]], perp_meta: Dict, asset_ctx_map: Dict, balances: Dict[str, float], mids: Dict[str, float]):
        """Logique de rebalancing pour les contrats perpétuels (tous DEX inclus)"""
        print("\n--- Rebalancing Futures (Main + HIP-3) ---")
        
        # Configuration des perpétuels
        perpetuals_config = self.config.get("perpetuals", {})
        
        # Créer un dictionnaire des positions ouvertes par (dex, asset_name)
        # Format: {(dex_name, asset_name): position_data}
        open_positions = {}
        for dex_name, pos in all_perp_positions:
            asset_name = pos.get("coin", "")
            if asset_name:
                open_positions[(dex_name, asset_name)] = pos
        
        # Parcourir la configuration pour les actifs à gérer
        for asset_name, tc in perpetuals_config.items():
            if not tc.get("enabled", False):
                continue
            
            # Récupérer les métadonnées de la config
            sz_decimals = tc.get("sz_decimals")
            config_dex = tc.get("dex", "")  # DEX stocké dans la config ("" pour main)
            
            if sz_decimals is None:
                print(f"\n⚠️  {asset_name}: Métadonnées manquantes, lancez autoconfig.py. Skip.")
                continue
            
            # Extraire le nom d'asset "pur" (sans préfixe dex) pour la recherche
            # Ex: "flx:TSLA" -> "TSLA", "BTC" -> "BTC"
            if ":" in asset_name:
                pure_asset_name = asset_name.split(":")[-1]  # Prend la partie après le ":"
            else:
                pure_asset_name = asset_name
            
            # Trouver la position correspondante (chercher d'abord avec le DEX de la config, puis sans DEX)
            pos = None
            dex_name = config_dex if config_dex else "main"
            
            # Essayer avec le DEX de la config et le nom pur
            if (dex_name, pure_asset_name) in open_positions:
                pos = open_positions[(dex_name, pure_asset_name)]
            # Essayer avec le nom complet (au cas où l'API retourne avec préfixe)
            elif (dex_name, asset_name) in open_positions:
                pos = open_positions[(dex_name, asset_name)]
            else:
                # Essayer sans DEX (main)
                if ("main", pure_asset_name) in open_positions:
                    pos = open_positions[("main", pure_asset_name)]
                    dex_name = "main"
                elif ("main", asset_name) in open_positions:
                    pos = open_positions[("main", asset_name)]
                    dex_name = "main"
                else:
                    # Chercher dans tous les DEX (au cas où le DEX aurait changé)
                    for (d, a), p in open_positions.items():
                        if a == pure_asset_name or a == asset_name:
                            pos = p
                            dex_name = d
                            break
            
            szi = float(pos.get("szi", 0)) if pos else 0
            
            # Récupérer le prix d'entrée et le PnL non réalisé depuis la position
            entry_price = float(pos.get("entryPx", 0)) if pos else 0
            unrealized_pnl = float(pos.get("unrealizedPnl", 0)) if pos else 0
            
            # Récupérer le prix mark - PRIORITÉ aux mids (plus fiable et à jour)
            mark_price = 0
            
            # 1. Essayer depuis mids avec le nom complet (ex: "flx:TSLA" pour HIP-3)
            if asset_name in mids:
                mark_price = mids[asset_name]
            # 2. Essayer avec le format dex:asset si pas déjà dans ce format
            elif dex_name != "main" and f"{dex_name}:{pure_asset_name}" in mids:
                mark_price = mids[f"{dex_name}:{pure_asset_name}"]
            # 3. Essayer avec le nom pur (pour main DEX)
            elif pure_asset_name in mids:
                mark_price = mids[pure_asset_name]
            # 4. Fallback: asset_ctx_map
            if mark_price == 0:
                asset_ctx = asset_ctx_map.get(pure_asset_name, asset_ctx_map.get(asset_name, {}))
                mark_price = float(asset_ctx.get("markPx", 0))
            
            # 5. Si pas de prix, essayer depuis la position
            if mark_price == 0 and pos:
                mark_from_pos = pos.get("markPx", 0)
                if mark_from_pos and mark_from_pos != "N/A":
                    try:
                        mark_price = float(mark_from_pos)
                    except (ValueError, TypeError):
                        pass
            
            # 6. CALCUL INTELLIGENT: Déduire le mark_price à partir du unrealized_pnl
            # Pour long: pnl = szi * (mark - entry) => mark = entry + (pnl / szi)
            # Pour short: pnl = szi * (entry - mark) => mark = entry - (pnl / abs(szi))
            if mark_price == 0 and entry_price > 0 and abs(szi) > 0 and unrealized_pnl != 0:
                if szi > 0:  # Position long
                    mark_price = entry_price + (unrealized_pnl / szi)
                else:  # Position short
                    mark_price = entry_price - (unrealized_pnl / abs(szi))
            
            # 7. Dernier recours: utiliser le prix d'entrée (seulement si pas de PnL)
            if mark_price == 0 and entry_price > 0:
                mark_price = entry_price
            
            if mark_price == 0:
                print(f"\n⚠️  {asset_name}: Prix mark non disponible. Skip.")
                continue
            
            # Calculer le PnL en pourcentage
            # Méthode 1: Basé sur unrealized_pnl de l'API (plus précis, inclut funding)
            # PnL % = unrealized_pnl / valeur_initiale_position
            initial_value = abs(szi) * entry_price if entry_price > 0 else 0
            if initial_value > 0 and unrealized_pnl != 0:
                pnl_pct = (unrealized_pnl / initial_value) * 100
            # Méthode 2: Fallback basé sur entry vs mark price
            elif entry_price > 0 and mark_price > 0:
                pnl_pct = ((mark_price - entry_price) / entry_price) * 100
                if szi < 0:  # Position short: PnL inversé
                    pnl_pct = -pnl_pct
            else:
                pnl_pct = 0
            
            # Valeur notionnelle actuelle (Current Notional Value)
            current_notional_usd = abs(szi) * mark_price
            target_usd = tc.get("hold_usd", 0)
            
            if target_usd <= 0:
                print(f"   [SKIP] {asset_name}: hold_usd <= 0.")
                continue
            
            # Calcul de la déviation
            deviation = ((current_notional_usd - target_usd) / target_usd * 100) if target_usd > 0 else 0
            
            # Affichage status
            emoji = "🟢" if abs(deviation) <= 10 else ("🟡" if abs(deviation) <= 30 else "🔴")
            dex_label = f"[{dex_name}]" if dex_name != "main" else "[Main]"
            print(f"\n{emoji} {asset_name} {dex_label} (Future):")
            print(f"   Position: {szi:.6f} @ ${mark_price:.4f} = ${current_notional_usd:.2f} (Notional)")
            print(f"   Entry: ${entry_price:.4f} | Mark: ${mark_price:.4f}")
            # Afficher le PnL en USD et en %
            pnl_emoji = "📈" if unrealized_pnl >= 0 else "📉"
            print(f"   {pnl_emoji} PnL: ${unrealized_pnl:+.2f} ({pnl_pct:+.2f}%) | Target: ${target_usd:.2f} ({deviation:+.1f}%)")
            
            # Vérifier cooldown
            if not self.cooldowns.can_trade(asset_name):
                remaining = self.cooldowns.remaining(asset_name) / 60
                print(f"   ⏳ Cooldown: {remaining:.1f}min")
                continue
            
            # Vérifier si action nécessaire
            action = check_rebalance(
                current_notional_usd, target_usd,
                tc.get("buy_threshold_pct", 50),
                tc.get("sell_threshold_pct", 50),
                tc.get("buy_enabled", False),
                tc.get("sell_enabled", True)
            )
            
            if action:
                # Construire le nom du coin pour l'ordre (pour HIP-3: "dex:asset", sinon juste "asset")
                # Vérifier si asset_name contient déjà le préfixe du dex (ex: "flx:TSLA")
                if dex_name != "main" and dex_name and not asset_name.startswith(f"{dex_name}:"):
                    coin_for_order = f"{dex_name}:{asset_name}"
                else:
                    coin_for_order = asset_name
                
                # Déterminer le quote asset pour cet ordre
                quote_asset = get_quote_asset_for_coin(coin_for_order)
                quote_balance = balances.get(quote_asset, 0)
                
                # Vérifier si on a assez de quote asset pour un achat
                is_buy = action == "buy"
                if is_buy and quote_balance < self.order_size:
                    print(f"   ⚠️  {quote_asset} insuffisant (${quote_balance:.2f} < ${self.order_size})")
                    continue
                
                # SÉCURITÉ: Ne pas vendre si le PnL est négatif (éviter de cristalliser les pertes)
                if not is_buy and unrealized_pnl < 0:
                    print(f"   🛡️  PROTECTION: Vente bloquée (PnL négatif: ${unrealized_pnl:.2f})")
                    print(f"      → Attente d'un break-even ou PnL positif avant de vendre")
                    continue
                
                # Calculer la taille de l'ordre pour ramener la valeur notionnelle à target_usd
                
                # Taille de l'ordre en USD (valeur notionnelle)
                order_notional_usd = self.order_size
                
                # Taille de l'ordre en tokens (sz)
                size_tokens = order_notional_usd / mark_price
                
                # Placer l'ordre
                success, msg = place_order(
                    self.private_key,
                    coin_for_order,
                    is_buy,
                    size_tokens,
                    mark_price,
                    sz_decimals,
                    is_perp=True,
                    dry_run=self.dry_run,
                    dex=dex_name if dex_name != "main" else ""
                )
                print(f"   🎯 {action.upper()} {size_tokens:.6f} {coin_for_order} ({quote_asset}): {msg}")
                if success:
                    self.cooldowns.record(asset_name)
            else:
                print(f"   ✓ OK")

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Hyperliquid Rebalancer V2 (Spot & Futures)")
    parser.add_argument("--dry-run", action="store_true", help="Mode simulation (pas d'ordres réels)")
    parser.add_argument("--wallet", type=int, help="Lance uniquement un wallet spécifique (ID)")
    args = parser.parse_args()
    
    # Déterminer les wallets à traiter
    wallet_ids = []
    if args.wallet:
        wallet_ids.append(args.wallet)
    else:
        # Chercher les variables d'environnement HL_ADDRESS_X
        i = 1
        while os.getenv(f"HL_ADDRESS_{i}"):
            wallet_ids.append(i)
            i += 1
    
    if not wallet_ids:
        print("❌ Aucun wallet trouvé. Assurez-vous que HL_ADDRESS_1, HL_PRIVATE_KEY_1, etc., sont définis.")
        return

    print("--- Mode Exécution du Bot ---")
    
    # Boucle principale du bot
    bots = []
    for wid in wallet_ids:
        try:
            config = load_config(wid)
            bot = WalletBot(wid, config, args.dry_run)
            bots.append(bot)
        except FileNotFoundError:
            print(f"❌ Fichier de configuration config_wallet_{wid}.json non trouvé. Lancez 'python autoconfig.py' d'abord.")
        except Exception as e:
            print(f"❌ Erreur lors du chargement/initialisation pour Wallet {wid}: {e}")
            
    if not bots:
        print("❌ Aucun bot n'a pu être initialisé. Vérifiez les configurations et les variables d'environnement.")
        return
        
    while True:
        for bot in bots:
            try:
                bot.run_cycle()
            except Exception as e:
                print(f"❌ Erreur critique dans le cycle du Wallet {bot.wallet_id}: {e}")
                
        # Attendre l'intervalle de vérification (on prend le max des intervalles)
        max_interval = max(bot.check_interval for bot in bots)
        print(f"\n[GLOBAL] Attente de {max_interval} secondes avant le prochain cycle...")
        time.sleep(max_interval)

if __name__ == "__main__":
    main()
