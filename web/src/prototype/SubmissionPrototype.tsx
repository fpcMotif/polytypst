// PROTOTYPE — throwaway. Question: what should dropping a Submission and following it to an
// Edition look like? Three variants on the reader's "New edition" view, switched by ?variant=.
// Everything is in memory and simulated; nothing calls Convex or an OCR backend.
import React, { useEffect, useRef, useState } from "react";
import { Check, FileText, Loader2, Mail, Upload, X } from "lucide-react";
import { PrototypeSwitcher, readVariant } from "./PrototypeSwitcher";

type Backend = "colab" | "mistral" | "jina";
type Stage = "idle" | "detecting" | "ocr" | "typesetting" | "ready";
type PageState = "text" | "scan" | "ocr-running" | "ocr-done";

type Submission = {
  id: number;
  name: string;
  kind: "PDF" | "EPUB" | "HTML";
  sizeMb: number;
  pages: PageState[];
  backend: Backend;
  tempKey: string;
  email: string;
  stage: Stage;
  typesetPct: number;
};

const BACKENDS: { id: Backend; label: string; note: string }[] = [
  { id: "colab", label: "Polytypst GPU", note: "Default. Free for invited readers." },
  { id: "mistral", label: "Mistral OCR 4.1", note: "Your key, about $4 per 1,000 pages." },
  { id: "jina", label: "Jina OCR", note: "Your key. Strong on formulas." },
];

const STAGES: { id: Stage; label: string }[] = [
  { id: "detecting", label: "Check pages" },
  { id: "ocr", label: "Read scanned pages" },
  { id: "typesetting", label: "Typeset" },
  { id: "ready", label: "Edition emailed" },
];

const stageIndex = (s: Stage) => STAGES.findIndex((x) => x.id === s);

let nextId = 1;

function makeSubmission(name: string, sizeMb: number): Submission {
  const ext = name.split(".").pop()?.toLowerCase();
  const kind = ext === "epub" ? "EPUB" : ext === "html" || ext === "htm" ? "HTML" : "PDF";
  const total = kind === "PDF" ? 184 : 0;
  const pages: PageState[] = Array.from({ length: total }, (_, i) =>
    i >= 40 && i < 112 ? "scan" : "text",
  );
  return {
    id: nextId++,
    name,
    kind,
    sizeMb,
    pages,
    backend: "colab",
    tempKey: "",
    email: "reader@example.com",
    stage: "idle",
    typesetPct: 0,
  };
}

function tick(s: Submission): Submission {
  if (s.stage === "detecting") return { ...s, stage: s.pages.some((p) => p === "scan") ? "ocr" : "typesetting" };
  if (s.stage === "ocr") {
    const pages = [...s.pages];
    const running = pages.indexOf("ocr-running");
    if (running >= 0) pages[running] = "ocr-done";
    for (let n = 0; n < 3; n++) {
      const next = pages.indexOf("scan");
      if (next >= 0) pages[next] = n === 2 ? "ocr-running" : "ocr-done";
    }
    const done = !pages.includes("scan") && !pages.includes("ocr-running");
    return { ...s, pages, stage: done ? "typesetting" : "ocr" };
  }
  if (s.stage === "typesetting") {
    const typesetPct = Math.min(100, s.typesetPct + 12);
    return { ...s, typesetPct, stage: typesetPct === 100 ? "ready" : "typesetting" };
  }
  return s;
}

function useSubmissions(seed: Submission[] = []) {
  const [subs, setSubs] = useState<Submission[]>(seed);
  const running = subs.some((s) => s.stage !== "idle" && s.stage !== "ready");
  useEffect(() => {
    if (!running) return;
    const t = window.setInterval(() => setSubs((all) => all.map(tick)), 350);
    return () => window.clearInterval(t);
  }, [running]);
  const update = (id: number, patch: Partial<Submission>) =>
    setSubs((all) => all.map((s) => (s.id === id ? { ...s, ...patch } : s)));
  return { subs, setSubs, update };
}

const ocrCounts = (s: Submission) => {
  const scans = s.pages.filter((p) => p !== "text").length;
  const done = s.pages.filter((p) => p === "ocr-done").length;
  return { scans, done, total: s.pages.length };
};

function progressPct(s: Submission): number {
  if (s.stage === "idle") return 0;
  if (s.stage === "ready") return 100;
  if (s.stage === "detecting") return 4;
  const { scans, done } = ocrCounts(s);
  const ocr = scans ? done / scans : 1;
  return Math.round(5 + ocr * 65 + (s.typesetPct / 100) * 30);
}

