<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot">
    <img src="https://i.imgur.com/hE2E2Qc.png" alt="Logo" width="80" height="80">
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
  <summary>Table des matières</summary>
  <ol>
    <li>
      <a href="#-français">Français</a>
      <ul>
        <li><a href="#présentation">Présentation</a></li>
        <li><a href="#fonctionnalités">Fonctionnalités</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#utilisation">Utilisation</a></li>
      </ul>
    </li>
    <li>
      <a href="#-english">English</a>
      <ul>
        <li><a href="#overview">Overview</a></li>
        <li><a href="#features">Features</a></li>
        <li><a href="#installation-en">Installation</a></li>
        <li><a href="#usage-en">Usage</a></li>
      </ul>
    </li>
    <li><a href="#avertissement">Avertissement</a></li>
    <li><a href="#licence">Licence</a></li>
  </ol>
</details>

---

## 🇫🇷 Français

<a name="présentation"></a>
### Présentation

Ce bot est un outil de **rééquilibrage (weighting)** automatique pour [Hyperliquid](https://app.hyperliquid.xyz/join/NICOS9). Il permet de maintenir des positions pondérées sur vos actifs Spot et Perpétuels (Futures) avec un levier de x1.

Le bot détecte automatiquement vos positions ouvertes et génère une configuration adaptée à votre portefeuille. Il supporte les actifs **USDC** et **USDH** comme collatéral/quote asset.

> 🎁 **Bonus de parrainage** : Utilisez mon code de parrainage pour bénéficier de **4% de réduction** sur tous vos frais de trading : [https://app.hyperliquid.xyz/join/NICOS9](https://app.hyperliquid.xyz/join/NICOS9)

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="fonctionnalités"></a>
### Fonctionnalités

- **Auto-détection** : Identifie automatiquement vos positions Spot, Perpétuels et HIP-3.
- **Multi-wallet** : Gérez plusieurs portefeuilles simultanément.
- **Pondération intelligente** : Rééquilibre vos positions selon vos paramètres cibles.
- **Support HIP-3** : Compatible avec les nouveaux actifs et DEXs sur Hyperliquid (flx, hyna, vntl, xyz).

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

3. **Configuration des variables d'environnement** :
   - Renommez le fichier `.env.example` en `.env`.
   - Ajoutez votre adresse et votre clé privée pour chaque wallet.
   ```bash
   cp .env.example .env
   ```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="utilisation"></a>
### Utilisation

1. **Générer la configuration** :
   Lancez le script d'auto-configuration pour détecter vos positions et créer les fichiers `config_wallet_X.json`.
   ```bash
   python autoconfig.py
   ```
   *Note : Éditez les fichiers JSON générés pour ajuster les poids et paramètres de chaque position.*

2. **Lancer le bot** :
   ```bash
   python bot.py
   ```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

---

## 🇺🇸 English

<a name="overview"></a>
### Overview

This bot is an automatic **rebalancing (weighting)** tool for [Hyperliquid](https://app.hyperliquid.xyz/join/NICOS9). It helps maintain weighted positions on your Spot and Perpetual (Futures) assets with 1x leverage.

The bot automatically detects your open positions and generates a configuration tailored to your wallet. It supports **USDC** and **USDH** as collateral/quote assets.

> 🎁 **Referral Bonus**: Use my referral link to get a **4% discount** on all your trading fees: [https://app.hyperliquid.xyz/join/NICOS9](https://app.hyperliquid.xyz/join/NICOS9)

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="features"></a>
### Features

- **Auto-detection**: Automatically identifies Spot, Perpetual, and HIP-3 positions.
- **Multi-wallet**: Manage multiple wallets simultaneously.
- **Smart Weighting**: Rebalances your positions according to your target settings.
- **HIP-3 Support**: Compatible with new assets and DEXs on Hyperliquid (flx, hyna, vntl, xyz).

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="installation-en"></a>
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

3. **Environment Configuration**:
   - Rename `.env.example` to `.env`.
   - Add your address and private key for each wallet.
   ```bash
   cp .env.example .env
   ```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<a name="usage-en"></a>
### Usage

1. **Generate Configuration**:
   Run the auto-configuration script to detect your positions and create `config_wallet_X.json` files.
   ```bash
   python autoconfig.py
   ```
   *Note: Edit the generated JSON files to adjust weights and parameters for each position.*

2. **Start the Bot**:
   ```bash
   python bot.py
   ```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

---

<a name="avertissement"></a>
### Avertissement

*Le trading de cryptomonnaies comporte des risques importants. Utilisez ce bot à vos propres risques. L'auteur n'est pas responsable des pertes financières.*

<a name="licence"></a>
### Licence

Distribué sous la licence MIT. Voir `LICENSE.txt` pour plus d'informations.

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[license-shield]: https://img.shields.io/github/license/nicos9eth-cmd/Hyperliquid-Weighting-Bot.svg?style=for-the-badge
[license-url]: https://github.com/nicos9eth-cmd/Hyperliquid-Weighting-Bot/blob/master/LICENSE.txt
