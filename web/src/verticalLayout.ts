import type { ContentBlock, VerticalSegment } from "./types";

export const ROWS = 20;
export const COLUMNS_PER_LEAF = 10;
export const BAND_ROWS = 5;
export const COLUMN_WIDTH = 1.55;
export const GUTTER = 0.55;
const SMALL_PER_ROW = 4;
const SIDE_FONT = 0.42;
const HEAD_FONT = 0.4;
const HEAD_LINE = 0.48;
const HEAD_GAP = 0.25;

export type ColumnRole = "juan" | "hui" | "title" | "variant" | "body" | "verse" | "note" | "blank";

export type Cell =
  | { kind: "char"; row: number; ch: string; color?: string }
  | { kind: "jp"; row: number; rows: number; right: string; left: string; color?: string };

export interface SideNote {
  row: number;
  text: string;
  color?: string;
  marker: boolean;
  font: number;
}

export interface HeadNote {
  text: string;
  color?: string;
  labels: string;
  right: number;
  width: number;
}

export interface Column {
  role: ColumnRole;
  cells: Cell[];
  side: SideNote[];
  head: { text: string; color?: string; labels: string }[];
}

export interface Leaf {
  columns: Column[];
  head: HeadNote[];
}

function newColumn(role: ColumnRole): Column {
  return { role, cells: [], side: [], head: [] };
}

function placeSide(row: number, text: string): { row: number; font: number } {
  const fitsBelow = (ROWS - row) / SIDE_FONT;
  if (text.length <= fitsBelow) return { row, font: SIDE_FONT };
  const fitsColumn = ROWS / SIDE_FONT;
  if (text.length <= fitsColumn) {
    return { row: Math.max(0, ROWS - Math.ceil(text.length * SIDE_FONT)), font: SIDE_FONT };
  }
  const lines = Math.ceil((text.length * SIDE_FONT) / ROWS);
  return { row: 0, font: Math.max(0.2, Math.min(SIDE_FONT, GUTTER / lines - 0.02)) };
}

function layoutParagraph(block: ContentBlock, out: Column[]): void {
  const role: ColumnRole =
    block.role === "verse" ? "verse" : block.role === "note" ? "note" : "body";
  const firstIndent = block.indent ?? 0;
  const contIndent = role === "verse" ? 2 : role === "note" ? 2 : 0;
  let col = newColumn(role);
  out.push(col);
  let row = firstIndent;
  const breakColumn = () => {
    col = newColumn(role);
    out.push(col);
    row = contIndent;
  };
  for (const seg of block.segments ?? []) {
    if (seg.k === "t") {
      for (const ch of seg.s) {
        if (row >= ROWS) breakColumn();
        if (ch === "　" && row === contIndent && col.cells.length === 0 && role !== "verse")
          continue;
        col.cells.push({ kind: "char", row, ch, color: seg.c });
        row += 1;
      }
    } else if (seg.k === "j") {
      let rest = Array.from(seg.s);
      while (rest.length > 0) {
        if (row >= ROWS) breakColumn();
        const take = Math.min(rest.length, (ROWS - row) * SMALL_PER_ROW);
        const chunk = rest.slice(0, take);
        rest = rest.slice(take);
        const half = Math.ceil(chunk.length / 2);
        const rows = Math.ceil(half / 2);
        col.cells.push({
          kind: "jp",
          row,
          rows,
          right: chunk.slice(0, half).join(""),
          left: chunk.slice(half).join(""),
          color: seg.c,
        });
        row += rows;
      }
    } else if (seg.k === "c") {
      if (row >= ROWS) breakColumn();
      const placed = placeSide(row, seg.s);
      col.side.push({
        row: placed.row,
        text: seg.s,
        color: seg.c,
        marker: false,
        font: placed.font,
      });
    } else {
      if (row >= ROWS) breakColumn();
      col.head.push({ text: seg.s, color: seg.c, labels: seg.n ?? "" });
      if (seg.n) {
        col.side.push({ row, text: seg.n, color: "00AEEF", marker: true, font: SIDE_FONT });
      }
    }
  }
}

function textColumns(role: ColumnRole, text: string, indent: number, color?: string): Column[] {
  const cols: Column[] = [];
  let col = newColumn(role);
  cols.push(col);
  let row = indent;
  for (const ch of text) {
    if (row >= ROWS) {
      col = newColumn(role);
      cols.push(col);
      row = indent;
    }
    col.cells.push({ kind: "char", row, ch, color });
    row += 1;
  }
  return cols;
}

function layoutTitle(block: ContentBlock, out: Column[]): void {
  const [number, title] = (block.segments ?? []).map((s: VerticalSegment) => s.s);
  if (block.juan) out.push(...textColumns("juan", block.juan, 0, "F26C4B"));
  if (number) out.push(...textColumns("hui", number, 1));
  const fitIndent = (text: string) => Math.max(0, Math.min(3, ROWS - Array.from(text).length));
  if (title) out.push(...textColumns("title", title, fitIndent(title)));
  for (const v of block.variants ?? []) out.push(...textColumns("variant", v, fitIndent(v)));
  out.push(newColumn("blank"));
}

export function layoutColumns(blocks: ContentBlock[]): Column[] {
  const columns: Column[] = [];
  for (const block of blocks) {
    if (block.type !== "vertical") continue;
    if (block.role === "title") layoutTitle(block, columns);
    else layoutParagraph(block, columns);
  }
  return columns;
}

export function paginate(columns: Column[]): Leaf[] {
  const leaves: Leaf[] = [];
  for (let i = 0; i < columns.length; i += COLUMNS_PER_LEAF) {
    const cols = columns.slice(i, i + COLUMNS_PER_LEAF);
    const head: HeadNote[] = [];
    let cursor = 0;
    cols.forEach((col, idx) => {
      for (const note of col.head) {
        const lines = Math.max(1, Math.ceil((note.text.length * HEAD_FONT) / (BAND_ROWS - 0.6)));
        const width = lines * HEAD_LINE;
        const right = Math.max(idx * COLUMN_WIDTH + 0.2, cursor);
        head.push({ ...note, right, width });
        cursor = right + width + HEAD_GAP;
      }
    });
    leaves.push({ columns: cols, head });
  }
  return leaves;
}
