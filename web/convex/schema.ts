import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  books: defineTable({
    slug: v.string(),
    order: v.number(),
    title: v.string(),
    subtitle: v.string(),
    author: v.string(),
    language: v.string(),
    domain: v.string(),
    renderingMode: v.union(
      v.literal("editorial-business"),
      v.literal("math-katex"),
      v.literal("vertical-classic"),
    ),
    renderingBadge: v.string(),
    description: v.string(),
    stats: v.object({
      pages: v.number(),
      figures: v.number(),
      tables: v.number(),
      chapters: v.number(),
    }),
    deliverables: v.object({
      pdf: v.string(),
      typst: v.string(),
      latex: v.string(),
      epub: v.string(),
    }),
    editions: v.optional(
      v.array(
        v.object({
          name: v.string(),
          label: v.string(),
          pdf: v.string(),
          typst: v.optional(v.string()),
          latex: v.optional(v.string()),
          epub: v.optional(v.string()),
        }),
      ),
    ),
    legend: v.optional(v.array(v.object({ color: v.string(), label: v.string() }))),
    chapterSummaries: v.array(
      v.object({
        slug: v.string(),
        number: v.string(),
        title: v.string(),
        tag: v.optional(v.string()),
        blockCount: v.number(),
      }),
    ),
  })
    .index("by_slug", ["slug"])
    .index("by_order", ["order"]),

  chapters: defineTable({
    bookSlug: v.string(),
    slug: v.string(),
    order: v.number(),
    number: v.string(),
    title: v.string(),
    tag: v.optional(v.string()),
    blocksJson: v.string(),
  })
    .index("by_book_and_slug", ["bookSlug", "slug"])
    .index("by_book_and_order", ["bookSlug", "order"]),

  annotations: defineTable({
    bookSlug: v.string(),
    chapterSlug: v.string(),
    readerName: v.string(),
    quoteText: v.string(),
    note: v.string(),
    createdAt: v.number(),
  }).index("by_book_and_chapter", ["bookSlug", "chapterSlug"]),
});
