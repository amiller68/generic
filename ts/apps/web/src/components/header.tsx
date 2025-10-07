import { Moon, Sun, Menu, X } from "lucide-react";
import { Button } from "./ui/button";
import { useTheme } from "@/hooks/use-theme";
import { useState } from "react";

export default function Header() {
  const { theme, setTheme } = useTheme();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      <header className="flex items-center justify-between w-full shadow-sm px-4 py-2">
        <div className="flex items-center">
          <a
            href="/"
            className="flex items-center px-2 py-1 hover:bg-muted rounded-full"
          >
            <img
              src="/icon.svg"
              alt="Icon"
              width={32}
              height={32}
              className="mr-2"
            />
            <div className="flex flex-col">
              <span className="font-black text-xl leading-none">GenericTS</span>
            </div>
          </a>
        </div>

        <nav className="hidden md:flex items-center gap-6">
          <a
            href="#features"
            className="text-sm font-medium hover:text-primary transition-colors"
          >
            Features
          </a>
          <a
            href="#roadmap"
            className="text-sm font-medium hover:text-primary transition-colors"
          >
            Roadmap
          </a>
        </nav>

        <div className="flex items-center gap-2">
          <div className="hidden md:block">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label="Toggle theme"
              className="relative"
            >
              <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle mobile menu"
          >
            {isMobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>
      </header>

      {isMobileMenuOpen && (
        <div className="md:hidden bg-background border-b">
          <nav className="flex flex-col px-4 py-2">
            <a
              href="#features"
              className="py-2 text-sm font-medium hover:text-primary transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Features
            </a>
            <a
              href="#roadmap"
              className="py-2 text-sm font-medium hover:text-primary transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Roadmap
            </a>
            <button
              className="py-2 text-sm font-medium hover:text-primary transition-colors text-left flex items-center gap-2"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? (
                <>
                  <Sun className="h-4 w-4" />
                  Light Mode
                </>
              ) : (
                <>
                  <Moon className="h-4 w-4" />
                  Dark Mode
                </>
              )}
            </button>
          </nav>
        </div>
      )}
    </>
  );
}
