import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api";
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

    if (!existingPdf) {
      if (existsSync(localPdfPath)) {
        try {
          const uploadUrl = await client.mutation(api.books.generateUploadUrl);
          const pdfBytes = readFileSync(localPdfPath);
          const res = await fetch(uploadUrl, {
            method: "POST",
            headers: { "Content-Type": "application/pdf" },
            body: pdfBytes,
          });
          const { storageId } = await res.json();
          if (storageId) {
            const liveUrl = await client.mutation(api.books.updateBookDeliverablePdf, {
              slug: book.slug,
              storageId,
            });
            console.log(`Uploaded ${book.slug} PDF to Convex Storage -> ${liveUrl}`);
          }
        } catch (err) {
          console.warn(`Could not upload PDF for ${book.slug}:`, err);
        }
      }
    }
    console.log(
      `Seeded ${book.slug} (${book.chapters.length} chapters) into Convex at ${convexUrl}`,
    );
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

  await client.mutation(api.books.addAnnotation, {
    bookSlug: "ahlfors",
    chapterSlug: "ch-1",
    readerName: "Harvard Mathematics",
    quoteText: "The Algebra of Complex Numbers",
    note: "Classic McGraw-Hill 1979 Crown Octavo edition with modernized KaTeX typography and 50 publication-grade vector figures.",
  });

  await client.mutation(api.books.addAnnotation, {
    bookSlug: "goursat-analyse",
    chapterSlug: "ch-1",
    readerName: "Sorbonne Analysis Group",
    quoteText: "Derivatives and Differentials",
    note: "Complete Dover/Hedrick English translation of Goursat Cours d'analyse with fully restored mathematical formulas and geometric figures.",
  });

  await client.mutation(api.books.addAnnotation, {
    bookSlug: "taocp-vol3",
    chapterSlug: "sec-4",
    readerName: "Stanford CS & TeX Project",
    quoteText: "Chapter Five: Sorting",
    note: "Donald Knuth's masterpiece sorting algorithms with 300-DPI matched graphics and authentic Computer Modern typography.",
  });

  console.log("Convex seeding complete!");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
