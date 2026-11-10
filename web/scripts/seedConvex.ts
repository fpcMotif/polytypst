import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api";
import type { Id } from "../convex/_generated/dataModel";
import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { BookData } from "../src/types";

async function main() {
  const envPath = resolve(import.meta.dirname, "../.env.local");
  const envText = readFileSync(envPath, "utf-8");
  const urlMatch = envText.match(/VITE_CONVEX_URL=([^\s\n]+)/);
  const convexUrl =
    process.env.VITE_CONVEX_URL || (urlMatch ? urlMatch[1] : "http://127.0.0.1:3210");

  const client = new ConvexHttpClient(convexUrl);
  const catalogPath = resolve(import.meta.dirname, "../public/data/catalog.json");
  const catalog = JSON.parse(readFileSync(catalogPath, "utf-8")) as { books: BookData[] };
  const remoteBooks = await client.query(api.books.listBooks);
  const remoteBySlug: Record<string, (typeof remoteBooks)[number]> = Object.fromEntries(
    remoteBooks.map((b) => [b.slug, b]),
  );

  async function retryMutation<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        if (attempt === retries - 1) throw err;
        const { promise, resolve: res } = Promise.withResolvers<void>();
        setTimeout(res, 1000 * (attempt + 1));
        await promise;
      }
    }
    throw new Error("Mutation failed after retries");
  }
  for (let bIdx = 0; bIdx < catalog.books.length; bIdx++) {
    const book = catalog.books[bIdx];
    const summaries = book.chapters.map((ch) => ({
      slug: ch.slug,
      number: ch.number,
      title: ch.title,
      tag: ch.tag,
      blockCount: ch.blocks.length,
    }));

    const relPdf = book.deliverables.pdf.replace(/^\//, "");
    const localPdfPath = resolve(import.meta.dirname, "../public", relPdf);
    const remotePdf = remoteBySlug[book.slug]?.deliverables?.pdf;
    let existingPdf: string | undefined;
    if (remotePdf?.startsWith("https://") && existsSync(localPdfPath)) {
      const head = await fetch(remotePdf, { method: "HEAD" });
      if (Number(head.headers.get("content-length")) === statSync(localPdfPath).size) {
        existingPdf = remotePdf;
      }
    }
    const finalDeliverables = {
      ...book.deliverables,
      pdf: existingPdf ?? book.deliverables.pdf,
    };

    await retryMutation(() =>
      client.mutation(api.books.upsertBookMetadata, {
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
        deliverables: finalDeliverables,
        editions: book.editions,
        legend: book.legend,
        chapterSummaries: summaries,
      }),
    );

    for (let cIdx = 0; cIdx < book.chapters.length; cIdx++) {
      const ch = book.chapters[cIdx];
      await retryMutation(() =>
        client.mutation(api.books.upsertChapter, {
          bookSlug: book.slug,
          slug: ch.slug,
          order: cIdx + 1,
          number: ch.number,
          title: ch.title,
          tag: ch.tag,
          blocksJson: JSON.stringify(ch.blocks),
        }),
      );
    }

    if (!existingPdf && existsSync(localPdfPath)) {
      const uploadUrl = await client.mutation(api.books.generateUploadUrl);
      const res = await fetch(uploadUrl, {
        method: "POST",
        headers: { "Content-Type": "application/pdf" },
        body: readFileSync(localPdfPath),
      });
      if (!res.ok) {
        throw new Error(`PDF upload for ${book.slug} failed: ${res.status} ${await res.text()}`);
      }
      const { storageId } = (await res.json()) as { storageId: Id<"_storage"> };
      const liveUrl = await client.mutation(api.books.updateBookDeliverablePdf, {
        slug: book.slug,
        storageId,
      });
      console.log(`Uploaded ${book.slug} PDF to Convex Storage -> ${liveUrl}`);
    }
    console.log(
      `Seeded ${book.slug} (${book.chapters.length} chapters) into Convex at ${convexUrl}`,
    );
  }

  const editorialNotes = [
    {
      bookSlug: "modern-firm",
      chapterSlug: "ch-2",
      quoteText: "图 5 · X 点、Y 点与 Z 点",
      note: "网页版把局部最佳点 X、Y 与不匹配点 Z 标为页内锚点，并链接到图 5 的矢量图。",
    },
    {
      bookSlug: "serre-arithmetique",
      chapterSlug: "serre-ch-1",
      quoteText: "Loi de réciprocité quadratique & corps p-adiques",
      note: "KaTeX rend les formules. Les figures du domaine fondamental de SL₂(ℤ) sont vectorielles.",
    },
    {
      bookSlug: "kerodon-ch1",
      chapterSlug: "sec-1-1",
      quoteText: "Tag 000R · The Boundary of Δⁿ",
      note: "Each of the 237 environments links to its Kerodon tag. The 60 commutative diagrams are 300-DPI images.",
    },
    {
      bookSlug: "ahlfors",
      chapterSlug: "ch-1",
      quoteText: "The Algebra of Complex Numbers",
      note: "Rebuilt from the 1979 McGraw-Hill edition. KaTeX sets the formulas, and the 50 figures are vector drawings.",
    },
    {
      bookSlug: "goursat-analyse",
      chapterSlug: "ch-1",
      quoteText: "Derivatives and Differentials",
      note: "Rebuilt from the Dover printing of E. R. Hedrick's English translation, with its formulas and geometric figures.",
    },
    {
      bookSlug: "taocp-vol3",
      chapterSlug: "sec-4",
      quoteText: "Chapter Five: Sorting",
      note: "Set in Computer Modern. The diagrams are 300-DPI images matched to the printed pages.",
    },
  ];
  const readerName = "Polytypst Editorial";
  for (const { bookSlug, chapterSlug, quoteText, note } of editorialNotes) {
    const existing = await client.query(api.books.listAnnotations, { bookSlug, chapterSlug });
    if (existing.some((a) => a.readerName === readerName && a.quoteText === quoteText)) continue;
    await client.mutation(api.books.addAnnotation, {
      bookSlug,
      chapterSlug,
      readerName,
      quoteText,
      note,
    });
  }

  console.log("Convex seeding complete!");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
