import { ReactNode } from "react";

interface TileProps {
  eyebrow?: string;
  headline: string;
  subhead: string;
  primaryCta: string;
  secondaryCta: string;
  image?: string;
  imageAlt?: string;
  theme?: "light" | "dark";
  align?: "left" | "center";
  height?: "tall" | "med" | "short";
  contentPosition?: "top" | "bottom";
  children?: ReactNode;
}

export const Tile = ({
  eyebrow,
  headline,
  subhead,
  primaryCta,
  secondaryCta,
  theme = "light",
  align = "center",
  height = "tall",
  contentPosition = "top",
  children,
}: TileProps) => {
  const isDark = theme === "dark";
  const heightCls =
    height === "tall"
      ? "min-h-[520px] md:min-h-[580px]"
      : height === "med"
      ? "min-h-[420px]"
      : "min-h-[360px]";

  return (
    <section
      className={`relative w-full overflow-hidden ${heightCls} ${
        isDark ? "bg-[#111111] text-white" : "bg-white text-foreground border-b border-black/[0.06]"
      }`}
    >
      {isDark && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 65% 75% at 50% 0%, rgba(99,102,241,0.08), transparent)",
          }}
        />
      )}

      <div
        className={`relative z-10 mx-auto flex h-full max-w-[1200px] flex-col px-6 ${
          contentPosition === "top" ? "pt-16 md:pt-20" : "pt-12"
        } ${align === "center" ? "items-center text-center" : "items-start text-left"} ${
          contentPosition === "bottom" ? "justify-end pb-16" : ""
        }`}
        style={{ minHeight: "inherit" }}
      >
        {eyebrow && (
          <p
            className={`subhead text-xs uppercase tracking-[0.2em] mb-4 ${
              isDark ? "text-white/40" : "opacity-50"
            }`}
          >
            {eyebrow}
          </p>
        )}
        <h2 className="display-headline text-[44px] md:text-[68px] lg:text-[80px] max-w-[12ch]">
          {headline}
        </h2>
        <p
          className={`subhead mt-4 text-lg md:text-xl max-w-[32ch] ${
            isDark ? "text-white/65" : "opacity-75"
          }`}
        >
          {subhead}
        </p>

        <div className={`mt-6 flex flex-wrap gap-3 ${align === "center" ? "justify-center" : ""}`}>
          <button className={isDark ? "pill-solid-invert" : "pill-solid"}>{primaryCta}</button>
          <button className={isDark ? "pill-ghost-invert" : "pill-ghost"}>{secondaryCta} ›</button>
        </div>

        {children}
      </div>
    </section>
  );
};
