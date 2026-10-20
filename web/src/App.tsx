import React, { useEffect, useMemo, useState } from "react";
import { BookPicker } from "./BookPicker";
import { useMutation, useQuery } from "convex/react";
import { api } from "../convex/_generated/api";
import { ChapterData, ContentBlock } from "./types";
import { escapeHtml, renderHtmlWithMath, renderMathProseToHtml } from "./mathRenderer";
import { VerticalReader } from "./VerticalReader";
import { Download, ExternalLink, Search } from "lucide-react";

type ViewSurface = "reader" | "split-pdfcn" | "deliverables";

const VIEWS: { id: ViewSurface; label: string }[] = [
  { id: "reader", label: "Read" },
  { id: "split-pdfcn", label: "Read + PDF" },
  { id: "deliverables", label: "Files" },
];

const focusRing =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900";

const inputClass =
  "w-full px-3 py-2 text-sm rounded-md border border-stone-300 bg-white placeholder:text-stone-400 focus:outline-none focus:border-stone-900";

function getTheoremStyle(kind: string = "") {
  const k = kind.toLowerCase();
  const plain = ["thm", "théorème", "theorem", "prop", "lemme", "lemma", "cor", "conj"].some((s) =>
    k.includes(s),
  );
  const definition = ["def", "déf", "notation", "construction", "example", "exemple"].some((s) =>
    k.includes(s),
  );
  return {
    rule: plain || definition || k.includes("warn"),
    italicBody: plain,
    remarkHead: !plain && !definition,
  };
}

function renderTheoremHtml(blk: ContentBlock): string {
  const style = getTheoremStyle(blk.kind);
  const number = (blk.number ?? "").replace(/\.$/, "");
  const label = [blk.kind ?? "", number].filter(Boolean).join(" ");
  const tag = blk.tag
    ? `<a class="thm-tag" href="https://kerodon.net/tag/${escapeHtml(blk.tag)}" target="_blank" rel="noreferrer">${escapeHtml(blk.tag)}</a>`
    : "";
  const note = blk.title
    ? ` <span class="thm-note">(${renderMathProseToHtml(blk.title)})</span>`
    : "";
  const head = `<span class="thm-head${style.remarkHead ? " thm-head-remark" : ""}">${escapeHtml(label)}.</span>`;
  return `${tag}${head}${note} ${renderMathProseToHtml(blk.content ?? "")}`;
}

function shortBookTitle(title: string): string {
  return title.split("：")[0].split("—")[0].trim();
}

function RichText({ text, math }: { text: string; math: boolean }) {
  if (!math) return <>{text}</>;
  return <span dangerouslySetInnerHTML={{ __html: renderMathProseToHtml(text) }} />;
}

