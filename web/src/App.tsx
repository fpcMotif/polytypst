import React, { useMemo, useState } from "react";
import { useMutation, useQuery } from "convex/react";
import { api } from "../convex/_generated/api";
import { ChapterData, ContentBlock } from "./types";
import { renderMathProseToHtml } from "./mathRenderer";
import {
  BookOpen,
  FileText,
  Download,
  Columns,
  Sparkles,
  Search,
  ExternalLink,
  MessageSquarePlus,
  Layers,
  CheckCircle2,
  Database,
} from "lucide-react";

type ViewSurface = "reader" | "split-pdfcn" | "deliverables";

function getCalloutTheme(kind: string = "") {
  const k = kind.toLowerCase();
  if (k.includes("thm") || k.includes("théorème") || k.includes("theorem")) {
    return {
      border: "border-l-4 border-amber-600 border-amber-200",
      bg: "bg-amber-50/70",
      badge: "bg-amber-100 text-amber-900 border-amber-300",
    };
  }
  if (k.includes("prop") || k.includes("lemme") || k.includes("lemma") || k.includes("cor")) {
    return {
      border: "border-l-4 border-indigo-600 border-indigo-200",
      bg: "bg-indigo-50/60",
      badge: "bg-indigo-100 text-indigo-900 border-indigo-300",
    };
  }
  if (k.includes("def") || k.includes("définition") || k.includes("notation")) {
    return {
      border: "border-l-4 border-blue-600 border-blue-200",
      bg: "bg-blue-50/60",
      badge: "bg-blue-100 text-blue-900 border-blue-300",
    };
  }
  if (k.includes("warn")) {
    return {
      border: "border-l-4 border-red-600 border-red-200",
      bg: "bg-red-50/60",
      badge: "bg-red-100 text-red-900 border-red-300",
    };
  }
  return {
    border: "border-l-4 border-stone-500 border-stone-200",
    bg: "bg-stone-50/80",
    badge: "bg-stone-200/80 text-stone-800 border-stone-300",
  };
}

