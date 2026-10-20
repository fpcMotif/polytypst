import { useMemo } from "react";
import type { ChapterData, LegendEntry } from "./types";
import {
  BAND_ROWS,
  COLUMN_WIDTH,
  COLUMNS_PER_LEAF,
  GUTTER,
  ROWS,
  layoutColumns,
  paginate,
  type Column,
  type Leaf,
} from "./verticalLayout";

const INK: Record<string, string> = {
  E73E29: "#b3382b",
  A70236: "#8f1d3c",
  "0E56A7": "#2b4f84",
  EC008C: "#a3326c",
  A46C35: "#87582c",
  "008080": "#2c6b66",
  "00AEEF": "#3a7fa6",
  "800080": "#6a3c78",
  "581600": "#5b2e14",
  FAA624: "#a97a22",
  F04E37: "#bf452f",
  F26C4B: "#b0442e",
};

export function inkColor(hex?: string): string | undefined {
  if (!hex || hex === "000000") return undefined;
  return INK[hex] ?? `#${hex}`;
}

const u = (n: number) => `calc(var(--cell) * ${n.toFixed(3)})`;

function ColumnView({ col, index }: { col: Column; index: number }) {
  return (
    <div
      className={`vcol vcol-${col.role}`}
      style={{ right: u(index * COLUMN_WIDTH), width: u(COLUMN_WIDTH) }}
    >
      {col.cells.map((cell, i) =>
        cell.kind === "char" ? (
          <span
            key={i}
            className="vchar"
            style={{ top: u(cell.row), right: u(GUTTER), color: inkColor(cell.color) }}
          >
            {cell.ch}
          </span>
        ) : (
          <span
            key={i}
            className="vjp"
            style={{
              top: u(cell.row),
              right: u(GUTTER),
              height: u(cell.rows),
              color: inkColor(cell.color) ?? "#3d372f",
            }}
          >
            <span className="vjp-line vjp-right">{cell.right}</span>
            <span className="vjp-line vjp-left">{cell.left}</span>
          </span>
        ),
      )}
      {col.side.map((note, i) => (
        <span
          key={`s${i}`}
          className={note.marker ? "vside vmarker" : "vside"}
          style={{
            top: u(note.row + 0.08),
            fontSize: u(note.font),
            maxHeight: u(ROWS - note.row),
            color: inkColor(note.color) ?? "#4a443b",
          }}
        >
          {note.text}
        </span>
      ))}
    </div>
  );
}

function LeafView({ leaf }: { leaf: Leaf }) {
  return (
    <div className="vleaf" style={{ width: u(COLUMNS_PER_LEAF * COLUMN_WIDTH + 0.6) }}>
      <div className="vband" style={{ height: u(BAND_ROWS) }}>
        {leaf.head.map((note, i) => (
          <span
            key={i}
            className="vhead"
            style={{
              right: u(note.right + 0.3),
              width: u(note.width),
              height: u(BAND_ROWS - 0.6),
              color: inkColor(note.color),
            }}
          >
            {note.labels && <span className="vhead-label">{note.labels}</span>}
            {note.text}
          </span>
        ))}
      </div>
      <div className="vframe">
        <div className="vbody" style={{ height: u(ROWS) }}>
          {Array.from({ length: COLUMNS_PER_LEAF - 1 }, (_, i) => (
            <span key={i} className="vrule" style={{ right: u((i + 1) * COLUMN_WIDTH) }} />
          ))}
          {leaf.columns.map((col, i) => (
            <ColumnView key={i} col={col} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

function Banxin({ title, hui, folio }: { title: string; hui: string; folio: number }) {
  return (
    <div className="vbanxin" aria-hidden="true">
      <span className="vbanxin-title">{title}</span>
      <span className="vfish" />
      <span className="vbanxin-hui">{hui}</span>
      <span className="vbanxin-folio">{folio}</span>
      <span className="vfish vfish-up" />
    </div>
  );
}

export function VerticalReader({
  chapter,
  bookTitle,
  legend,
}: {
  chapter: ChapterData;
  bookTitle: string;
  legend?: LegendEntry[];
}) {
  const leaves = useMemo(() => paginate(layoutColumns(chapter.blocks)), [chapter.blocks]);
  const sheets: Leaf[][] = [];
  for (let i = 0; i < leaves.length; i += 2) sheets.push(leaves.slice(i, i + 2));

  return (
    <div className="vreader" lang="zh-Hant">
      {legend && legend.length > 0 && (
        <ul className="vlegend" aria-label="批語顏色">
          {legend.map((entry) => (
            <li key={entry.color}>
              <span
                className="vlegend-swatch"
                style={{ background: inkColor(entry.color) ?? "#1d1b17" }}
              />
              {entry.label}
            </li>
          ))}
        </ul>
      )}
      <div className="vsheets">
        {sheets.map((pair, i) => (
          <section key={i} className="vsheet" aria-label={`第${i + 1}葉`}>
            <LeafView leaf={pair[0]} />
            <Banxin title={bookTitle} hui={chapter.number} folio={i + 1} />
            {pair[1] ? <LeafView leaf={pair[1]} /> : <div className="vleaf vleaf-empty" />}
          </section>
        ))}
      </div>
    </div>
  );
}