export function App() {
  const [selectedBookSlug, setSelectedBookSlug] = useState<string>(
    () => new URLSearchParams(location.search).get("book") ?? "modern-firm",
  );
  const [selectedChapterSlug, setSelectedChapterSlug] = useState<string>(
    () => new URLSearchParams(location.search).get("ch") ?? "",
  );
  const [surface, setSurface] = useState<ViewSurface>("reader");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [readerName, setReaderName] = useState<string>("");
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

  useEffect(() => {
    if (!activeBook || !effectiveChapterSlug) return;
    const params = new URLSearchParams({ book: activeBook.slug, ch: effectiveChapterSlug });
    history.replaceState(null, "", `?${params}`);
  }, [activeBook, effectiveChapterSlug]);

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

  async function handleInspectSource(url: string, format: string) {
    const resp = await fetch(url);
    const text = await resp.text();
    setSourcePreview({ format, content: text.slice(0, 18000) });
    setSurface("deliverables");
  }

  async function handleAddAnnotation(e: React.FormEvent) {
    e.preventDefault();
    if (!activeBook || !activeChapter || !noteText.trim()) return;
    await addAnnotationMutation({
      bookSlug: activeBook.slug,
      chapterSlug: activeChapter.slug,
      readerName: readerName.trim() || "Reader",
      quoteText: quoteText || activeChapter.title,
      note: noteText,
    });
    setQuoteText("");
    setNoteText("");
  }

  if (!activeBook || !convexBooks) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f6f5f2] text-sm text-stone-500">
        Loading…
      </div>
    );
  }

  const isVertical = activeBook.renderingMode === "vertical-classic";
  const isMath = activeBook.renderingMode === "math-katex";
  const editions = activeBook.editions?.length
    ? activeBook.editions
    : [{ name: "main", label: "", ...activeBook.deliverables }];
  const files = editions.flatMap((ed) =>
    [
      { label: "PDF", note: "Print edition", href: ed.pdf, source: false },
      { label: "EPUB", note: "Reflowable e-book", href: ed.epub, source: false },
      { label: "Typst", note: ".typ source", href: ed.typst, source: true },
      { label: "LaTeX", note: ".tex source", href: ed.latex, source: true },
    ]
      .filter((file): file is typeof file & { href: string } => Boolean(file.href))
      .map((file) => ({
        ...file,
        key: `${ed.name}-${file.label}`,
        label: ed.label ? `${ed.label} · ${file.label}` : file.label,
      })),
  );

  return (
    <div className="min-h-screen bg-[#f6f5f2] text-stone-900">
      <header className="sticky top-0 z-30 border-b border-stone-200 bg-[#f6f5f2]/90 backdrop-blur">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 h-14 flex items-center gap-4 sm:gap-8">
          <span className="font-serif text-lg font-semibold tracking-tight shrink-0">
            Polytypst
          </span>

          <BookPicker
            books={convexBooks}
            activeSlug={activeBook.slug}
            label={shortBookTitle(activeBook.title)}
            onSelect={(slug) => {
              setSelectedBookSlug(slug);
              setSelectedChapterSlug("");
              setSourcePreview(null);
            }}
          />

          <div
            role="tablist"
            aria-label="View"
            className="hidden md:flex shrink-0 items-center rounded-md bg-stone-200/60 p-0.5"
          >
            {VIEWS.map((view) => (
              <button
                key={view.id}
                role="tab"
                aria-selected={surface === view.id}
                onClick={() => setSurface(view.id)}
                className={`px-3 py-1 rounded text-sm transition-colors ${focusRing} ${
                  surface === view.id
                    ? "bg-white text-stone-900 shadow-[0_1px_2px_rgb(0_0_0/0.08)]"
                    : "text-stone-500 hover:text-stone-900"
                }`}
              >
                {view.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 lg:py-10 lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:gap-10">
        <aside className="space-y-6 mb-6 lg:mb-0 lg:sticky lg:top-24 lg:self-start lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto lg:overscroll-contain">
          <div>
            <h1 className="font-serif text-xl font-semibold leading-snug">
              {shortBookTitle(activeBook.title)}
            </h1>
            <p className="mt-1 text-sm text-stone-500">{activeBook.author}</p>
            <div className="mt-3 flex items-center gap-2">
              <a
                href={activeBook.deliverables.pdf}
                target="_blank"
                rel="noreferrer"
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-stone-900 text-white hover:bg-stone-700 transition-colors ${focusRing}`}
              >
                <Download className="w-4 h-4" strokeWidth={1.75} />
                PDF
              </a>
              {activeBook.deliverables.epub && (
                <a
                  href={activeBook.deliverables.epub}
                  download
                  className={`inline-flex items-center px-3 py-1.5 rounded-md text-sm text-stone-700 hover:bg-stone-200/60 transition-colors ${focusRing}`}
                >
                  EPUB
                </a>
              )}
            </div>
          </div>

          <div className="relative">
            <Search
              className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2"
              strokeWidth={1.75}
            />
            <input
              type="search"
              aria-label="Search this chapter"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search this chapter"
              className={`${inputClass} pl-9`}
            />
          </div>

          <div className="md:hidden">
            <select
              aria-label="View"
              value={surface}
              onChange={(e) => setSurface(e.target.value as ViewSurface)}
              className={inputClass}
            >
              {VIEWS.map((view) => (
                <option key={view.id} value={view.id}>
                  {view.label}
                </option>
              ))}
            </select>
          </div>

          <div className="lg:hidden">
            <select
              aria-label="Chapter"
              value={effectiveChapterSlug}
              onChange={(e) => setSelectedChapterSlug(e.target.value)}
              className={inputClass}
            >
              {activeBook.chapterSummaries.map((ch) => (
                <option key={ch.slug} value={ch.slug}>
                  {ch.number} · {ch.title.replace(/\$/g, "")}
                </option>
              ))}
            </select>
          </div>

          <nav aria-label="Contents" className="hidden lg:block">
            <div className="text-xs font-medium text-stone-500 mb-2">Contents</div>
            <ol className="space-y-0.5 border-l border-stone-200">
              {activeBook.chapterSummaries.map((ch) => {
                const active = ch.slug === effectiveChapterSlug;
                return (
                  <li key={ch.slug}>
                    <button
                      aria-current={active ? "true" : undefined}
                      onClick={() => setSelectedChapterSlug(ch.slug)}
                      className={`-ml-px w-full text-left pl-3 pr-2 py-1.5 border-l text-sm leading-snug transition-colors ${focusRing} ${
                        active
                          ? "border-stone-900 text-stone-900 font-medium"
                          : "border-transparent text-stone-500 hover:text-stone-900"
                      }`}
                    >
                      <span className="block text-xs text-stone-400 tabular-nums">{ch.number}</span>
                      <RichText text={ch.title} math={isMath} />
                    </button>
                  </li>
                );
              })}
            </ol>
          </nav>

          <details className="group border-t border-stone-200 pt-4">
            <summary
              className={`flex items-center justify-between cursor-pointer list-none text-sm font-medium text-stone-700 ${focusRing}`}
            >
              Notes
              <span className="text-xs text-stone-400 tabular-nums">
                {convexAnnotations?.length ?? 0}
              </span>
            </summary>

            <form onSubmit={handleAddAnnotation} className="mt-3 space-y-2">
              <input
                type="text"
                aria-label="Your name"
                value={readerName}
                onChange={(e) => setReaderName(e.target.value)}
                placeholder="Your name"
                className={inputClass}
              />
              <input
                type="text"
                aria-label="Reference"
                value={quoteText}
                onChange={(e) => setQuoteText(e.target.value)}
                placeholder="Reference, e.g. Tag 000R"
                className={inputClass}
              />
              <textarea
                aria-label="Note"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Write a note"
                rows={3}
                className={inputClass}
              />
              <button
                type="submit"
                disabled={!noteText.trim()}
                className={`w-full py-2 rounded-md text-sm font-medium bg-stone-900 text-white hover:bg-stone-700 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors ${focusRing}`}
              >
                Add note
              </button>
            </form>

            {convexAnnotations && convexAnnotations.length > 0 && (
              <ul className="mt-4 space-y-3">
                {convexAnnotations.map((ann) => (
                  <li key={ann._id} className="text-sm">
                    <div className="text-xs text-stone-400">
                      {ann.readerName} · {ann.quoteText}
                    </div>
                    <p className="text-stone-700">{ann.note}</p>
                  </li>
                ))}
              </ul>
            )}
          </details>
        </aside>

        {surface === "deliverables" ? (
          <section className="space-y-8">
            <div>
              <h2 className="font-serif text-2xl font-semibold">Files</h2>
              <p className="mt-1 text-sm text-stone-500">
                Print and source files for {shortBookTitle(activeBook.title)}.
              </p>
            </div>

            <ul className="divide-y divide-stone-200 border-y border-stone-200">
              {files.map((file) => (
                <li key={file.key} className="flex items-center justify-between gap-4 py-3">
                  <div>
                    <div className="text-sm font-medium">{file.label}</div>
                    <div className="text-xs text-stone-500">{file.note}</div>
                  </div>
                  <div className="flex items-center gap-1">
                    {file.source && (
                      <button
                        onClick={() => handleInspectSource(file.href, file.label)}
                        className={`px-3 py-1.5 rounded-md text-sm text-stone-700 hover:bg-stone-200/60 transition-colors ${focusRing}`}
                      >
                        Preview
                      </button>
                    )}
                    <a
                      href={file.href}
                      target="_blank"
                      rel="noreferrer"
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm text-stone-700 hover:bg-stone-200/60 transition-colors ${focusRing}`}
                    >
                      <Download className="w-4 h-4" strokeWidth={1.75} />
                      Download
                    </a>
                  </div>
                </li>
              ))}
            </ul>

            {sourcePreview && (
              <div>
                <div className="mb-2 text-sm font-medium">{sourcePreview.format}</div>
                <pre className="p-4 rounded-lg bg-white text-xs font-mono text-stone-800 overflow-auto overscroll-contain max-h-[420px] leading-relaxed shadow-[0_0_0_1px_rgb(0_0_0/0.06)]">
                  {sourcePreview.content}
                </pre>
              </div>
            )}

            <iframe
              src={activeBook.deliverables.pdf}
              title="PDF preview"
              className="w-full h-[720px] rounded-lg bg-white shadow-[0_0_0_1px_rgb(0_0_0/0.06)]"
            />
          </section>
        ) : (
          <section
            className={`grid gap-6 ${
              surface === "split-pdfcn" ? "grid-cols-1 xl:grid-cols-2" : "grid-cols-1"
            }`}
          >
            <article className="bg-white rounded-lg px-5 py-8 sm:px-12 sm:py-14 shadow-[0_0_0_1px_rgb(0_0_0/0.05),0_1px_3px_rgb(0_0_0/0.04)]">
              {!activeChapter ? (
                <div className="py-16 text-center text-sm text-stone-400">Loading chapter…</div>
              ) : (
                <>
                  <header className="mb-10 math-column">
                    <div className="flex items-baseline justify-between gap-4 text-sm text-stone-500">
                      <span>{activeChapter.number}</span>
                      {activeChapter.tag && (
                        <a
                          href={`https://kerodon.net/tag/${activeChapter.tag}`}
                          target="_blank"
                          rel="noreferrer"
                          className="math-tag text-sm"
                        >
                          Tag {activeChapter.tag}
                        </a>
                      )}
                    </div>
                    <h2
                      className={`mt-2 text-3xl sm:text-4xl font-bold leading-tight text-stone-900 ${
                        isMath ? "math-serif" : "font-serif"
                      }`}
                    >
                      <RichText text={activeChapter.title} math={isMath} />
                    </h2>
                  </header>

                  {isVertical ? (
                    <VerticalReader
                      chapter={activeChapter}
                      bookTitle={shortBookTitle(activeBook.title)}
                      legend={activeBook.legend}
                    />
                  ) : (
                    <>
                      {filteredBlocks.length === 0 && (
                        <p className="text-center text-sm text-stone-400">
                          Nothing in this chapter matches “{searchQuery}”.
                        </p>
                      )}

                      <div
                        lang={activeBook.language}
                        className={`math-column ${isMath ? "math-prose" : "editorial-prose space-y-5"}`}
                      >
                        {filteredBlocks.map((blk, idx) => {
                          if (blk.type === "heading") {
                            const Tag = blk.level === 2 ? "h3" : "h4";
                            return (
                              <Tag
                                key={idx}
                                className={
                                  isMath
                                    ? `math-heading ${blk.level === 2 ? "math-heading-2" : "math-heading-3"}`
                                    : `font-serif font-bold text-stone-900 pt-4 ${
                                        blk.level === 2 ? "text-xl" : "text-lg"
                                      }`
                                }
                              >
                                <RichText text={blk.text ?? ""} math={isMath} />
                              </Tag>
                            );
                          }

                          if (blk.type === "figure") {
                            return (
                              <figure key={idx} id={blk.id} className="my-10 scroll-mt-24">
                                <div className="flex justify-center">
                                  <img
                                    src={blk.src}
                                    alt={blk.caption ?? blk.label}
                                    className="math-figure-img max-h-[420px] w-auto object-contain"
                                  />
                                </div>
                                {(blk.label || blk.caption) && (
                                  <figcaption className="mt-3 text-center text-sm text-stone-600">
                                    {blk.label && (
                                      <span className="font-semibold text-stone-900">
                                        {blk.label}{" "}
                                      </span>
                                    )}
                                    {blk.caption && <RichText text={blk.caption} math={isMath} />}
                                  </figcaption>
                                )}
                              </figure>
                            );
                          }

                          if (blk.type === "table" && blk.headers && blk.rows) {
                            return (
                              <figure key={idx} id={blk.id} className="my-10 scroll-mt-24">
                                <figcaption className="mb-3 text-sm text-stone-600">
                                  <span className="font-semibold text-stone-900">{blk.label} </span>
                                  {blk.caption}
                                </figcaption>
                                <div className="overflow-x-auto">
                                  <table className="w-full border-collapse text-sm">
                                    <thead>
                                      <tr className="border-y border-stone-900">
                                        {blk.headers.map((h, hIdx) => (
                                          <th
                                            key={hIdx}
                                            className={`py-2 px-3 font-semibold ${
                                              hIdx > 0 ? "text-right" : "text-left"
                                            }`}
                                          >
                                            {h}
                                          </th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody className="border-b border-stone-900">
                                      {blk.rows.map((row, rIdx) => (
                                        <tr key={rIdx}>
                                          {row.map((cell, cIdx) => (
                                            <td
                                              key={cIdx}
                                              className={`py-1.5 px-3 ${
                                                cIdx > 0 ? "text-right tabular-nums" : "text-left"
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
                                  <p className="mt-2 text-xs text-stone-500">{blk.note}</p>
                                )}
                              </figure>
                            );
                          }

                          if (blk.type === "theorem") {
                            const style = getTheoremStyle(blk.kind);
                            return (
                              <section
                                key={idx}
                                id={blk.tag ? `tag-${blk.tag}` : undefined}
                                className={`thm scroll-mt-24 ${style.rule ? "thm-rule" : ""}`}
                              >
                                <div
                                  className={style.italicBody ? "thm-italic" : undefined}
                                  dangerouslySetInnerHTML={{ __html: renderTheoremHtml(blk) }}
                                />

                                {blk.diagrams && blk.diagrams.length > 0 && (
                                  <div className="mt-4 space-y-4">
                                    {blk.diagrams.map((d, dIdx) => (
                                      <figure key={dIdx} className="flex flex-col items-center">
                                        <img
                                          src={d.src}
                                          alt={d.caption}
                                          className="max-h-60 w-auto object-contain"
                                        />
                                        <figcaption className="thm-tag !float-none mt-1">
                                          {d.caption}
                                        </figcaption>
                                      </figure>
                                    ))}
                                  </div>
                                )}
                              </section>
                            );
                          }

                          if (blk.type === "html") {
                            return (
                              <div
                                key={idx}
                                className="html-block"
                                dangerouslySetInnerHTML={{
                                  __html: renderHtmlWithMath(blk.html ?? ""),
                                }}
                              />
                            );
                          }

                          if (blk.type === "math-paragraph") {
                            return (
                              <div
                                key={idx}
                                dangerouslySetInnerHTML={{
                                  __html: renderMathProseToHtml(blk.content ?? ""),
                                }}
                              />
                            );
                          }

                          return (
                            <p
                              key={idx}
                              className={
                                isMath
                                  ? undefined
                                  : "text-[17px] leading-[1.9] text-stone-800 indent-8"
                              }
                              dangerouslySetInnerHTML={{ __html: blk.html ?? blk.text ?? "" }}
                            />
                          );
                        })}
                      </div>
                    </>
                  )}
                </>
              )}
            </article>

            {surface === "split-pdfcn" && (
              <div className="xl:sticky xl:top-24 h-[80vh] xl:h-[calc(100vh-8rem)] flex flex-col">
                <div className="flex items-center justify-between mb-2 text-sm">
                  <span className="text-stone-500">Print edition</span>
                  <a
                    href={activeBook.deliverables.pdf}
                    target="_blank"
                    rel="noreferrer"
                    className={`inline-flex items-center gap-1 text-stone-700 hover:text-stone-900 ${focusRing}`}
                  >
                    Open <ExternalLink className="w-3.5 h-3.5" strokeWidth={1.75} />
                  </a>
                </div>
                <iframe
                  src={activeBook.deliverables.pdf}
                  title="Print edition PDF"
                  className="w-full flex-1 rounded-lg bg-white shadow-[0_0_0_1px_rgb(0_0_0/0.06)]"
                />
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
