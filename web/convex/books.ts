import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const listBooks = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("books").withIndex("by_order").collect();
  },
});

export const getChapter = query({
  args: {
    bookSlug: v.string(),
    chapterSlug: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("chapters")
      .withIndex("by_book_and_slug", (q) =>
        q.eq("bookSlug", args.bookSlug).eq("slug", args.chapterSlug),
      )
      .unique();
  },
});

export const listAnnotations = query({
  args: {
    bookSlug: v.string(),
    chapterSlug: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("annotations")
      .withIndex("by_book_and_chapter", (q) =>
        q.eq("bookSlug", args.bookSlug).eq("chapterSlug", args.chapterSlug),
      )
      .order("desc")
      .take(50);
  },
});

export const addAnnotation = mutation({
  args: {
    bookSlug: v.string(),
    chapterSlug: v.string(),
    readerName: v.string(),
    quoteText: v.string(),
    note: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("annotations", {
      bookSlug: args.bookSlug,
      chapterSlug: args.chapterSlug,
      readerName: args.readerName.trim() || "Scholar",
      quoteText: args.quoteText.trim(),
      note: args.note.trim(),
      createdAt: Date.now(),
    });
  },
});

export const upsertBookMetadata = mutation({
  args: {
    slug: v.string(),
    order: v.number(),
    title: v.string(),
    subtitle: v.string(),
    author: v.string(),
    language: v.string(),
    domain: v.string(),
    renderingMode: v.union(v.literal("editorial-business"), v.literal("math-katex")),
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
    chapterSummaries: v.array(
      v.object({
        slug: v.string(),
        number: v.string(),
        title: v.string(),
        tag: v.optional(v.string()),
        blockCount: v.number(),
      }),
    ),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("books")
      .withIndex("by_slug", (q) => q.eq("slug", args.slug))
      .unique();
    if (existing) {
      await ctx.db.patch(existing._id, args);
      return existing._id;
    }
    return await ctx.db.insert("books", args);
  },
});

export const upsertChapter = mutation({
  args: {
    bookSlug: v.string(),
    slug: v.string(),
    order: v.number(),
    number: v.string(),
    title: v.string(),
    tag: v.optional(v.string()),
    blocksJson: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("chapters")
      .withIndex("by_book_and_slug", (q) => q.eq("bookSlug", args.bookSlug).eq("slug", args.slug))
      .unique();
    if (existing) {
      await ctx.db.patch(existing._id, args);
      return existing._id;
    }
    return await ctx.db.insert("chapters", args);
  },
});
