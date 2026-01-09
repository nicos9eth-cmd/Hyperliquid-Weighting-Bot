# CLAUDE.md - Guide pour le développement

## Vue d'ensemble du projet

**Hyperliquid Weighting Bot** est un bot de rééquilibrage automatique pour la plateforme de trading [Hyperliquid](https://app.hyperliquid.xyz). Il maintient des positions pondérées sur les actifs Spot et Perpétuels (Futures) avec un levier de 1x.

## Architecture du projet

```
Hyperliquid-Weighting-Bot/
├── bot.py              # Bot principal - boucle de rééquilibrage
├── autoconfig.py       # Générateur de configuration automatique
├── meta.py             # Module utilitaire pour les métadonnées
├── .env                # Variables d'environnement (clés privées) - NON VERSIONNÉ
├── .env.example        # Template pour .env
├── config_wallet_X.json # Configuration par wallet (généré par autoconfig.py)
├── README.md           # Documentation utilisateur
├── CLAUDE.md           # Ce fichier - guide développeur
└── LICENSE.txt         # Licence MIT
```

## Commandes de développement

```bash
# Installation des dépendances
pip install hyperliquid-python-sdk eth-account python-dotenv requests

# Générer la configuration (détecte les positions existantes)
python autoconfig.py

# Lancer le bot en mode simulation (pas d'ordres réels)
python bot.py --dry-run

# Lancer le bot normalement
python bot.py

# Lancer uniquement un wallet spécifique
python bot.py --wallet 1
```

## Flux de travail principal

1. L'utilisateur configure ses clés dans `.env` (HL_ADDRESS_X, HL_PRIVATE_KEY_X)
2. `autoconfig.py` détecte les positions et génère `config_wallet_X.json`
3. L'utilisateur édite la config pour définir ses targets (`hold_usd`, seuils, etc.)
4. `bot.py` exécute une boucle infinie de rééquilibrage

## Composants clés du code

### bot.py

- **`WalletBot`** : Classe principale gérant un wallet
  - `run_cycle()` : Exécute un cycle de rééquilibrage
  - `_rebalance_spot()` : Logique pour les tokens Spot
  - `_rebalance_perpetuals()` : Logique pour les Futures

- **`CooldownManager`** : Gère les cooldowns par actif pour éviter le spam d'ordres

- **`place_order()`** : Place les ordres IOC (Immediate Or Cancel) via le SDK

- **`check_rebalance()`** : Détermine si un achat/vente est nécessaire

### autoconfig.py

- Détecte automatiquement toutes les positions (Spot + Futures)
- Supporte le main DEX et les HIP-3 DEXs (flx, hyna, vntl, xyz)
- Génère `config_wallet_X.json` avec les métadonnées appropriées

## Structure de configuration (config_wallet_X.json)

```json
{
  "settings": {
    "order_size_usd": 15,           // Taille des ordres en USD
    "cooldown_minutes": 15,          // Délai entre ordres sur même actif
    "check_interval_seconds": 100,   // Intervalle entre cycles
    "dry_run": false                 // Mode simulation
  },
  "spot_tokens": {
    "BTC": {
      "enabled": true,               // Activer le rééquilibrage
      "hold_usd": 1000,              // Valeur cible en USD
      "buy_threshold_pct": 16,       // Seuil d'achat (% sous la cible)
      "sell_threshold_pct": 16,      // Seuil de vente (% au-dessus)
      "pair_index": 5,               // Index de la paire Spot
      "sz_decimals": 8,              // Décimales pour la taille
      "quote_asset": "USDC"          // Actif de cotation
    }
  },
  "perpetuals": {
    "BTC": {
      "enabled": true,
      "hold_usd": 5000,              // Valeur notionnelle cible
      "dex": "",                     // "" pour main DEX
      "quote_asset": "USDC"
    },
    "flx:TSLA": {
      "dex": "flx",                  // DEX HIP-3
      "quote_asset": "USDH"          // Collatéral HIP-3
    }
  }
}
```

## API Hyperliquid utilisées

- **`allMids`** : Prix mid de tous les actifs
- **`spotClearinghouseState`** : Balances Spot d'un utilisateur
- **`clearinghouseState`** : Positions Futures d'un utilisateur
- **`spotMeta`** : Métadonnées des paires Spot
- **`metaAndAssetCtxs`** : Métadonnées et contextes des actifs Futures

## Logique de rééquilibrage

### Déclencheurs d'achat/vente

```
ACHAT si : valeur_actuelle <= valeur_cible × (1 - buy_threshold_pct%)
VENTE si : valeur_actuelle >= valeur_cible × (1 + sell_threshold_pct%)
```

### Sécurités intégrées

1. **Cooldown** : Empêche les ordres répétitifs sur un même actif
2. **Protection pertes** : Bloque la vente si PnL négatif (Futures)
3. **Vérification balance** : S'assure que le quote asset est suffisant
4. **Mode dry-run** : Simule sans exécuter d'ordres réels

## DEXs supportés

| DEX | Type | Quote Asset |
|-----|------|-------------|
| Main | Principal | USDC |
| flx | HIP-3 | USDH |
| vntl | HIP-3 | USDH |
| xyz | HIP-3 | USDC |
| hyna | HIP-3 | USDE |

## Points d'attention pour les modifications

1. **Ordres** : Utiliser des ordres IOC avec buffer de prix (+/- 1%)
2. **Décimales** : Respecter `sz_decimals` et `tick_size` de chaque actif
3. **HIP-3** : Le format des coins est `DEX:ASSET` (ex: `flx:TSLA`)
4. **Quote assets** : Varient selon le DEX, récupérer dynamiquement via API
5. **Cache** : Les métadonnées sont cachées pour performance

## Tests

Pour tester des modifications :

```bash
# Toujours tester en dry-run d'abord
python bot.py --dry-run --wallet 1

# Vérifier les logs pour s'assurer du bon fonctionnement
```

## Variables d'environnement requises

```bash
HL_ADDRESS_1=0x...     # Adresse du wallet 1
HL_PRIVATE_KEY_1=0x... # Clé privée du wallet 1

# Wallets additionnels (optionnel)
HL_ADDRESS_2=0x...
HL_PRIVATE_KEY_2=0x...
```

## Dépendances Python

- `hyperliquid-python-sdk` : SDK officiel Hyperliquid
- `eth-account` : Gestion des comptes Ethereum (signatures)
- `python-dotenv` : Chargement des variables d'environnement
- `requests` : Appels API HTTP