function fileFromEvent(e: React.DragEvent | React.ChangeEvent<HTMLInputElement>) {
  const list = "dataTransfer" in e ? e.dataTransfer.files : e.target.files;
  const f = list?.[0];
  return f ? { name: f.name, sizeMb: Math.max(0.1, Math.round((f.size / 1e6) * 10) / 10) } : null;
}

const SAMPLE = { name: "Ahlfors - Complex Analysis (scan).pdf", sizeMb: 38.4 };

const btn =
  "inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900";
const primary = `${btn} bg-stone-900 text-white hover:bg-stone-700 disabled:bg-stone-300`;
const ghost = `${btn} text-stone-700 hover:bg-stone-200/60`;
const input =
  "w-full px-3 py-2 text-sm rounded-md border border-stone-300 bg-white placeholder:text-stone-400 focus:outline-none focus:border-stone-900";

function BackendPicker({ s, onChange }: { s: Submission; onChange: (p: Partial<Submission>) => void }) {
  return (
    <div className="space-y-2">
      {BACKENDS.map((b) => (
        <label key={b.id} className="flex items-start gap-3 text-sm cursor-pointer">
          <input
            type="radio"
            name={`backend-${s.id}`}
            checked={s.backend === b.id}
            onChange={() => onChange({ backend: b.id })}
            className="mt-1 accent-stone-900"
          />
          <span>
            <span className="font-medium">{b.label}</span>
            <span className="block text-xs text-stone-500">{b.note}</span>
          </span>
        </label>
      ))}
      {s.backend !== "colab" && (
        <div className="pl-7">
          <input
            type="password"
            aria-label="Temporary API key"
            placeholder={`${s.backend === "mistral" ? "Mistral" : "Jina"} API key`}
            value={s.tempKey}
            onChange={(e) => onChange({ tempKey: e.target.value })}
            className={input}
          />
          <p className="mt-1 text-xs text-stone-500">
            Used for this Submission only, then erased. Never stored on your profile.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Variant A: one quiet column, form then stepper ──────────────────────────
function VariantA() {
  const { subs, setSubs, update } = useSubmissions();
  const s = subs[0];
  const [over, setOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const add = (f: { name: string; sizeMb: number } | null) => f && setSubs([makeSubmission(f.name, f.sizeMb)]);

  return (
    <article className="bg-white rounded-lg px-5 py-8 sm:px-12 sm:py-12 shadow-[0_0_0_1px_rgb(0_0_0/0.05),0_1px_3px_rgb(0_0_0/0.04)] max-w-2xl">
      <h2 className="font-serif text-2xl font-semibold">New edition</h2>
      <p className="mt-1 text-sm text-stone-500">
        Drop a PDF, EPUB or HTML file. We re-typeset it and email you a PDF and EPUB.
      </p>

      {!s ? (
        <div
          onDragOver={(e) => (e.preventDefault(), setOver(true))}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => (e.preventDefault(), setOver(false), add(fileFromEvent(e)))}
          className={`mt-8 rounded-lg border-2 border-dashed px-6 py-16 text-center transition-colors ${
            over ? "border-stone-900 bg-stone-50" : "border-stone-300"
          }`}
        >
          <Upload className="w-6 h-6 mx-auto text-stone-400" strokeWidth={1.5} />
          <p className="mt-3 text-sm">Drop a file here</p>
          <div className="mt-4 flex justify-center gap-2">
            <button className={ghost} onClick={() => fileRef.current?.click()}>Choose file</button>
            <button className={ghost} onClick={() => add(SAMPLE)}>Use a sample scan</button>
          </div>
          <input ref={fileRef} type="file" hidden accept=".pdf,.epub,.html,.htm" onChange={(e) => add(fileFromEvent(e))} />
        </div>
      ) : (
        <div className="mt-8 space-y-8">
          <div className="flex items-center gap-3 text-sm">
            <FileText className="w-5 h-5 text-stone-400" strokeWidth={1.5} />
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{s.name}</div>
              <div className="text-xs text-stone-500">
                {s.kind} · {s.sizeMb} MB
                {s.pages.length > 0 && ` · ${s.pages.length} pages, ${ocrCounts(s).scans} scanned`}
              </div>
            </div>
            {s.stage === "idle" && (
              <button aria-label="Remove file" className={ghost} onClick={() => setSubs([])}>
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {s.stage === "idle" ? (
            <>
              {ocrCounts(s).scans > 0 && (
                <section>
                  <h3 className="text-sm font-medium mb-3">Read the {ocrCounts(s).scans} scanned pages with</h3>
                  <BackendPicker s={s} onChange={(p) => update(s.id, p)} />
                </section>
              )}
              <section>
                <h3 className="text-sm font-medium mb-2">Email the edition to</h3>
                <input className={input} value={s.email} onChange={(e) => update(s.id, { email: e.target.value })} />
              </section>
              <button
                className={`${primary} w-full py-2`}
                disabled={s.backend !== "colab" && !s.tempKey}
                onClick={() => update(s.id, { stage: "detecting" })}
              >
                Make edition
              </button>
            </>
          ) : (
            <ol className="space-y-4">
              {STAGES.map((st, i) => {
                const cur = stageIndex(s.stage);
                const state = s.stage === "ready" || i < cur ? "done" : i === cur ? "now" : "todo";
                const { scans, done } = ocrCounts(s);
                return (
                  <li key={st.id} className="flex items-start gap-3 text-sm">
                    <span
                      className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                        state === "done" ? "bg-stone-900 text-white" : state === "now" ? "border-2 border-stone-900" : "border border-stone-300"
                      }`}
                    >
                      {state === "done" && <Check className="w-3 h-3" strokeWidth={3} />}
                    </span>
                    <div className="flex-1">
                      <div className={state === "todo" ? "text-stone-400" : "font-medium"}>{st.label}</div>
                      {st.id === "ocr" && state !== "todo" && (
                        <div className="text-xs text-stone-500 tabular-nums">
                          {done} / {scans} pages · {BACKENDS.find((b) => b.id === s.backend)?.label}
                        </div>
                      )}
                      {st.id === "typesetting" && state === "now" && (
                        <div className="mt-1.5 h-1 rounded bg-stone-200 overflow-hidden">
                          <div className="h-full bg-stone-900 transition-all" style={{ width: `${s.typesetPct}%` }} />
                        </div>
                      )}
                      {st.id === "ready" && state === "done" && (
                        <div className="text-xs text-stone-500">
                          Sent to {s.email}. The link works for 7 days.
                          <div className="mt-2 flex gap-2">
                            <button className={primary}>Download PDF</button>
                            <button className={ghost}>EPUB</button>
                          </div>
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </div>
      )}
    </article>
  );
}

// ─── Variant B: the whole page is a drop target, Submissions are a queue ─────
function seedQueue(): Submission[] {
  const done = makeSubmission("Kodaira - Complex Manifolds.pdf", 22.1);
  done.stage = "ready";
  done.pages = done.pages.map((p) => (p === "scan" ? "ocr-done" : p));
  done.typesetPct = 100;
  const epub = makeSubmission("Serre - A Course in Arithmetic.epub", 3.2);
  epub.stage = "typesetting";
  epub.typesetPct = 30;
  return [epub, done];
}

function VariantB() {
  const { subs, setSubs, update } = useSubmissions(seedQueue());
  const [over, setOver] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function add(f: { name: string; sizeMb: number } | null) {
    if (!f) return;
    const s = { ...makeSubmission(f.name, f.sizeMb), stage: "detecting" as Stage };
    setSubs((all) => [s, ...all]);
  }

  return (
    <section
      className="relative min-h-[70vh]"
      onDragOver={(e) => (e.preventDefault(), setOver(true))}
      onDragLeave={(e) => e.currentTarget === e.target && setOver(false)}
      onDrop={(e) => (e.preventDefault(), setOver(false), add(fileFromEvent(e)))}
    >
      {over && (
        <div className="absolute inset-0 z-20 rounded-lg border-2 border-dashed border-stone-900 bg-[#f6f5f2]/90 flex items-center justify-center font-serif text-xl">
          Drop to start a new edition
        </div>
      )}
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="font-serif text-2xl font-semibold">Your editions</h2>
          <p className="mt-1 text-sm text-stone-500">
            Drop files anywhere on this page. Each one starts right away with Polytypst GPU.
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          <button className={ghost} onClick={() => add(SAMPLE)}>Sample scan</button>
          <button className={primary} onClick={() => fileRef.current?.click()}>
            <Upload className="w-4 h-4" /> Add files
          </button>
          <input ref={fileRef} type="file" hidden accept=".pdf,.epub,.html,.htm" onChange={(e) => add(fileFromEvent(e))} />
        </div>
      </div>

      <ul className="mt-6 divide-y divide-stone-200 border-y border-stone-200">
        {subs.map((s) => {
          const pct = progressPct(s);
          const { scans, done } = ocrCounts(s);
          const label =
            s.stage === "ocr" ? `Reading scans ${done}/${scans}` : STAGES.find((x) => x.id === s.stage)?.label ?? "Waiting";
          return (
            <li key={s.id} className="py-3">
              <div className="grid grid-cols-[minmax(0,1fr)_9rem_12rem_auto] items-center gap-4 text-sm">
                <div className="min-w-0">
                  <div className="font-medium truncate">{s.name}</div>
                  <div className="text-xs text-stone-500">
                    {s.kind} · {s.sizeMb} MB{s.pages.length > 0 && ` · ${s.pages.length} pp`}
                  </div>
                </div>
                <span
                  className={`justify-self-start px-2 py-0.5 rounded-full text-xs ${
                    s.stage === "ready" ? "bg-emerald-100 text-emerald-800" : "bg-stone-200 text-stone-700"
                  }`}
                >
                  {label}
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded bg-stone-200 overflow-hidden">
                    <div
                      className={`h-full transition-all ${s.stage === "ready" ? "bg-emerald-600" : "bg-stone-900"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="w-9 text-right text-xs tabular-nums text-stone-500">{pct}%</span>
                </div>
                <div className="flex gap-1 justify-end">
                  {s.stage === "ready" ? (
                    <>
                      <button className={ghost}>PDF</button>
                      <button className={ghost}>EPUB</button>
                      <span title={`Emailed to ${s.email}`} className="p-1.5 text-stone-400">
                        <Mail className="w-4 h-4" />
                      </span>
                    </>
                  ) : (
                    <button className={ghost} onClick={() => setOpen(open === s.id ? null : s.id)}>
                      Options
                    </button>
                  )}
                </div>
              </div>
              {open === s.id && s.stage !== "ready" && (
                <div className="mt-3 ml-0 grid sm:grid-cols-2 gap-6 rounded-md bg-white p-4 shadow-[0_0_0_1px_rgb(0_0_0/0.06)]">
                  <div>
                    <div className="text-xs font-medium text-stone-500 mb-2">OCR for scanned pages</div>
                    <BackendPicker s={s} onChange={(p) => update(s.id, p)} />
                    <p className="mt-2 text-xs text-stone-500">Changing this restarts the scanned pages.</p>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-stone-500 mb-2">Email to</div>
                    <input className={input} value={s.email} onChange={(e) => update(s.id, { email: e.target.value })} />
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

// ─── Variant C: guided steps beside a live map of every page ─────────────────
const TILE: Record<PageState, string> = {
  text: "bg-stone-200",
  scan: "bg-amber-300",
  "ocr-running": "bg-sky-500 animate-pulse",
  "ocr-done": "bg-emerald-500",
};

function VariantC() {
  const { subs, setSubs, update } = useSubmissions();
  const s = subs[0];
  const [step, setStep] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const add = (f: { name: string; sizeMb: number } | null) => {
    if (!f) return;
    setSubs([makeSubmission(f.name, f.sizeMb)]);
    setStep(1);
  };
  const steps = ["Drop", "What we found", "Scanned pages", "Delivery", "Making it"];
  const counts = s ? ocrCounts(s) : null;

  return (
    <section className="grid lg:grid-cols-[22rem_minmax(0,1fr)] gap-8">
      <div className="space-y-6">
        <ol className="flex gap-1">
          {steps.map((label, i) => (
            <li key={label} className={`h-1 flex-1 rounded ${i <= step ? "bg-stone-900" : "bg-stone-300"}`} title={label} />
          ))}
        </ol>
        <div className="text-xs text-stone-500">
          Step {step + 1} of {steps.length} · {steps[step]}
        </div>

        {step === 0 && (
          <div>
            <h2 className="font-serif text-2xl font-semibold leading-snug">Which book should we re-typeset?</h2>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => (e.preventDefault(), add(fileFromEvent(e)))}
              className="mt-5 rounded-lg border-2 border-dashed border-stone-300 px-4 py-10 text-center text-sm"
            >
              Drop PDF, EPUB or HTML
              <div className="mt-3 flex justify-center gap-2">
                <button className={ghost} onClick={() => fileRef.current?.click()}>Choose</button>
                <button className={ghost} onClick={() => add(SAMPLE)}>Sample scan</button>
              </div>
              <input ref={fileRef} type="file" hidden accept=".pdf,.epub,.html,.htm" onChange={(e) => add(fileFromEvent(e))} />
            </div>
          </div>
        )}

        {step === 1 && s && counts && (
          <div>
            <h2 className="font-serif text-2xl font-semibold leading-snug">
              {counts.scans > 0
                ? `${counts.scans} of ${counts.total} pages are scans.`
                : "This file has real text throughout."}
            </h2>
            <p className="mt-2 text-sm text-stone-600">
              {counts.scans > 0
                ? "Pages with a text layer are used as they are. Only the amber pages need OCR."
                : "No OCR is needed, so no key is needed either."}
            </p>
            <button className={`${primary} mt-5`} onClick={() => setStep(counts.scans > 0 ? 2 : 3)}>Continue</button>
          </div>
        )}

        {step === 2 && s && (
          <div>
            <h2 className="font-serif text-2xl font-semibold leading-snug">Who should read the scans?</h2>
            <div className="mt-5">
              <BackendPicker s={s} onChange={(p) => update(s.id, p)} />
            </div>
            <button
              className={`${primary} mt-5`}
              disabled={s.backend !== "colab" && !s.tempKey}
              onClick={() => setStep(3)}
            >
              Continue
            </button>
          </div>
        )}

        {step === 3 && s && (
          <div>
            <h2 className="font-serif text-2xl font-semibold leading-snug">Where should the edition go?</h2>
            <input className={`${input} mt-5`} value={s.email} onChange={(e) => update(s.id, { email: e.target.value })} />
            <p className="mt-2 text-xs text-stone-500">Google Drive and Dropbox come later.</p>
            <button
              className={`${primary} mt-5`}
              onClick={() => (update(s.id, { stage: "detecting" }), setStep(4))}
            >
              Make edition
            </button>
          </div>
        )}

        {step === 4 && s && (
          <div>
            <h2 className="font-serif text-2xl font-semibold leading-snug">
              {s.stage === "ready" ? "Your edition is on its way." : STAGES.find((x) => x.id === s.stage)?.label + "…"}
            </h2>
            <p className="mt-2 text-sm text-stone-600 tabular-nums">
              {s.stage === "ocr" && `${counts?.done} of ${counts?.scans} scanned pages read.`}
              {s.stage === "typesetting" && `Typesetting ${s.typesetPct}%.`}
              {s.stage === "ready" && `Emailed to ${s.email}. You can close this page.`}
            </p>
            {s.stage !== "ready" && <Loader2 className="mt-4 w-5 h-5 animate-spin text-stone-400" />}
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg p-6 shadow-[0_0_0_1px_rgb(0_0_0/0.05)] min-h-[420px]">
        {!s ? (
          <div className="h-full flex items-center justify-center text-sm text-stone-400">
            Every page of your file will appear here.
          </div>
        ) : s.stage === "ready" ? (
          <div className="flex flex-col items-center justify-center h-full gap-5">
            <div className="w-40 aspect-[3/4] bg-[#f6f5f2] rounded shadow-md flex flex-col justify-end p-4">
              <div className="font-serif text-sm font-semibold leading-tight">{s.name.replace(/\.\w+$/, "")}</div>
              <div className="mt-1 text-[10px] text-stone-500">Polytypst edition</div>
            </div>
            <div className="flex gap-2">
              <button className={primary}>Download PDF</button>
              <button className={ghost}>EPUB</button>
            </div>
          </div>
        ) : s.pages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-stone-500">
            {s.kind} files have no pages to scan. Typesetting {s.typesetPct}%.
          </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-4 text-xs text-stone-500 mb-4">
              <span className="flex items-center gap-1.5"><i className="w-2.5 h-3 rounded-sm bg-stone-200" /> Text layer</span>
              <span className="flex items-center gap-1.5"><i className="w-2.5 h-3 rounded-sm bg-amber-300" /> Needs OCR</span>
              <span className="flex items-center gap-1.5"><i className="w-2.5 h-3 rounded-sm bg-sky-500" /> Reading</span>
              <span className="flex items-center gap-1.5"><i className="w-2.5 h-3 rounded-sm bg-emerald-500" /> Read</span>
            </div>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(14px,1fr))] gap-1">
              {s.pages.map((p, i) => (
                <div key={i} title={`Page ${i + 1}`} className={`aspect-[3/4] rounded-sm ${TILE[p]}`} />
              ))}
            </div>
            {s.stage === "typesetting" && (
              <div className="mt-6 h-1.5 rounded bg-stone-200 overflow-hidden">
                <div className="h-full bg-stone-900 transition-all" style={{ width: `${s.typesetPct}%` }} />
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}

const VARIANTS = [
  { key: "A", name: "Quiet form", Component: VariantA },
  { key: "B", name: "Queue", Component: VariantB },
  { key: "C", name: "Page map", Component: VariantC },
];

export function SubmissionPrototype() {
  const [variant, setVariant] = useState(() => readVariant(VARIANTS.map((v) => v.key)));
  const Active = VARIANTS.find((v) => v.key === variant)?.Component ?? VariantA;
  return (
    <>
      <Active key={variant} />
      <PrototypeSwitcher variants={VARIANTS} current={variant} onChange={setVariant} />
    </>
  );
}
