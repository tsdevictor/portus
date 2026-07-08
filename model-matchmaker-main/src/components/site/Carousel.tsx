import { useEffect, useState } from "react";
import { Pause, Play } from "lucide-react";

const slides = [
  {
    accent: "rgba(99,102,241,0.15)",
    eyebrow: "Catalog",
    title: "12,000+ Hugging Face models, ranked.",
    sub: "We match each API call to the smallest model that does the job.",
  },
  {
    accent: "rgba(34,197,94,0.12)",
    eyebrow: "Workflow",
    title: "From scan to PR in minutes.",
    sub: "Auto-generate diff suggestions for every detected call site.",
  },
  {
    accent: "rgba(236,72,153,0.11)",
    eyebrow: "Independence",
    title: "Cut the cord from closed APIs.",
    sub: "Bring inference in-house. Own your stack, end to end.",
  },
];

export const Carousel = () => {
  const [i, setI] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => setI((p) => (p + 1) % slides.length), 4000);
    return () => clearInterval(t);
  }, [playing]);

  const s = slides[i];

  return (
    <section className="w-full bg-[#0a0a0a]">
      <div className="relative w-full h-[480px] md:h-[560px] overflow-hidden">
        {/* Per-slide radial accent */}
        {slides.map((slide, idx) => (
          <div
            key={idx}
            className={`absolute inset-0 transition-opacity duration-700 ${idx === i ? "opacity-100" : "opacity-0"}`}
            style={{
              background: `radial-gradient(ellipse 70% 70% at 25% 55%, ${slide.accent}, transparent)`,
            }}
          />
        ))}

        <div className="relative z-10 mx-auto flex h-full max-w-[1200px] flex-col justify-end px-6 pb-16 text-white">
          <p className="subhead text-xs uppercase tracking-[0.2em] mb-3 text-white/40">{s.eyebrow}</p>
          <h3 className="display-headline text-[36px] md:text-[60px] max-w-[16ch]">{s.title}</h3>
          <p className="subhead mt-3 text-base md:text-lg text-white/65 max-w-[40ch]">{s.sub}</p>
          <div className="mt-6 flex gap-3">
            <button className="pill-solid-invert">Explore models</button>
            <button className="pill-ghost-invert">Read brief ›</button>
          </div>
        </div>
      </div>

      <div className="mx-auto flex max-w-[1200px] items-center justify-center gap-3 py-5">
        {slides.map((_, idx) => (
          <button
            key={idx}
            aria-label={`Slide ${idx + 1}`}
            onClick={() => setI(idx)}
            className={`h-1.5 rounded-full transition-all ${
              idx === i ? "w-8 bg-white" : "w-1.5 bg-white/25"
            }`}
          />
        ))}
        <button
          aria-label={playing ? "Pause" : "Play"}
          onClick={() => setPlaying((p) => !p)}
          className="ml-3 grid h-6 w-6 place-items-center rounded-full border border-white/25 hover:border-white/60 transition text-white/60 hover:text-white"
        >
          {playing ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
        </button>
      </div>
    </section>
  );
};
