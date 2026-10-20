import categories from "../data/categories.json";
import tags from "../data/tags.json";
import { getCollection, type CollectionEntry } from "astro:content";

export type Post = CollectionEntry<"posts">;
type Cat = { slug: string; name: string; parent: string | null };
export const CATS = categories as Record<string, Cat>;
export const TAGS = tags as Record<string, string>;

export const SITE = {
  title: "Journal About Nothing",
  author: "Ethan Mills",
  description: "Carnet d’Ethan Mills : psychologie, philosophie, lettres d’insultes, journaux intimes et podcasts philo pour enfants.",
  epigraph: "Nous ignorions où nous allions, ni même comment nous y allions, mais nous étions sûrs d’une chose : quand nous serions là-bas, nous y serions.",
  epigraphAuthor: "S. J. Perelman",
  email: "saul.stanson@gmx.fr",
  perPage: 20,
};

export const NAV = [
  { href: "/", label: "Accueil" },
  { href: "/masterclasse/", label: "Masterclasse" },
  { href: "/podcast-philo-pour-enfants/", label: "Podcast philo pour enfants" },
  { href: "/a-propos/", label: "Biographie" },
  { href: "/contact/", label: "Contact" },
];

export async function getPosts(): Promise<Post[]> {
  const all = await getCollection("posts", ({ data }) => !data.draft);
  return all.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export function catUrl(slug: string) {
  const c = CATS[slug];
  if (!c) return "/";
  return c.parent ? `/category/${c.parent}/${slug}/` : `/category/${slug}/`;
}

/** Parent « visible » : les sous-rubriques de « Non classé » sont traitées comme des rubriques principales. */
export function shownParent(slug: string) {
  const p = CATS[slug]?.parent;
  return p && p !== "non-classe" ? p : null;
}

export function catName(slug: string) {
  return CATS[slug]?.name ?? slug;
}

/** Rubrique la plus précise d'un article (on évite « Non classé »). */
export function mainCat(post: Post) {
  const cs = post.data.categories.filter((c) => c !== "non-classe");
  const child = cs.find((c) => shownParent(c));
  const top = cs.find((c) => CATS[c] && !CATS[c].parent);
  return child ?? cs.find((c) => CATS[c]?.parent) ?? top ?? cs[0] ?? post.data.categories[0];
}

/** Rubriques couvertes par une rubrique : elle-même et ses enfants. */
export function catFamily(slug: string) {
  return [slug, ...Object.values(CATS).filter((c) => c.parent === slug).map((c) => c.slug)];
}

export function postsInCat(posts: Post[], slug: string) {
  const fam = catFamily(slug);
  return posts.filter((p) => p.data.categories.some((c) => fam.includes(c)));
}

const fmtLong = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const fmtShort = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
export const dateLong = (d: Date) => fmtLong.format(d);
export const dateShort = (d: Date) => fmtShort.format(d);
export const iso = (d: Date) => d.toISOString().slice(0, 10);

export function readLabel(post: Post) {
  return `${post.data.readingTime} min de lecture`;
}

export function chunk<T>(arr: T[], n: number) {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n));
  return out.length ? out : [[]];
}
