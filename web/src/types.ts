export type RenderingMode = "editorial-business" | "math-katex";

export interface DiagramItem {
  tag: string;
  src: string;
  caption: string;
}

export interface ContentBlock {
  type: "paragraph" | "math-paragraph" | "heading" | "figure" | "table" | "theorem";
  html?: string;
  text?: string;
  content?: string;
  level?: number;
  id?: string;
  label?: string;
  caption?: string;
  src?: string;
  headers?: string[];
  rows?: string[][];
  note?: string;
  kind?: string;
  number?: string;
  title?: string;
  tag?: string;
  diagrams?: DiagramItem[];
  page?: number;
}

export interface ChapterData {
  slug: string;
  number: string;
  title: string;
  tag?: string;
  blocks: ContentBlock[];
}

export interface ChapterSummary {
  slug: string;
  number: string;
  title: string;
  tag?: string;
  blockCount: number;
}

export interface BookData {
  slug: string;
  title: string;
  subtitle: string;
  author: string;
  language: string;
  domain: string;
  renderingMode: RenderingMode;
  renderingBadge: string;
  description: string;
  stats: {
    pages: number;
    figures: number;
    tables: number;
    chapters: number;
  };
  deliverables: {
    pdf: string;
    typst: string;
    latex: string;
    epub: string;
  };
  chapters: ChapterData[];
  chapterSummaries?: ChapterSummary[];
}

export interface AnnotationItem {
  _id?: string;
  bookSlug: string;
  chapterSlug: string;
  readerName: string;
  quoteText: string;
  note: string;
  createdAt: number;
}
