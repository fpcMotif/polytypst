import katex from "katex";

const KATEX_MACROS: Record<string, string> = {
  "\\mathscr": "\\mathcal",
  "\\id": "\\operatorname{id}",
  "\\Hom": "\\operatorname{Hom}",
  "\\Fun": "\\operatorname{Fun}",
  "\\Set": "\\operatorname{Set}",
  "\\Cat": "\\operatorname{Cat}",
  "\\Sing": "\\operatorname{Sing}",
  "\\SL": "\\operatorname{SL}",
  "\\GL": "\\operatorname{GL}",
};

export function escapeHtml(raw: string): string {
  return raw
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderTeXSegment(tex: string, displayMode: boolean): string {
  const cleaned = tex
    .replace(/\\textnormal\{/g, "\\text{")
    .replace(/\\varinjlim/g, "\\underset{\\longrightarrow}{\\lim}")
    .replace(/\\varprojlim/g, "\\underset{\\longleftarrow}{\\lim}")
    .replace(/(\^[0-9a-zA-Z]+)\^(\{[^}]+\})/g, "{$1}^$2")
    .trim();
  if (!cleaned) {
    return "";
  }
  try {
    return katex.renderToString(cleaned, {
      displayMode,
      throwOnError: false,
      strict: "ignore",
      trust: true,
      macros: { ...KATEX_MACROS },
    });
  } catch {
    return `<code class="text-xs font-mono text-amber-900 bg-amber-50 px-1 rounded">${escapeHtml(cleaned)}</code>`;
  }
}

export function renderMathProseToHtml(input: string): string {
  if (!input) {
    return "";
  }
  const displayChunks: string[] = [];
  let text = input.replace(/\$\$([\s\S]+?)\$\$/g, (_, mathBody: string) => {
    const idx = displayChunks.length;
    displayChunks.push(`<div class="math-display">${renderTeXSegment(mathBody, true)}</div>`);
    return `@@DISPLAY_MATH_${idx}@@`;
  });

  const inlineChunks: string[] = [];
  text = text.replace(/\$([^$]+?)\$/g, (_, mathBody: string) => {
    const idx = inlineChunks.length;
    const isMultilineEnv = mathBody.includes("\\begin{");
    inlineChunks.push(renderTeXSegment(mathBody, isMultilineEnv));
    return `@@INLINE_MATH_${idx}@@`;
  });

  let htmlOut = escapeHtml(text);
  htmlOut = htmlOut.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  htmlOut = htmlOut.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  htmlOut = htmlOut.replace(
    /\[([^\]]+)\]\((#[a-zA-Z0-9_:-]+)\)/g,
    (_, label: string, anchor: string) => {
      const normalized = anchor.replace("#fig:", "#serre-fig-");
      return `<a href="${normalized}" class="math-ref">${label}</a>`;
    },
  );
  htmlOut = htmlOut.replace(
    /\(Tag\s+([0-9A-Z]{4})\)/g,
    '(<a href="https://kerodon.net/tag/$1" target="_blank" rel="noreferrer" class="math-tag">Tag $1</a>)',
  );

  htmlOut = htmlOut.replace(/@@INLINE_MATH_(\d+)@@/g, (_, idxStr: string) => {
    return inlineChunks[Number(idxStr)] ?? "";
  });
  htmlOut = htmlOut.replace(/@@DISPLAY_MATH_(\d+)@@/g, (_, idxStr: string) => {
    return displayChunks[Number(idxStr)] ?? "";
  });

  return htmlOut;
}
