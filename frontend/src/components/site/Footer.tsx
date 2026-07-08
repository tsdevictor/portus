const cols = [
  {
    title: "Product",
    links: ["Scan", "Models", "Migrate", "CLI", "API", "Changelog"],
  },
  {
    title: "Providers",
    links: ["OpenAI", "Anthropic", "Cohere", "Google", "Mistral", "All"],
  },
  {
    title: "Open models",
    links: ["Llama 3", "Mistral 7B", "Phi-3", "Qwen", "Gemma", "Browse all"],
  },
  {
    title: "Resources",
    links: ["Docs", "Migration guide", "Cost calculator", "Benchmarks", "Blog", "Status"],
  },
  {
    title: "Company",
    links: ["About", "Careers", "Press", "Contact", "Partners", "Security"],
  },
];

export const Footer = () => {
  return (
    <footer className="bg-[hsl(var(--surface-light))] text-foreground">
      <div className="mx-auto max-w-[1024px] border-t border-border px-5 py-12">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10">
          {cols.map((c) => (
            <div key={c.title}>
              <h4 className="text-[12px] font-semibold mb-3">{c.title}</h4>
              <ul className="space-y-2">
                {c.links.map((l) => (
                  <li key={l}>
                    <a href="#" className="text-[12px] text-muted-foreground hover:text-foreground transition">
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex max-w-[1024px] flex-col md:flex-row items-center justify-between gap-2 px-5 py-4 text-[11px] text-muted-foreground">
          <p>© {new Date().getFullYear()} Portus Labs. All rights reserved.</p>
          <div className="flex gap-5">
            <a href="#" className="hover:text-foreground">Privacy</a>
            <a href="#" className="hover:text-foreground">Terms</a>
            <a href="#" className="hover:text-foreground">Cookies</a>
            <a href="#" className="hover:text-foreground">Legal</a>
          </div>
        </div>
      </div>
    </footer>
  );
};
