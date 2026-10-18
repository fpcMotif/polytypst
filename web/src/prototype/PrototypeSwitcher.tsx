import { useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

type Variant = { key: string; name: string };

export function readVariant(keys: string[]): string {
  const value = new URLSearchParams(window.location.search).get("variant") ?? keys[0];
  return keys.includes(value) ? value : keys[0];
}

export function PrototypeSwitcher({
  variants,
  current,
  onChange,
}: {
  variants: Variant[];
  current: string;
  onChange: (key: string) => void;
}) {
  const index = variants.findIndex((v) => v.key === current);

  function go(step: number) {
    const next = variants[(index + step + variants.length) % variants.length];
    const url = new URL(window.location.href);
    url.searchParams.set("variant", next.key);
    window.history.replaceState(null, "", url);
    onChange(next.key);
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement | null;
      if (t && (t.closest("input, textarea, select") || t.isContentEditable)) return;
      if (e.key === "ArrowLeft") go(-1);
      if (e.key === "ArrowRight") go(1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (!import.meta.env.DEV) return null;

  return (
    <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 flex items-center gap-1 rounded-full bg-fuchsia-600 text-white pl-1 pr-1 py-1 shadow-lg ring-2 ring-white text-sm">
      <button aria-label="Previous variant" onClick={() => go(-1)} className="p-1.5 rounded-full hover:bg-white/20">
        <ChevronLeft className="w-4 h-4" />
      </button>
      <span className="px-2 font-medium tabular-nums">
        PROTOTYPE · {current} ({variants[index]?.name})
      </span>
      <button aria-label="Next variant" onClick={() => go(1)} className="p-1.5 rounded-full hover:bg-white/20">
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}