export function App() {
  const [selectedBookSlug, setSelectedBookSlug] = useState<string>("modern-firm");
  const [selectedChapterSlug, setSelectedChapterSlug] = useState<string>("");
  const [surface, setSurface] = useState<ViewSurface>("reader");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [readerName, setReaderName] = useState<string>("Editorial Reviewer");
  const [quoteText, setQuoteText] = useState<string>("");
  const [noteText, setNoteText] = useState<string>("");
  const [sourcePreview, setSourcePreview] = useState<{ format: string; content: string } | null>(
    null,
  );

  const convexBooks = useQuery(api.books.listBooks);
  const activeBook = useMemo(() => {
    if (!convexBooks || convexBooks.length === 0) return null;
    return convexBooks.find((b) => b.slug === selectedBookSlug) ?? convexBooks[0] ?? null;
  }, [convexBooks, selectedBookSlug]);

  const effectiveChapterSlug = useMemo(() => {
    if (!activeBook) return "";
    const found = activeBook.chapterSummaries.find((c) => c.slug === selectedChapterSlug);
    return found ? found.slug : (activeBook.chapterSummaries[0]?.slug ?? "");
  }, [activeBook, selectedChapterSlug]);

  const convexChapter = useQuery(
    api.books.getChapter,
    activeBook && effectiveChapterSlug
      ? { bookSlug: activeBook.slug, chapterSlug: effectiveChapterSlug }
      : "skip",
  );

  const convexAnnotations = useQuery(
    api.books.listAnnotations,
    activeBook && effectiveChapterSlug
      ? { bookSlug: activeBook.slug, chapterSlug: effectiveChapterSlug }
      : "skip",
  );

  const addAnnotationMutation = useMutation(api.books.addAnnotation);

  const activeChapter: ChapterData | null = useMemo(() => {
    if (!convexChapter || !convexChapter.blocksJson) return null;
    try {
      const parsedBlocks = JSON.parse(convexChapter.blocksJson) as ContentBlock[];
      return {
        slug: convexChapter.slug,
        number: convexChapter.number,
        title: convexChapter.title,
        tag: convexChapter.tag,
        blocks: parsedBlocks,
      };
    } catch {
      return null;
    }
  }, [convexChapter]);

  const filteredBlocks = useMemo(() => {
    if (!activeChapter) return [];
    const q = searchQuery.trim().toLowerCase();
    if (!q) return activeChapter.blocks;
    return activeChapter.blocks.filter((blk) => {
      const hay = [blk.text, blk.content, blk.html, blk.caption, blk.title, blk.tag, blk.number]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [activeChapter, searchQuery]);

  async function handleInspectSource(format: "typst" | "latex") {
    if (!activeBook) return;
    const url = activeBook.deliverables[format];
    const resp = await fetch(url);
    const text = await resp.text();
    setSourcePreview({
      format: format === "typst" ? "Typst Master (.typ)" : "XeLaTeX Master (.tex)",
      content: text.slice(0, 18000),
    });
    setSurface("deliverables");
  }

  async function handleAddAnnotation(e: React.FormEvent) {
    e.preventDefault();
    if (!activeBook || !activeChapter || !noteText.trim()) return;
    await addAnnotationMutation({
      bookSlug: activeBook.slug,
      chapterSlug: activeChapter.slug,
      readerName,
      quoteText: quoteText || activeChapter.title,
      note: noteText,
    });
    setQuoteText("");
    setNoteText("");
  }

  if (!activeBook || !convexBooks) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#faf8f5] text-stone-700">
        <div className="flex items-center gap-3 text-sm font-medium">
          <Sparkles className="w-5 h-5 text-amber-600 animate-spin" />
          <span>Connecting to Convex Cloud Publication Database...</span>
        </div>
      </div>
    );
  }

  const isBusinessMode = activeBook.renderingMode === "editorial-business";

  return (
    <div className="min-h-screen flex flex-col bg-[#faf8f5] text-stone-900">
      <header className="sticky top-0 z-30 border-b border-stone-200/90 bg-[#faf8f5]/95 backdrop-blur">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-stone-900 text-amber-300 flex items-center justify-center font-serif font-bold text-lg shadow-sm">
              P
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-serif font-bold text-base sm:text-lg tracking-tight text-stone-900">
                  Polytypst Digital &amp; Print Press
                </h1>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                  <Database className="w-3 h-3" />
                  {`Convex Cloud (${convexBooks.length} Books Synced)`}
                </span>
              </div>
              <p className="text-xs text-stone-500">
                Domain-Specific Web Publishing · Editorial HTML for Business &amp; KaTeX for
                Mathematics · Integrated pdfcn Viewer
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {convexBooks.map((book) => {
              const selected = book.slug === activeBook.slug;
              return (
                <button
                  key={book.slug}
                  onClick={() => {
                    setSelectedBookSlug(book.slug);
                    setSelectedChapterSlug(book.chapterSummaries[0]?.slug ?? "");
                    setSourcePreview(null);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                    selected
                      ? "bg-stone-900 text-white border-stone-900 shadow-sm"
                      : "bg-white text-stone-700 border-stone-200 hover:border-stone-400"
                  }`}
                >
                  <span className="font-semibold">{book.title.split("：")[0].split("—")[0]}</span>
                  <span
                    className={`ml-1.5 px-1.5 py-0.5 rounded text-[10px] ${
                      selected
                        ? "bg-amber-400/20 text-amber-200"
                        : book.renderingMode === "editorial-business"
                          ? "bg-amber-50 text-amber-800"
                          : "bg-blue-50 text-blue-800"
                    }`}
                  >
                    {book.renderingMode === "editorial-business" ? "Editorial Web" : "KaTeX Math"}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-1.5 bg-stone-200/70 p-1 rounded-lg">
            <button
              onClick={() => setSurface("reader")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition ${
                surface === "reader"
                  ? "bg-white text-stone-900 shadow-xs"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              Web Reader
            </button>
            <button
              onClick={() => setSurface("split-pdfcn")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition ${
                surface === "split-pdfcn"
                  ? "bg-white text-stone-900 shadow-xs"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              pdfcn Split View
            </button>
            <button
              onClick={() => setSurface("deliverables")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition ${
                surface === "deliverables"
                  ? "bg-white text-stone-900 shadow-xs"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Deliverables (.pdf / .typ / .tex / .epub)
            </button>
          </div>
        </div>
      </header>

      <div className="bg-white border-b border-stone-200/80">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                {activeBook.domain}
              </span>
              <span
                className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                  isBusinessMode
                    ? "bg-amber-50 text-amber-900 border-amber-300"
                    : "bg-blue-50 text-blue-900 border-blue-300"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                {activeBook.renderingBadge}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-serif font-bold text-stone-900">
              {activeBook.title}
            </h2>
            <p className="text-xs sm:text-sm text-stone-600">
              <span className="font-semibold text-stone-800">{activeBook.author}</span> ·{" "}
              {activeBook.subtitle}
            </p>
            <p className="text-xs text-stone-600 leading-relaxed pt-0.5">
              {activeBook.description}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="grid grid-cols-3 gap-2 text-center bg-stone-50 border border-stone-200 rounded-lg px-3 py-2">
              <div>
                <div className="text-sm font-bold text-stone-900">{activeBook.stats.pages}</div>
                <div className="text-[10px] uppercase text-stone-500">Print Pages</div>
              </div>
              <div>
                <div className="text-sm font-bold text-stone-900">{activeBook.stats.figures}</div>
                <div className="text-[10px] uppercase text-stone-500">Vector/HD Figs</div>
              </div>
              <div>
                <div className="text-sm font-bold text-stone-900">
                  {activeBook.chapterSummaries.length}
                </div>
                <div className="text-[10px] uppercase text-stone-500">Sections</div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
              <a
                href={activeBook.deliverables.pdf}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-stone-900 text-white hover:bg-stone-800 transition"
              >
                <Download className="w-3.5 h-3.5" />
                PDF
              </a>
              <a
                href={activeBook.deliverables.epub}
                download
                className="inline-flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-xs font-medium bg-white border border-stone-300 text-stone-700 hover:bg-stone-50 transition"
              >
                <Download className="w-3.5 h-3.5" />
                EPUB
              </a>
              <button
                onClick={() => handleInspectSource("typst")}
                className="inline-flex items-center gap-1 px-2.5 py-2 rounded-lg text-xs font-medium bg-white border border-stone-300 text-stone-700 hover:bg-stone-50 transition"
              >
                <FileText className="w-3.5 h-3.5" />
                .typ
              </button>
              <button
                onClick={() => handleInspectSource("latex")}
                className="inline-flex items-center gap-1 px-2.5 py-2 rounded-lg text-xs font-medium bg-white border border-stone-300 text-stone-700 hover:bg-stone-50 transition"
              >
                <FileText className="w-3.5 h-3.5" />
                .tex
              </button>
            </div>
          </div>
        </div>
      </div>

      <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-3 space-y-4">
          <div className="bg-white rounded-xl border border-stone-200/90 p-3.5 shadow-2xs">
            <div className="relative mb-3">
              <Search className="w-4 h-4 text-stone-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter blocks, tags, figures..."
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-stone-200 focus:outline-none focus:border-stone-500"
              />
            </div>

            <div className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 px-2 mb-2">
              Table of Contents ({activeBook.chapterSummaries.length})
            </div>
            <nav className="space-y-1 max-h-[55vh] overflow-y-auto pr-1">
              {activeBook.chapterSummaries.map((ch) => {
                const active = ch.slug === effectiveChapterSlug;
                return (
                  <button
                    key={ch.slug}
                    onClick={() => setSelectedChapterSlug(ch.slug)}
                    className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition flex items-start justify-between gap-2 ${
                      active
                        ? "bg-stone-900 text-white font-semibold"
                        : "text-stone-700 hover:bg-stone-100"
                    }`}
                  >
                    <div className="truncate">
                      <span className={active ? "text-amber-300 mr-1.5" : "text-stone-400 mr-1.5"}>
                        {ch.number}
                      </span>
                      <span>{ch.title}</span>
                    </div>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded shrink-0 ${
                        active ? "bg-stone-700 text-stone-200" : "bg-stone-100 text-stone-500"
                      }`}
                    >
                      {ch.blockCount}
                    </span>
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="bg-white rounded-xl border border-stone-200/90 p-3.5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-stone-800 flex items-center gap-1.5">
                <MessageSquarePlus className="w-4 h-4 text-amber-600" />
                Convex Live Marginalia
              </span>
              <span className="text-[10px] text-stone-400">
                {convexAnnotations ? `${convexAnnotations.length} notes` : "Realtime"}
              </span>
            </div>

            <form onSubmit={handleAddAnnotation} className="space-y-2">
              <input
                type="text"
                value={readerName}
                onChange={(e) => setReaderName(e.target.value)}
                placeholder="Your name"
                className="w-full px-2.5 py-1.5 text-xs rounded border border-stone-200"
              />
              <input
                type="text"
                value={quoteText}
                onChange={(e) => setQuoteText(e.target.value)}
                placeholder="Section / Figure / Tag reference (e.g. 图 5 or Tag 000R)"
                className="w-full px-2.5 py-1.5 text-xs rounded border border-stone-200"
              />
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Add a marginal note persisted to Convex..."
                rows={2}
                className="w-full px-2.5 py-1.5 text-xs rounded border border-stone-200"
              />
              <button
                type="submit"
                className="w-full py-1.5 rounded-lg text-xs font-semibold bg-amber-600 text-white hover:bg-amber-700 transition"
              >
                Save Note to Convex
              </button>
            </form>

            {convexAnnotations && convexAnnotations.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-stone-100 max-h-48 overflow-y-auto">
                {convexAnnotations.map((ann) => (
                  <div
                    key={ann._id}
                    className="p-2 rounded-lg bg-stone-50 border border-stone-200/70 text-xs"
                  >
                    <div className="flex items-center justify-between text-[10px] text-stone-500 mb-0.5">
                      <span className="font-semibold text-stone-700">{ann.readerName}</span>
                      <span className="font-mono text-amber-800">{ann.quoteText}</span>
                    </div>
                    <p className="text-stone-700">{ann.note}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {surface === "deliverables" ? (
          <section className="lg:col-span-9 space-y-6">
            <div className="bg-white rounded-2xl border border-stone-200 p-6 shadow-2xs space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-stone-200 pb-4">
                <div>
                  <h3 className="text-lg font-serif font-bold text-stone-900">
                    Publication Deliverables &amp; Master Source Inspector
                  </h3>
                  <p className="text-xs text-stone-500">
                    Local print deliverables use Typst and XeLaTeX with full mathematical
                    typesetting, while the web edition adapts to each book&apos;s domain.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleInspectSource("typst")}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-stone-900 text-white"
                  >
                    Inspect Typst (.typ)
                  </button>
                  <button
                    onClick={() => handleInspectSource("latex")}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-stone-100 text-stone-800 border border-stone-300"
                  >
                    Inspect XeLaTeX (.tex)
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {[
                  { label: "Typst Print PDF", ext: "PDF", href: activeBook.deliverables.pdf },
                  { label: "Typst Master Source", ext: "TYP", href: activeBook.deliverables.typst },
                  {
                    label: "XeLaTeX Master Source",
                    ext: "TEX",
                    href: activeBook.deliverables.latex,
                  },
                  { label: "Reflowable EPUB 3", ext: "EPUB", href: activeBook.deliverables.epub },
                ].map((item) => (
                  <a
                    key={item.ext}
                    href={item.href}
                    target="_blank"
                    rel="noreferrer"
                    className="p-3.5 rounded-xl border border-stone-200 hover:border-stone-400 bg-stone-50/60 flex items-center justify-between transition"
                  >
                    <div>
                      <div className="text-xs font-bold text-stone-900">{item.label}</div>
                      <div className="text-[11px] text-stone-500 font-mono">{item.href}</div>
                    </div>
                    <span className="px-2 py-1 rounded text-[10px] font-bold bg-stone-900 text-amber-300">
                      {item.ext}
                    </span>
                  </a>
                ))}
              </div>

              {sourcePreview && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-stone-700">
                    Previewing {sourcePreview.format} (first 18 KB):
                  </div>
                  <pre className="p-4 rounded-xl bg-stone-950 text-stone-100 text-xs font-mono overflow-x-auto max-h-[420px] leading-relaxed">
                    {sourcePreview.content}
                  </pre>
                </div>
              )}

              <div className="space-y-2">
                <div className="text-xs font-semibold text-stone-700">
                  Embedded pdfcn Print Deliverable Viewer ({activeBook.deliverables.pdf}):
                </div>
                <iframe
                  src={activeBook.deliverables.pdf}
                  title="PDF Deliverable Preview"
                  className="w-full h-[680px] rounded-xl border border-stone-300 bg-stone-100"
                />
              </div>
            </div>
          </section>
        ) : (
          <section
            className={`lg:col-span-9 grid gap-6 ${
              surface === "split-pdfcn" ? "grid-cols-1 xl:grid-cols-2" : "grid-cols-1"
            }`}
          >
            <article className="bg-white rounded-2xl border border-stone-200/90 p-6 sm:p-10 shadow-2xs">
              {!activeChapter ? (
                <div className="py-12 flex items-center justify-center gap-2 text-xs text-stone-500">
                  <Sparkles className="w-4 h-4 text-amber-600 animate-spin" />
                  <span>Loading chapter from Convex Cloud...</span>
                </div>
              ) : (
                <>
                  <div className="border-b border-stone-200 pb-5 mb-8">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <span className="text-xs font-bold uppercase tracking-widest text-amber-700">
                        {activeChapter.number}
                      </span>
                      {activeChapter.tag && (
                        <a
                          href={`https://kerodon.net/tag/${activeChapter.tag}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200"
                        >
                          Kerodon Tag {activeChapter.tag}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-serif font-bold text-stone-900">
                      {activeChapter.title}
                    </h3>
                  </div>

                  <div
                    className={
                      isBusinessMode ? "editorial-prose space-y-5" : "math-prose space-y-5"
                    }
                  >
                    {filteredBlocks.map((blk, idx) => {
                      if (blk.type === "heading") {
                        const Tag = blk.level === 2 ? "h4" : "h5";
                        return (
                          <Tag
                            key={idx}
                            className={`font-serif font-bold text-stone-900 pt-4 ${
                              blk.level === 2 ? "text-xl border-b border-stone-100 pb-2" : "text-lg"
                            }`}
                          >
                            {isBusinessMode ? (
                              blk.text
                            ) : (
                              <span
                                dangerouslySetInnerHTML={{
                                  __html: renderMathProseToHtml(blk.text ?? ""),
                                }}
                              />
                            )}
                          </Tag>
                        );
                      }

                      if (blk.type === "figure") {
                        return (
                          <figure
                            key={idx}
                            id={blk.id}
                            className="my-8 p-5 rounded-xl bg-[#fcfbf9] border border-stone-200/90 shadow-2xs scroll-mt-24"
                          >
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300">
                                {blk.label}
                              </span>
                              <span className="text-[11px] font-mono text-stone-400">
                                #{blk.id}
                              </span>
                            </div>
                            <div className="flex justify-center bg-white p-4 rounded-lg border border-stone-100">
                              <img
                                src={blk.src}
                                alt={blk.caption ?? blk.label}
                                className="max-h-[420px] w-auto object-contain"
                              />
                            </div>
                            {blk.caption && (
                              <figcaption className="mt-3 text-center text-xs sm:text-sm font-medium text-stone-700">
                                {isBusinessMode ? (
                                  <span>
                                    <strong>{blk.label}</strong> {blk.caption}
                                  </span>
                                ) : (
                                  <span
                                    dangerouslySetInnerHTML={{
                                      __html: renderMathProseToHtml(blk.caption),
                                    }}
                                  />
                                )}
                              </figcaption>
                            )}
                          </figure>
                        );
                      }

                      if (blk.type === "table" && blk.headers && blk.rows) {
                        return (
                          <figure
                            key={idx}
                            id={blk.id}
                            className="my-8 p-5 rounded-xl bg-stone-50/70 border border-stone-200 scroll-mt-24"
                          >
                            <div className="flex items-center justify-between mb-3">
                              <div className="text-sm font-bold text-stone-900">
                                <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 mr-2 text-xs">
                                  {blk.label}
                                </span>
                                {blk.caption}
                              </div>
                              <span className="text-[11px] font-mono text-stone-400">
                                #{blk.id}
                              </span>
                            </div>
                            <div className="overflow-x-auto bg-white rounded-lg border border-stone-200">
                              <table className="w-full text-left border-collapse text-xs sm:text-sm">
                                <thead>
                                  <tr className="border-b-2 border-stone-800 bg-stone-100/80">
                                    {blk.headers.map((h, hIdx) => (
                                      <th
                                        key={hIdx}
                                        className={`py-2.5 px-3 font-bold text-stone-900 ${
                                          hIdx > 0 ? "text-right" : "text-left"
                                        }`}
                                      >
                                        {h}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-stone-200">
                                  {blk.rows.map((row, rIdx) => (
                                    <tr key={rIdx} className="hover:bg-amber-50/30">
                                      {row.map((cell, cIdx) => (
                                        <td
                                          key={cIdx}
                                          className={`py-2 px-3 ${
                                            cIdx > 0 ? "text-right font-mono" : "text-stone-800"
                                          }`}
                                        >
                                          {cell}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            {blk.note && (
                              <p className="mt-2 text-xs text-stone-500 italic">{blk.note}</p>
                            )}
                          </figure>
                        );
                      }

                      if (blk.type === "theorem") {
                        const theme = getCalloutTheme(blk.kind);
                        return (
                          <div
                            key={idx}
                            id={blk.tag ? `tag-${blk.tag}` : undefined}
                            className={`my-5 p-4 sm:p-5 rounded-r-xl border ${theme.border} ${theme.bg} space-y-2.5`}
                          >
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex flex-wrap items-center gap-2">
                                <span
                                  className={`text-xs font-bold px-2 py-0.5 rounded border ${theme.badge}`}
                                >
                                  {blk.kind} {blk.number}
                                </span>
                                {blk.title && (
                                  <span
                                    className="text-sm font-bold text-stone-900"
                                    dangerouslySetInnerHTML={{
                                      __html: `(${renderMathProseToHtml(blk.title)})`,
                                    }}
                                  />
                                )}
                              </div>
                              {blk.tag && (
                                <a
                                  href={`https://kerodon.net/tag/${blk.tag}`}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-[11px] font-mono text-blue-700 hover:underline flex items-center gap-1"
                                >
                                  Tag {blk.tag} ↗
                                </a>
                              )}
                            </div>

                            <div
                              className="text-sm sm:text-base leading-relaxed text-stone-900"
                              dangerouslySetInnerHTML={{
                                __html: renderMathProseToHtml(blk.content ?? ""),
                              }}
                            />

                            {blk.diagrams && blk.diagrams.length > 0 && (
                              <div className="pt-3 space-y-3">
                                {blk.diagrams.map((d, dIdx) => (
                                  <div
                                    key={dIdx}
                                    className="bg-white p-3.5 rounded-lg border border-stone-200 flex flex-col items-center"
                                  >
                                    <img
                                      src={d.src}
                                      alt={d.caption}
                                      className="max-h-60 w-auto object-contain"
                                    />
                                    <span className="mt-2 text-[11px] text-stone-500 font-mono">
                                      {d.caption}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      }

                      if (blk.type === "math-paragraph") {
                        return (
                          <div
                            key={idx}
                            className="text-base leading-relaxed text-stone-900"
                            dangerouslySetInnerHTML={{
                              __html: renderMathProseToHtml(blk.content ?? ""),
                            }}
                          />
                        );
                      }

                      return (
                        <p
                          key={idx}
                          className="text-base sm:text-[17px] leading-[1.95] text-stone-800 indent-8"
                          dangerouslySetInnerHTML={{ __html: blk.html ?? blk.text ?? "" }}
                        />
                      );
                    })}
                  </div>
                </>
              )}
            </article>

            {surface === "split-pdfcn" && (
              <div className="bg-white rounded-2xl border border-stone-200 p-4 shadow-2xs sticky top-20 h-[calc(100vh-6rem)] flex flex-col">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-stone-200">
                  <div>
                    <div className="text-xs font-bold text-stone-900">
                      pdfcn Synchronized Print Deliverable
                    </div>
                    <div className="text-[11px] text-stone-500">
                      Comparing Web ({activeBook.renderingMode}) vs. Print PDF (
                      {activeBook.deliverables.pdf})
                    </div>
                  </div>
                  <a
                    href={activeBook.deliverables.pdf}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-semibold text-amber-700 hover:underline flex items-center gap-1"
                  >
                    Open Full PDF <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <iframe
                  src={activeBook.deliverables.pdf}
                  title="Synchronized Print PDF"
                  className="w-full flex-1 rounded-xl border border-stone-200 bg-stone-100"
                />
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
