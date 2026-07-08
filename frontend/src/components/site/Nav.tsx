import { useState, useEffect } from "react";
import { Search, Menu, X, Sparkles } from "lucide-react";

export const Nav = () => {
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const items = ["Scan", "Models", "Migrate", "Pricing", "Docs", "Support"];

  return (
    <>
      <header
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          scrolled || searchOpen || menuOpen
            ? "bg-[#080808]/90 backdrop-blur-xl border-b border-white/10"
            : "bg-transparent"
        }`}
      >
        <nav className="mx-auto flex h-11 max-w-[1024px] items-center justify-between px-5 text-white">
          <a href="#" aria-label="Home" className="flex items-center gap-1.5">
            <Sparkles className="h-4 w-4" strokeWidth={1.5} />
            <span className="text-[13px] font-semibold tracking-tight">portus</span>
          </a>

          <ul className="hidden md:flex items-center gap-7">
            {items.map((item) => (
              <li key={item}>
                <a
                  href="#"
                  className="text-[12px] font-normal text-white/60 hover:text-white transition-colors"
                >
                  {item}
                </a>
              </li>
            ))}
          </ul>

          <div className="flex items-center gap-4">
            <button
              aria-label="Search"
              onClick={() => setSearchOpen((v) => !v)}
              className="text-white/60 hover:text-white transition-colors"
            >
              <Search className="h-3.5 w-3.5" strokeWidth={1.5} />
            </button>
            <button
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              onClick={() => setMenuOpen((v) => !v)}
              className="md:hidden text-white/60 hover:text-white transition-colors"
            >
              {menuOpen ? <X className="h-4 w-4" strokeWidth={1.5} /> : <Menu className="h-4 w-4" strokeWidth={1.5} />}
            </button>
          </div>
        </nav>

        {/* Search flyout */}
        <div
          className={`overflow-hidden transition-all duration-300 ${
            searchOpen ? "max-h-40" : "max-h-0"
          }`}
        >
          <div className="mx-auto max-w-[1024px] px-5 py-6">
            <div className="flex items-center gap-3 border-b border-white/15 pb-3">
              <Search className="h-5 w-5 text-white/40" strokeWidth={1.5} />
              <input
                autoFocus={searchOpen}
                placeholder="Search models, providers, docs"
                className="w-full bg-transparent text-2xl font-light tracking-tight outline-none placeholder:text-white/30 text-white"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Mobile slide-in */}
      <div
        className={`fixed inset-0 z-40 bg-[#080808] transition-transform duration-300 md:hidden ${
          menuOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <ul className="flex flex-col gap-6 px-6 pt-24">
          {items.map((item) => (
            <li key={item}>
              <a href="#" className="text-3xl font-semibold tracking-tight text-white">
                {item}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
};
