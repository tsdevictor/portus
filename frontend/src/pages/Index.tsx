import { Nav } from "@/components/site/Nav";
import { HeroTile } from "@/components/site/HeroTile";
import { Tile } from "@/components/site/Tile";
import { Carousel } from "@/components/site/Carousel";
import { Footer } from "@/components/site/Footer";

const Index = () => {
  return (
    <main className="bg-[#080808]">
      <Nav />
      <HeroTile />

      <Tile
        eyebrow="Detect"
        headline="Every OpenAI. Every Anthropic. Found."
        subhead="Static analysis spots SDK calls, raw HTTP, and embedded prompts across your repo."
        primaryCta="Run a scan"
        secondaryCta="See sample report"
        theme="dark"
        align="center"
      />

      <Tile
        eyebrow="Powered by Mistral 7B"
        headline="Local. Private. Fast."
        subhead="Code never leaves your machine. The 7B model runs the analysis in seconds."
        primaryCta="Learn more"
        secondaryCta="Read the paper"
        theme="light"
        align="center"
      />

      <Carousel />

      <section className="grid w-full grid-cols-1 md:grid-cols-2">
        <div className="bg-[#111111] text-white min-h-[440px] flex flex-col items-center justify-center text-center px-8 py-20">
          <h3 className="display-headline text-[40px] md:text-[56px] max-w-[14ch]">For engineers.</h3>
          <p className="subhead mt-3 text-base md:text-lg max-w-[32ch] text-white/65">
            CLI, IDE plugin, GitHub Action. Plug it where the code lives.
          </p>
          <div className="mt-6 flex gap-3">
            <button className="pill-solid-invert">Install CLI</button>
            <button className="pill-ghost-invert">Docs ›</button>
          </div>
        </div>
        <div className="bg-white text-foreground min-h-[440px] flex flex-col items-center justify-center text-center px-8 py-20 border-l border-black/[0.06]">
          <h3 className="display-headline text-[40px] md:text-[56px] max-w-[14ch]">For platform teams.</h3>
          <p className="subhead mt-3 text-base md:text-lg max-w-[32ch] opacity-60">
            Org-wide visibility on third-party LLM spend and exposure.
          </p>
          <div className="mt-6 flex gap-3">
            <button className="pill-solid">Talk to sales</button>
            <button className="pill-ghost">Pricing ›</button>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
};

export default Index;
