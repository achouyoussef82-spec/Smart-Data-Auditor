# 🛡️ Smart Data Auditor

Application web qui **audite, nettoie et analyse** un fichier CSV en quelques clics, et permet de **poser des questions sur ses données en langage naturel** grâce à l'IA (Claude, d'Anthropic).

> Projet réalisé par Youssef Achou, [Synerbyte Technologies](https://synerbyte-technologies.fr) : Data, IA & Automatisation.

## ✨ Fonctionnalités

| Onglet | Ce qu'il fait |
|---|---|
| 📋 **Audit** | Nombre de lignes et de colonnes, doublons, valeurs manquantes, qualité colonne par colonne |
| 🧹 **Nettoyage** | Suppression des doublons et des lignes vides, normalisation des noms de colonnes, suppression des espaces en trop. Export du fichier propre |
| 📈 **Visualisation** | Graphiques automatiques : somme, moyenne ou nombre, regroupés par catégorie |
| 🤖 **Questions à l'IA** | « Quel produit rapporte le plus ? », « Quelle ville a le plus de commandes ? » : l'IA écrit et exécute elle-même les requêtes SQL sur vos données, puis répond en français |

## 🧠 Comment fonctionne l'IA

L'IA n'invente pas les chiffres. Elle dispose d'un outil `run_sql` qui exécute des requêtes SQL **en lecture seule** sur le fichier (via Polars SQL). Elle calcule les réponses sur les vraies données, puis les explique.

- **Modèle :** Claude Opus 5.5 (Anthropic), utilisé avec le *tool runner* du SDK Python
- **Sécurité :** les requêtes s'exécutent sur une copie en mémoire : le fichier n'est jamais modifié par l'IA

## 🛠️ Stack

Python · Streamlit · Polars · Polars SQL · Anthropic SDK (Claude)

## 🚀 Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Pour activer l'IA, créez une clé API sur [console.anthropic.com](https://console.anthropic.com), puis :
- soit collez-la dans l'onglet « Questions à l'IA » (elle n'est pas enregistrée) ;
- soit copiez `.streamlit/secrets.toml.example` en `.streamlit/secrets.toml` et mettez-y votre clé.

Un fichier d'exemple est fourni : `sample_data/ventes_exemple.csv` (500 commandes fictives, avec des doublons, des valeurs manquantes et des espaces en trop à nettoyer).

## 📫 Contact

[LinkedIn](https://www.linkedin.com/in/youssef-youssef-5218a83b9) · Disponible pour des missions data et IA en France et en Europe.
