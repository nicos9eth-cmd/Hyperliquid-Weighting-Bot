<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot">
    <img src="https://hyperliquid.gitbook.io/hyperliquid-docs/~gitbook/image?url=https%3A%2F%2F2356094849-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252FyUdp569E6w18GdfqlGvJ%252Ficon%252FsIAjqhKKIUysM08ahKPh%252FHL-logoSwitchDISliStat.png%3Falt%3Dmedia%26token%3Da81fa25c-0510-4d97-87ff-3fb8944935b1&width=32&dpr=4&quality=100&sign=3e1219e3&sv=2" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Hyperliquid Weighting Bot</h3>

  <p align="center">
    Un bot de rééquilibrage automatique pour Hyperliquid.
    <br />
    <a href="https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot"><strong>Explorer les docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot/issues">Signaler un bug</a>
    ·
    <a href="https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot/issues">Demander une fonctionnalité</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table des matières / Table of Contents</summary>
  <ol>
    <li>
      <a href="#-français">Français</a>
      <ul>
        <li><a href="#présentation">Présentation</a></li>
        <li><a href="#fonctionnalités">Fonctionnalités</a></li>
        <li><a href="#prérequis">Prérequis</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#configuration-du-fichier-env">Configuration .env</a></li>
        <li><a href="#configuration-du-fichier-config_wallet_xjson">Configuration config.json</a></li>
        <li><a href="#utilisation">Utilisation</a></li>
        <li><a href="#exemples-de-stratégies">Exemples de stratégies</a></li>
      </ul>
    </li>
    <li>
      <a href="#-english">English</a>
      <ul>
        <li><a href="#overview">Overview</a></li>
        <li><a href="#features">Features</a></li>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation-1">Installation</a></li>
        <li><a href="#env-file-configuration">Configuration .env</a></li>
        <li><a href="#config_wallet_xjson-configuration">Configuration config.json</a></li>
        <li><a href="#usage">Usage</a></li>
        <li><a href="#strategy-examples">Strategy Examples</a></li>
      </ul>
    </li>
    <li><a href="#avertissement--disclaimer">Avertissement / Disclaimer</a></li>
    <li><a href="#licence">Licence</a></li>
  </ol>
</details>

---

## 🇫🇷 Français

<a name="présentation"></a>
### Présentation

