import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";

interface Suggestion {
  id: string;
  task: string;
  downloads: number;
  likes: number;
  description: string;
  source: string;
}

interface Analysis {
  task_description: string;
  hf_pipeline_tag: string;
  confidence: "high" | "medium" | "low";
}

interface Detection {
  file: string;
  line_number: number;
  provider: string;
  method: string;
  detection_type: string;
  context_snippet: string;
  analysis: Analysis | null;
  suggestions: Suggestion[];
}

interface ScanResult {
  total_detections: number;
  files_scanned: number;
  backend_used: string;
  detections: Detection[];
}

const PROVIDER_COLORS: Record<string, string> = {
  "OpenAI":               "bg-[#10a37f]/15 text-[#0d8a6d]",
  "Anthropic":            "bg-[#c96442]/15 text-[#a84f34]",
  "Cohere":               "bg-[#6c47ff]/15 text-[#5535d4]",
  "Google GenAI":         "bg-[#4285f4]/15 text-[#2b6cd4]",
  "Mistral (commercial)": "bg-[#f97316]/15 text-[#c45c0a]",
  "Azure OpenAI":         "bg-[#0078d4]/15 text-[#005ea3]",
  "AWS Bedrock":          "bg-[#ff9900]/15 text-[#b36b00]",
};

const CONFIDENCE_STYLES: Record<string, string> = {
  high:   "text-emerald-700 bg-emerald-50",
  medium: "text-amber-700 bg-amber-50",
  low:    "text-rose-700 bg-rose-50",
};

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

function DetectionCard({ det, index }: { det: Detection; index: number }) {
  const [open, setOpen] = useState(index < 3);
  const provColor = PROVIDER_COLORS[det.provider] ?? "bg-muted text-muted-foreground";

  return (
    <div className="rounded-2xl border border-border bg-background overflow-hidden">
      {/* Header — always visible */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-muted/40 transition-colors"
      >
        <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${provColor}`}>
          {det.provider}
        </span>
        <span className="flex-1 min-w-0">
          <span className="font-medium text-sm">{det.method}</span>
          <span className="ml-2 text-xs text-muted-foreground truncate">
            {det.file}:{det.line_number}
          </span>
        </span>
        {det.analysis && (
          <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${CONFIDENCE_STYLES[det.analysis.confidence]}`}>
            {det.analysis.confidence}
          </span>
        )}
        {open ? <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />}
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-5 border-t border-border">
          {/* Code context */}
          <div>
            <p className="mt-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
              Code context
            </p>
            <pre className="text-xs bg-muted/60 rounded-xl p-4 overflow-x-auto leading-relaxed font-mono whitespace-pre">
              {det.context_snippet}
            </pre>
          </div>

          {/* Mistral analysis */}
          {det.analysis && (
            <div className="rounded-xl bg-muted/40 px-4 py-3 space-y-1">
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                Mistral Analysis
              </p>
              <p className="text-sm">{det.analysis.task_description}</p>
              <p className="text-xs text-muted-foreground">
                HF task: <span className="font-mono">{det.analysis.hf_pipeline_tag}</span>
              </p>
            </div>
          )}

          {/* HF suggestions */}
          {det.suggestions.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">
                Suggested HuggingFace Replacements
                {det.suggestions[0]?.source === "local_cache" && (
                  <span className="ml-1 normal-case font-normal">(offline cache)</span>
                )}
              </p>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {det.suggestions.map((s) => (
                  <a
                    key={s.id}
                    href={`https://huggingface.co/${s.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex flex-col gap-1 rounded-xl border border-border bg-background p-3 hover:border-foreground/30 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-1">
                      <span className="text-xs font-semibold font-mono leading-tight break-all">
                        {s.id}
                      </span>
                      <ExternalLink className="shrink-0 h-3 w-3 text-muted-foreground group-hover:text-foreground transition-colors mt-0.5" />
                    </div>
                    <div className="flex gap-2 text-xs text-muted-foreground">
                      <span>{fmt(s.downloads)} dl</span>
                      <span>·</span>
                      <span>{s.likes} ♥</span>
                    </div>
                    {s.description && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                        {s.description}
                      </p>
                    )}
                  </a>
                ))}
              </div>
            </div>
          )}

          {!det.analysis && !det.suggestions.length && (
            <p className="text-xs text-muted-foreground italic">
              No Mistral analysis — start the backend with a valid HF token or ollama to get suggestions.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

const Results = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const results: ScanResult | undefined = state?.results;

  if (!results) {
    return (
      <main className="bg-background min-h-screen">
        <Nav />
        <div className="flex flex-col items-center justify-center py-40 gap-4">
          <p className="text-muted-foreground">No scan results found.</p>
          <button onClick={() => navigate("/")} className="pill-solid">
            ← Back to scan
          </button>
        </div>
        <Footer />
      </main>
    );
  }

  // Group by file
  const byFile: Record<string, Detection[]> = {};
  for (const d of results.detections) {
    (byFile[d.file] ??= []).push(d);
  }

  const providerCounts: Record<string, number> = {};
  for (const d of results.detections) {
    providerCounts[d.provider] = (providerCounts[d.provider] ?? 0) + 1;
  }

  return (
    <main className="bg-background min-h-screen">
      <Nav />

      <div className="mx-auto max-w-[960px] px-6 pt-28 pb-24">
        {/* Back */}
        <button
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8"
        >
          <ArrowLeft className="h-4 w-4" /> Back to scan
        </button>

        {/* Summary header */}
        <div className="mb-10">
          <h1 className="display-headline text-[40px] md:text-[56px]">Scan Results</h1>
          <div className="mt-4 flex flex-wrap gap-3 text-sm text-muted-foreground">
            <span className="rounded-full bg-muted px-3 py-1">
              {results.total_detections} detection{results.total_detections !== 1 ? "s" : ""}
            </span>
            <span className="rounded-full bg-muted px-3 py-1">
              {results.files_scanned} file{results.files_scanned !== 1 ? "s" : ""} scanned
            </span>
            <span className="rounded-full bg-muted px-3 py-1 font-mono">
              backend: {results.backend_used}
            </span>
          </div>

          {/* Provider breakdown */}
          {Object.keys(providerCounts).length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(providerCounts).map(([prov, count]) => (
                <span
                  key={prov}
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${PROVIDER_COLORS[prov] ?? "bg-muted text-muted-foreground"}`}
                >
                  {prov} · {count}
                </span>
              ))}
            </div>
          )}
        </div>

        {results.total_detections === 0 ? (
          <div className="rounded-2xl border border-border bg-muted/30 px-8 py-16 text-center">
            <p className="text-lg font-medium">No commercial AI API calls detected.</p>
            <p className="mt-2 text-sm text-muted-foreground">
              The scanned files don't appear to use OpenAI, Anthropic, Cohere, or other supported providers.
            </p>
          </div>
        ) : (
          Object.entries(byFile).map(([file, detections]) => (
            <section key={file} className="mb-10">
              <h2 className="text-sm font-mono font-semibold text-muted-foreground mb-3 flex items-center gap-2">
                <span className="opacity-40">//</span> {file}
                <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-sans font-normal">
                  {detections.length}
                </span>
              </h2>
              <div className="space-y-3">
                {detections.map((det, i) => (
                  <DetectionCard key={`${det.file}-${det.line_number}-${i}`} det={det} index={i} />
                ))}
              </div>
            </section>
          ))
        )}
      </div>

      <Footer />
    </main>
  );
};

export default Results;
