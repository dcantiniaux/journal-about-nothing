import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const comment = z.object({
  id: z.string(),
  parent: z.string().default("0"),
  author: z.string(),
  date: z.string(),
  text: z.string(),
});

const posts = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/posts" }),
  schema: z.object({
    title: z.string(),
    path: z.string(),
    date: z.coerce.date(),
    updated: z.coerce.date().optional(),
    categories: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    image: z.string().optional(),
    excerpt: z.string().default(""),
    accroche: z.string().optional(),
    readingTime: z.number().default(1),
    comments: z.array(comment).default([]),
    draft: z.boolean().default(false),
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/pages" }),
  schema: z.object({ title: z.string(), path: z.string() }),
});

export const collections = { posts, pages };