Ce bot est un outil de **rééquilibrage (weighting)** automatique pour [Hyperliquid](https://app.hyperliquid.xyz/join/NICOS9). Il permet de maintenir des positions pondérées sur vos actifs Spot et Perpétuels (Futures) avec un levier de x1.

**Comment ça fonctionne ?**

1. Vous définissez une valeur cible en USD pour chaque actif (`hold_usd`)
2. Vous définissez des seuils de déclenchement (`buy_threshold_pct`, `sell_threshold_pct`)
3. Le bot surveille vos positions et rééquilibre automatiquement :
   - **Achète** si la valeur tombe sous le seuil inférieur
   - **Vend** si la valeur dépasse le seuil supérieur

> 🎁 **Bonus de parrainage** : Utilisez mon code de parrainage pour bénéficier de **4% de réduction** sur tous vos frais de trading : [https://app.hyperliquid.xyz/join/NICOS9](https://app.hyperliquid.xyz/join/NICOS9)

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="fonctionnalités"></a>
### Fonctionnalités

- **Auto-détection** : Identifie automatiquement vos positions Spot, Perpétuels et HIP-3
- **Multi-wallet** : Gérez plusieurs portefeuilles simultanément
- **Pondération intelligente** : Rééquilibre vos positions selon vos paramètres cibles
- **Support HIP-3** : Compatible avec les DEXs HIP-3 (flx, hyna, vntl, xyz)
- **Multi-collatéral** : Supporte USDC, USDH, USDE et USDT comme quote assets
- **Protection des pertes** : Bloque automatiquement la vente si votre PnL est négatif
- **Mode simulation** : Testez votre configuration sans exécuter d'ordres réels

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="prérequis"></a>
### Prérequis

- Python 3.7 ou supérieur
- Un compte Hyperliquid avec des positions ouvertes
- Votre clé privée de wallet (gardez-la secrète !)

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="installation"></a>
### Installation

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot.git
   cd Hyperliquid-Weighting-Bot
   ```

2. **Installer les dépendances** :
   ```bash
   pip install hyperliquid-python-sdk eth-account python-dotenv requests
   ```

3. **Créer le fichier .env** :
   ```bash
   cp .env.example .env
   ```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="configuration-du-fichier-env"></a>
### Configuration du fichier .env

Ouvrez le fichier `.env` avec votre éditeur de texte et ajoutez vos informations :

```bash
# Wallet 1 (obligatoire)
HL_ADDRESS_1=0xVotreAdresseWallet
HL_PRIVATE_KEY_1=0xVotreClePrivee

# Wallet 2 (optionnel)
HL_ADDRESS_2=0xDeuxiemeAdresse
HL_PRIVATE_KEY_2=0xDeuxiemeCle

# Ajoutez autant de wallets que nécessaire (3, 4, 5...)
```

> ⚠️ **SÉCURITÉ** : Ne partagez JAMAIS votre clé privée. Le fichier `.env` ne doit jamais être versionné sur Git.

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="configuration-du-fichier-config_wallet_xjson"></a>
### Configuration du fichier config_wallet_X.json

#### Étape 1 : Générer la configuration automatiquement

```bash
python autoconfig.py
```

Cette commande analyse votre wallet et génère un fichier `config_wallet_1.json` (et `config_wallet_2.json`, etc. si vous avez plusieurs wallets).

#### Étape 2 : Comprendre la structure du fichier

Voici un exemple complet de fichier de configuration avec explications :

```json
{
  "settings": {
    "order_size_usd": 15,
    "cooldown_minutes": 15,
    "check_interval_seconds": 100,
    "default_fee_pct": 0.07,
    "dry_run": false
  },
  "spot_tokens": {
    "BTC": {
      "enabled": false,
      "hold_usd": 1000,
      "buy_enabled": true,
      "sell_enabled": true,
      "buy_threshold_pct": 16,
      "sell_threshold_pct": 16,
      "fee_pct": 0.07,
      "pair_index": 5,
      "sz_decimals": 8,
      "price_decimals": 6,
      "quote_asset": "USDC"
    }
  },
  "perpetuals": {
    "BTC": {
      "enabled": false,
      "hold_usd": 5000,
      "buy_enabled": true,
      "sell_enabled": true,
      "buy_threshold_pct": 16,
      "sell_threshold_pct": 16,
      "fee_pct": 0.07,
      "sz_decimals": 8,
      "dex": "",
      "quote_asset": "USDC"
    }
  }
}
```

#### Étape 3 : Comprendre chaque paramètre

##### Section `settings` - Paramètres globaux

| Paramètre | Description | Valeur conseillée |
|-----------|-------------|-------------------|
| `order_size_usd` | Taille de chaque ordre de rééquilibrage en USD | 10-50 USD |
| `cooldown_minutes` | Temps minimum entre deux ordres sur le même actif | 15-30 min |
| `check_interval_seconds` | Intervalle entre chaque cycle de vérification | 60-300 sec |
| `default_fee_pct` | Frais de trading par défaut (informatif) | 0.07 |
| `dry_run` | Mode simulation (pas d'ordres réels) | false |

##### Section `spot_tokens` / `perpetuals` - Configuration par actif

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `enabled` | **Active ou désactive** le rééquilibrage pour cet actif | `true` / `false` |
| `hold_usd` | **Valeur cible** en USD que vous souhaitez maintenir | `1000` |
| `buy_enabled` | Autorise les ordres d'achat | `true` |
| `sell_enabled` | Autorise les ordres de vente | `true` |
| `buy_threshold_pct` | % en dessous de la cible déclenchant un achat | `16` |
| `sell_threshold_pct` | % au-dessus de la cible déclenchant une vente | `16` |
| `dex` | DEX pour les Futures (`""` = main, `"flx"`, `"vntl"`, etc.) | `""` |
| `quote_asset` | Monnaie de cotation (auto-détecté) | `"USDC"` |

> **Note** : Les paramètres `pair_index`, `sz_decimals`, `price_decimals` et `quote_asset` sont générés automatiquement par `autoconfig.py`. Ne les modifiez pas manuellement.

#### Étape 4 : Configurer vos objectifs

**Exemple : Vous voulez maintenir 1000$ de BTC Spot avec +/- 16% de tolérance**

```json
"BTC": {
  "enabled": true,           // Activer le rééquilibrage
  "hold_usd": 1000,          // Cible: 1000$
  "buy_enabled": true,       // Autoriser les achats
  "sell_enabled": true,      // Autoriser les ventes
  "buy_threshold_pct": 16,   // Acheter si valeur < 840$ (1000 × 0.84)
  "sell_threshold_pct": 16,  // Vendre si valeur > 1160$ (1000 × 1.16)
  ...
}
```

**Visualisation des seuils :**
```
                    VENTE déclenchée
                         ↓
    |-------|--------[1160$]------->
    |       |         +16%
    |       |
    |  [1000$] ← Valeur cible (hold_usd)
    |       |
    |       |         -16%
    |-------v--------[840$]-------->
                         ↑
                    ACHAT déclenché
```

#### Étape 5 : Activer les actifs souhaités

Après avoir ajusté `hold_usd` et les seuils, **mettez `enabled` à `true`** pour chaque actif que vous souhaitez rééquilibrer :

```json
"BTC": {
  "enabled": true,    // ← Changez de false à true
  "hold_usd": 1000,
  ...
}
```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="utilisation"></a>
### Utilisation

1. **Tester en mode simulation** (fortement recommandé) :
   ```bash
   python bot.py --dry-run
   ```
   Vérifiez les logs pour vous assurer que le bot fonctionne comme prévu.

2. **Lancer le bot en mode réel** :
   ```bash
   python bot.py
   ```

3. **Lancer pour un seul wallet** :
   ```bash
   python bot.py --wallet 1
   ```

4. **Régénérer la configuration** (si nouvelles positions) :
   ```bash
   python autoconfig.py
   ```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="exemples-de-stratégies"></a>
### Exemples de stratégies

#### Stratégie 1 : Portfolio équilibré (conservateur)

```json
{
  "settings": {
    "order_size_usd": 20,
    "cooldown_minutes": 30,
    "check_interval_seconds": 180
  },
  "spot_tokens": {
    "BTC": { "enabled": true, "hold_usd": 2000, "buy_threshold_pct": 20, "sell_threshold_pct": 20 },
    "ETH": { "enabled": true, "hold_usd": 1500, "buy_threshold_pct": 20, "sell_threshold_pct": 20 },
    "HYPE": { "enabled": true, "hold_usd": 500, "buy_threshold_pct": 20, "sell_threshold_pct": 20 }
  }
}
```

#### Stratégie 2 : Trading actif (agressif)

```json
{
  "settings": {
    "order_size_usd": 10,
    "cooldown_minutes": 10,
    "check_interval_seconds": 60
  },
  "perpetuals": {
    "BTC": { "enabled": true, "hold_usd": 5000, "buy_threshold_pct": 10, "sell_threshold_pct": 10 },
    "ETH": { "enabled": true, "hold_usd": 3000, "buy_threshold_pct": 10, "sell_threshold_pct": 10 }
  }
}
```

#### Stratégie 3 : Accumulation uniquement (DCA)

```json
{
  "spot_tokens": {
    "BTC": {
      "enabled": true,
      "hold_usd": 10000,
      "buy_enabled": true,
      "sell_enabled": false,    // Désactiver les ventes
      "buy_threshold_pct": 5,   // Acheter dès -5%
      "sell_threshold_pct": 100 // Ne jamais vendre
    }
  }
}
```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

---

## 🇺🇸 English

<a name="overview"></a>
### Overview

This bot is an automatic **rebalancing (weighting)** tool for [Hyperliquid](https://app.hyperliquid.xyz/join/NICOS9). It helps maintain weighted positions on your Spot and Perpetual (Futures) assets with 1x leverage.

**How does it work?**

1. You define a target USD value for each asset (`hold_usd`)
2. You define trigger thresholds (`buy_threshold_pct`, `sell_threshold_pct`)
3. The bot monitors your positions and automatically rebalances:
   - **Buys** if the value falls below the lower threshold
   - **Sells** if the value exceeds the upper threshold

> 🎁 **Referral Bonus**: Use my referral link to get a **4% discount** on all your trading fees: [https://app.hyperliquid.xyz/join/NICOS9](https://app.hyperliquid.xyz/join/NICOS9)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a name="features"></a>
### Features

- **Auto-detection**: Automatically identifies Spot, Perpetual, and HIP-3 positions
- **Multi-wallet**: Manage multiple wallets simultaneously
- **Smart Weighting**: Rebalances your positions according to your target settings
- **HIP-3 Support**: Compatible with HIP-3 DEXs (flx, hyna, vntl, xyz)
- **Multi-collateral**: Supports USDC, USDH, USDE, and USDT as quote assets
- **Loss Protection**: Automatically blocks selling if your PnL is negative
- **Simulation Mode**: Test your configuration without executing real orders

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a name="prerequisites"></a>
### Prerequisites

- Python 3.7 or higher
- A Hyperliquid account with open positions
- Your wallet private key (keep it secret!)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a name="installation-1"></a>
### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot.git
   cd Hyperliquid-Weighting-Bot
   ```

2. **Install dependencies**:
   ```bash
   pip install hyperliquid-python-sdk eth-account python-dotenv requests
   ```

3. **Create the .env file**:
   ```bash
   cp .env.example .env
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a name="env-file-configuration"></a>
### .env File Configuration

Open the `.env` file with your text editor and add your information:

```bash
# Wallet 1 (required)
HL_ADDRESS_1=0xYourWalletAddress
HL_PRIVATE_KEY_1=0xYourPrivateKey

# Wallet 2 (optional)
HL_ADDRESS_2=0xSecondAddress
HL_PRIVATE_KEY_2=0xSecondKey

# Add as many wallets as needed (3, 4, 5...)
```

> ⚠️ **SECURITY**: NEVER share your private key. The `.env` file should never be committed to Git.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a name="config_wallet_xjson-configuration"></a>
### config_wallet_X.json Configuration

#### Step 1: Generate configuration automatically

```bash
python autoconfig.py
```

This command analyzes your wallet and generates a `config_wallet_1.json` file (and `config_wallet_2.json`, etc. if you have multiple wallets).

#### Step 2: Understand the file structure

Here's a complete example configuration file with explanations:

```json
{
  "settings": {
    "order_size_usd": 15,
    "cooldown_minutes": 15,
    "check_interval_seconds": 100,
    "default_fee_pct": 0.07,
    "dry_run": false
  },
  "spot_tokens": {
    "BTC": {
      "enabled": false,
      "hold_usd": 1000,
      "buy_enabled": true,
      "sell_enabled": true,
      "buy_threshold_pct": 16,
      "sell_threshold_pct": 16,
      "fee_pct": 0.07,
      "pair_index": 5,
      "sz_decimals": 8,
      "price_decimals": 6,
      "quote_asset": "USDC"
    }
  },
  "perpetuals": {
    "BTC": {
      "enabled": false,
      "hold_usd": 5000,
      "buy_enabled": true,
      "sell_enabled": true,
      "buy_threshold_pct": 16,
      "sell_threshold_pct": 16,
      "fee_pct": 0.07,
      "sz_decimals": 8,
      "dex": "",
      "quote_asset": "USDC"
    }
  }
}
```

#### Step 3: Understand each parameter

##### `settings` Section - Global Parameters

| Parameter | Description | Recommended Value |
|-----------|-------------|-------------------|
| `order_size_usd` | Size of each rebalancing order in USD | 10-50 USD |
| `cooldown_minutes` | Minimum time between orders on the same asset | 15-30 min |
| `check_interval_seconds` | Interval between each verification cycle | 60-300 sec |
| `default_fee_pct` | Default trading fee (informational) | 0.07 |
| `dry_run` | Simulation mode (no real orders) | false |

##### `spot_tokens` / `perpetuals` Sections - Per-Asset Configuration

| Parameter | Description | Example |
|-----------|-------------|---------|
| `enabled` | **Enables or disables** rebalancing for this asset | `true` / `false` |
| `hold_usd` | **Target value** in USD you want to maintain | `1000` |
| `buy_enabled` | Allows buy orders | `true` |
| `sell_enabled` | Allows sell orders | `true` |
| `buy_threshold_pct` | % below target triggering a buy | `16` |
| `sell_threshold_pct` | % above target triggering a sell | `16` |
| `dex` | DEX for Futures (`""` = main, `"flx"`, `"vntl"`, etc.) | `""` |
| `quote_asset` | Quote currency (auto-detected) | `"USDC"` |

> **Note**: Parameters `pair_index`, `sz_decimals`, `price_decimals`, and `quote_asset` are automatically generated by `autoconfig.py`. Don't modify them manually.

#### Step 4: Configure your targets

**Example: You want to maintain $1000 of BTC Spot with +/- 16% tolerance**

```json
"BTC": {
  "enabled": true,           // Enable rebalancing
  "hold_usd": 1000,          // Target: $1000
  "buy_enabled": true,       // Allow buys
  "sell_enabled": true,      // Allow sells
  "buy_threshold_pct": 16,   // Buy if value < $840 (1000 × 0.84)
  "sell_threshold_pct": 16,  // Sell if value > $1160 (1000 × 1.16)
  ...
}
```

**Threshold visualization:**
```
                    SELL triggered
                         ↓
    |-------|--------[$1160]------->
    |       |         +16%
    |       |
    |  [$1000] ← Target value (hold_usd)
    |       |
    |       |         -16%
    |-------v--------[$840]-------->
                         ↑
                    BUY triggered
```

#### Step 5: Enable desired assets

After adjusting `hold_usd` and thresholds, **set `enabled` to `true`** for each asset you want to rebalance:

```json
"BTC": {
  "enabled": true,    // ← Change from false to true
  "hold_usd": 1000,
  ...
}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a name="usage"></a>
### Usage

1. **Test in simulation mode** (strongly recommended):
   ```bash
   python bot.py --dry-run
   ```
   Check the logs to ensure the bot works as expected.

2. **Start the bot in real mode**:
   ```bash
   python bot.py
   ```

3. **Run for a single wallet**:
   ```bash
   python bot.py --wallet 1
   ```

4. **Regenerate configuration** (if new positions):
   ```bash
   python autoconfig.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a name="strategy-examples"></a>
### Strategy Examples

#### Strategy 1: Balanced Portfolio (Conservative)

```json
{
  "settings": {
    "order_size_usd": 20,
    "cooldown_minutes": 30,
    "check_interval_seconds": 180
  },
  "spot_tokens": {
    "BTC": { "enabled": true, "hold_usd": 2000, "buy_threshold_pct": 20, "sell_threshold_pct": 20 },
    "ETH": { "enabled": true, "hold_usd": 1500, "buy_threshold_pct": 20, "sell_threshold_pct": 20 },
    "HYPE": { "enabled": true, "hold_usd": 500, "buy_threshold_pct": 20, "sell_threshold_pct": 20 }
  }
}
```

#### Strategy 2: Active Trading (Aggressive)

```json
{
  "settings": {
    "order_size_usd": 10,
    "cooldown_minutes": 10,
    "check_interval_seconds": 60
  },
  "perpetuals": {
    "BTC": { "enabled": true, "hold_usd": 5000, "buy_threshold_pct": 10, "sell_threshold_pct": 10 },
    "ETH": { "enabled": true, "hold_usd": 3000, "buy_threshold_pct": 10, "sell_threshold_pct": 10 }
  }
}
```

#### Strategy 3: Accumulation Only (DCA)

```json
{
  "spot_tokens": {
    "BTC": {
      "enabled": true,
      "hold_usd": 10000,
      "buy_enabled": true,
      "sell_enabled": false,    // Disable sells
      "buy_threshold_pct": 5,   // Buy at -5%
      "sell_threshold_pct": 100 // Never sell
    }
  }
}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<a name="avertissement--disclaimer"></a>
## Avertissement / Disclaimer

**FR** : Le trading de cryptomonnaies comporte des risques importants. Utilisez ce bot à vos propres risques. L'auteur n'est pas responsable des pertes financières. Testez toujours en mode `--dry-run` avant d'utiliser en mode réel.

**EN**: Cryptocurrency trading carries significant risks. Use this bot at your own risk. The author is not responsible for any financial losses. Always test with `--dry-run` mode before using in real mode.

<a name="licence"></a>
## Licence

Distribué sous la licence MIT. Voir `LICENSE.txt` pour plus d'informations.

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[license-shield]: https://img.shields.io/github/license/nicos9eth-cmd/Hyperliquid-Weighting-Bot.svg?style=for-the-badge
[license-url]: https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot/blob/master/LICENSE.txt
