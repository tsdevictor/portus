import { useRef, useState } from "react";
import { FolderOpen, FileCode2, Upload, Loader2, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

type ScanState = "idle" | "scanning" | "error";

export const HeroTile = () => {
  const dirRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [files, setFiles] = useState<FileList | null>(null);
  const [scanState, setScanState] = useState<ScanState>("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const navigate = useNavigate();

  const onDir = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files;
    if (f && f.length) {
      setPicked(`${f.length} file${f.length > 1 ? "s" : ""} selected`);
      setFiles(f);
      setScanState("idle");
    }
  };

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files;
    if (f && f[0]) {
      setPicked(f[0].name);
      setFiles(f);
      setScanState("idle");
    }
  };

  const handleScan = async () => {
    if (!files || files.length === 0) return;
    setScanState("scanning");
    setErrorMsg("");

    const form = new FormData();
    const paths: string[] = [];
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      form.append("files", f, f.name);
      paths.push((f as File & { webkitRelativePath: string }).webkitRelativePath || f.name);
    }
    paths.forEach((p) => form.append("paths", p));
    form.append("backend", "ollama");

    try {
      const res = await fetch("/api/scan", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Scan failed");
      }
      const data = await res.json();
      navigate("/results", { state: { results: data } });
    } catch (e: unknown) {
      setScanState("error");
      setErrorMsg(e instanceof Error ? e.message : "Unknown error");
    }
  };

  return (
    <section className="relative w-full overflow-hidden min-h-[760px] md:min-h-[860px] bg-[#080808]">
      {/* Subtle grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.04) 1px,transparent 1px)",
          backgroundSize: "72px 72px",
        }}
      />
      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 55% at 50% 30%, rgba(99,102,241,0.13), transparent)",
        }}
      />

      <div
        className="relative z-10 mx-auto flex h-full max-w-[1200px] flex-col items-center px-6 pt-24 md:pt-28 text-center"
        style={{ minHeight: "inherit" }}
      >
        <p className="subhead text-xs uppercase tracking-[0.2em] mb-5 text-white/40">
          Portus · LLM Migration Assistant
        </p>
        <h1 className="display-headline text-[52px] md:text-[88px] lg:text-[112px] max-w-[14ch] animate-fade-up text-white">
          Find every closed-source call.
        </h1>
        <p className="subhead mt-5 text-lg md:text-2xl max-w-[36ch] text-white/65">
          Drop a folder or a script. We scan with Mistral 7B and recommend an open Hugging Face model for each call.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={() => dirRef.current?.click()}
            className="pill-solid-invert"
            disabled={scanState === "scanning"}
          >
            <FolderOpen className="!h-4 !w-4" /> Choose folder
          </button>
          <button
            onClick={() => fileRef.current?.click()}
            className="pill-ghost-invert"
            disabled={scanState === "scanning"}
          >
            <FileCode2 className="!h-4 !w-4" /> Upload script ›
          </button>
        </div>

        {picked && scanState !== "scanning" && (
          <div className="mt-6 flex flex-col items-center gap-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.07] backdrop-blur px-4 py-1.5 text-sm text-white/80">
              <Upload className="h-3.5 w-3.5" /> {picked}
            </div>
            <button onClick={handleScan} className="pill-solid-invert text-base px-6 py-2">
              Scan now →
            </button>
          </div>
        )}

        {scanState === "scanning" && (
          <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.07] backdrop-blur px-5 py-2 text-sm text-white/80">
            <Loader2 className="h-4 w-4 animate-spin" />
            Scanning with Mistral 7B…
          </div>
        )}

        {scanState === "error" && (
          <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-4 py-1.5 text-sm text-red-400">
            <AlertCircle className="h-3.5 w-3.5" />
            {errorMsg || "Scan failed — is the backend running?"}
          </div>
        )}

        <input
          ref={dirRef}
          type="file"
          // @ts-expect-error - non-standard but widely supported
          webkitdirectory=""
          directory=""
          multiple
          className="hidden"
          onChange={onDir}
        />
        <input
          ref={fileRef}
          type="file"
          accept=".py,.js,.ts,.tsx,.jsx,.rb,.go,.java,.txt,.md"
          className="hidden"
          onChange={onFile}
        />
      </div>
    </section>
  );
};
