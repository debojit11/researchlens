export interface HealthResponse {
  status: string;
  runtime_ready?: boolean;
}

export interface DocumentationCitation {
  type: "documentation";
  source: string;
  section: string;
  page_start?: number;
  page_end?: number;
}

export interface WebCitation {
  type: "web";
  title: string;
  url: string;
}

export type Citation = DocumentationCitation | WebCitation;

export interface ResearchRequest {
  query: string;
}

export interface ResearchResponse {
  answer: string;
  citations?: Citation[];
  route?: "documentation" | "web" | string;
  rewrite_count?: number;
  generation_attempts?: number;
  faithful?: boolean | null;
  useful?: boolean | null;
}
