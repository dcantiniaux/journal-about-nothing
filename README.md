# Journal About Nothing

Le blog d’Ethan Mills, reconstruit en site statique avec [Astro](https://astro.build) à partir de l’export WordPress.com du 20 octobre 2026.

## Ce qui a été repris

- 144 articles publics et 2 pages (Biographie, Contact), en Markdown dans `src/content/`.
- Les adresses d’origine : `/2024/07/27/conseils-pour-un-enterrement-2/`, `/category/non-classe/psychologie-philosophie-analyse/`, `/page/2/`, `/tag/…/`. Les liens déjà partagés continuent de fonctionner.
- 99 commentaires approuvés, affichés en archives (sans e-mail ni adresse IP). Les commentaires sont fermés.
- Masterclasse et Podcast philo pour enfants : listes des textes de la rubrique.

## Ce qui n’a pas été repris

- Les 7 articles protégés par mot de passe : un site statique ne sait pas protéger un texte, il serait lisible par tous dans le code. Ils restent dans l’export WordPress.
- Les 35 brouillons.
- Les sondages Crowdsignal et le formulaire d’abonnement Jetpack.
- Les vidéos VideoPress (18) restent hébergées chez WordPress.com : elles disparaîtront si le compte WordPress.com est supprimé.

## Commandes

| Commande | Effet |
| --- | --- |
| `npm install` | Installe Astro (une seule fois) |
| `zsh tools/download-media.sh` | Télécharge les images dans `public/wp-content/uploads` |
| `npm run dev` | Site local sur http://localhost:4321 |
| `npm run build` | Génère le site dans `dist/` |

## Écrire un nouveau texte

Créer un fichier dans `src/content/posts/`, par exemple `2026-11-02-mon-texte.md` :

```markdown
---
title: "Mon texte"
path: "/2026/11/02/mon-texte/"
date: "2026-11-02T09:00:00"
categories: ["psychologie-philosophie-analyse"]
tags: []
image: "/images/mon-texte.jpg"
accroche: "La phrase qui donne envie de lire."
readingTime: 5
---

Le texte, en Markdown.
```

L’image va dans `public/images/`. Un `git push` publie le site.

## Reconvertir l’export

`python3 tools/convert_wp.py chemin/vers/export.xml` (nécessite `pip install beautifulsoup4 markdownify`). Attention : la commande remplace tous les fichiers de `src/content/`.
