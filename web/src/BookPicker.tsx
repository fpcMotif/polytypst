import { useEffect, useMemo, useRef, useState } from "react";
import { BookOpen, ChevronDown, Search } from "lucide-react";

export interface PickerBook {
  slug: string;
  title: string;
  author: string;
  domain: string;
}

const focusRing =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900";

export function BookPicker({
  books,
  activeSlug,
  label,
  onSelect,
}: {
  books: PickerBook[];
  activeSlug: string;
  label: string;
  onSelect: (slug: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return books;
    return books.filter((b) =>
      [b.title, b.author, b.domain, b.slug].join(" ").toLowerCase().includes(q),
    );
  }, [books, query]);

  const groups = useMemo(() => {
    const byDomain = new Map<string, PickerBook[]>();
    for (const b of matches) byDomain.set(b.domain, [...(byDomain.get(b.domain) ?? []), b]);
    return [...byDomain.entries()];
  }, [matches]);
  const ordered = groups.flatMap(([, list]) => list);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const onPointer = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointer);
    return () => document.removeEventListener("pointerdown", onPointer);
  }, [open]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  function choose(slug: string) {
    onSelect(slug);
    setOpen(false);
    setQuery("");
  }

  function onInputKey(e: React.KeyboardEvent) {
    if (e.key === "Escape") setOpen(false);
    else if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, ordered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter" && ordered[cursor]) choose(ordered[cursor].slug);
  }

  return (
    <div ref={rootRef} className="relative min-w-0 flex-1">
      <button
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className={`flex max-w-full items-center gap-2 rounded-md px-3 py-1.5 text-sm bg-white shadow-[0_0_0_1px_rgb(0_0_0/0.08),0_1px_2px_rgb(0_0_0/0.06)] hover:bg-stone-50 ${focusRing}`}
      >
        <BookOpen className="w-4 h-4 shrink-0 text-stone-500" strokeWidth={1.75} />
        <span className="truncate font-medium">{label}</span>
        <span className="hidden sm:inline shrink-0 text-xs text-stone-400 tabular-nums">
          {books.length} books
        </span>
        <ChevronDown className="w-4 h-4 shrink-0 text-stone-400" strokeWidth={1.75} />
      </button>

      {open && (
        <div
          aria-label="Choose a book"
          className="absolute left-0 top-full mt-2 w-[min(32rem,calc(100vw-2rem))] rounded-lg bg-white shadow-[0_0_0_1px_rgb(0_0_0/0.08),0_12px_32px_-8px_rgb(0_0_0/0.2)] overflow-hidden"
        >
          <div className="relative border-b border-stone-200">
            <Search
              className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2"
              strokeWidth={1.75}
            />
            <input
              ref={inputRef}
              type="search"
              aria-label="Search books"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setCursor(0);
              }}
              onKeyDown={onInputKey}
              placeholder="Search title, author, or subject"
              className="w-full pl-9 pr-3 py-3 text-sm bg-transparent placeholder:text-stone-400 focus:outline-none"
            />
          </div>
          <div className="max-h-[min(28rem,70vh)] overflow-y-auto overscroll-contain py-2">
            {groups.length === 0 && (
              <p className="px-4 py-6 text-center text-sm text-stone-400">No book matches.</p>
            )}
            {groups.map(([domain, list]) => (
              <div key={domain} className="pb-1">
                <div className="px-4 pt-2 pb-1 text-xs font-medium text-stone-400">{domain}</div>
                {list.map((b) => {
                  const idx = ordered.indexOf(b);
                  const active = b.slug === activeSlug;
                  return (
                    <button
                      key={b.slug}
                      onClick={() => choose(b.slug)}
                      onMouseEnter={() => setCursor(idx)}
                      className={`block w-full text-left px-4 py-2 ${
                        idx === cursor ? "bg-stone-100" : ""
                      }`}
                    >
                      <span
                        className={`block text-sm leading-snug ${active ? "font-semibold" : ""}`}
                      >
                        {b.title}
                      </span>
                      <span className="block text-xs text-stone-500">{b.author}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
