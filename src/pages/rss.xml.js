import rss from "@astrojs/rss";
import { getPosts, SITE } from "../lib/site";

export async function GET(context) {
  const posts = await getPosts();
  return rss({
    title: SITE.title,
    description: SITE.description,
    site: context.site,
    customData: "<language>fr-FR</language>",
    items: posts.slice(0, 30).map((p) => ({
      title: p.data.title,
      pubDate: p.data.date,
      description: p.data.accroche ?? p.data.excerpt,
      link: p.data.path,
    })),
  });
}
