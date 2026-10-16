import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { BookData } from "../src/types";

async function main() {
  const envPath = resolve(import.meta.dirname, "../.env.local");
  const envText = readFileSync(envPath, "utf-8");
  const urlMatch = envText.match(/VITE_CONVEX_URL=([^\s\n]+)/);
  const convexUrl = process.env.VITE_CONVEX_URL || (urlMatch ? urlMatch[1] : "http://127.0.0.1:3210");

  const client = new ConvexHttpClient(convexUrl);
  const catalogPath = resolve(import.meta.dirname, "../public/data/catalog.json");
  const catalog = JSON.parse(readFileSync(catalogPath, "utf-8")) as { books: BookData[] };

  for (let bIdx = 0; bIdx < catalog.books.length; bIdx++) {
    const book = catalog.books[bIdx];
    const summaries = book.chapters.map((ch) => ({
      slug: ch.slug,
      number: ch.number,
      title: ch.title,
      tag: ch.tag,
      blockCount: ch.blocks.length,
    }));

    await client.mutation(api.books.upsertBookMetadata, {
      slug: book.slug,
      order: bIdx + 1,
      title: book.title,
      subtitle: book.subtitle,
      author: book.author,
      language: book.language,
      domain: book.domain,
      renderingMode: book.renderingMode,
      renderingBadge: book.renderingBadge,
      description: book.description,
      stats: book.stats,
      deliverables: book.deliverables,
      chapterSummaries: summaries,
    });

    for (let cIdx = 0; cIdx < book.chapters.length; cIdx++) {
      const ch = book.chapters[cIdx];
      await client.mutation(api.books.upsertChapter, {
        bookSlug: book.slug,
        slug: ch.slug,
        order: cIdx + 1,
        number: ch.number,
        title: ch.title,
        tag: ch.tag,
        blocksJson: JSON.stringify(ch.blocks),
      });
    }
    console.log(`Seeded ${book.slug} (${book.chapters.length} chapters) into Convex at ${convexUrl}`);
  }

  await client.mutation(api.books.addAnnotation, {
    bookSlug: "modern-firm",
    chapterSlug: "ch-2",
    readerName: "Polytypst Editorial",
    quoteText: "图 5 · X 点、Y 点与 Z 点",
    note: "网页端采用纯正商业社论排版，将局部最佳点 X、Y 与不匹配点 Z 呈现为高对比语义标签，并与图 5 矢量图联动。",
  });

  await client.mutation(api.books.addAnnotation, {
    bookSlug: "serre-arithmetique",
    chapterSlug: "serre-ch-1",
    readerName: "Bourbaki Seminar",
    quoteText: "Loi de réciprocité quadratique & corps p-adiques",
    note: "Édition web mathématique propulsée par KaTeX avec théorèmes structurés et figures vectorielles SL₂(ℤ).",
  });

  await client.mutation(api.books.addAnnotation, {
    bookSlug: "kerodon-ch1",
    chapterSlug: "sec-1-1",
    readerName: "Homotopy Reader",
    quoteText: "Tag 000R · The Boundary of Δⁿ",
    note: "All 237 environments and 60 300-DPI commutative diagrams linked to official Kerodon tags.",
  });

  console.log("Convex seeding complete!");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
