import { Moon, Sun, Menu, X } from "lucide-react";
import { Button } from "./ui/button";
import { useTheme } from "@/hooks/use-theme";
import { useState } from "react";

export default function Header() {
  const { theme, setTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="relative flex items-stretch w-full shadow-sm">
      <div className="flex items-center justify-between w-full px-4">
        <a
          href="/"
          className="flex items-center py-2 hover:bg-muted rounded-full pr-4"
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

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-stretch flex-grow">
          <div className="flex items-center gap-6 ml-8">
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
          </div>
        </nav>

        {/* Desktop Theme Toggle */}
        <div className="hidden md:flex items-center gap-2">
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

        {/* Mobile Menu Button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <Menu className="h-6 w-6" />
          )}
        </Button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="absolute top-full left-0 right-0 bg-background border-b shadow-lg md:hidden">
          <nav className="flex flex-col p-4">
            <a
              href="#features"
              className="py-3 text-sm font-medium hover:text-primary transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              Features
            </a>
            <a
              href="#roadmap"
              className="py-3 text-sm font-medium hover:text-primary transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              Roadmap
            </a>
            <div className="pt-3 mt-3 border-t">
              <Button
                variant="ghost"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="w-full justify-start"
              >
                {theme === "dark" ? (
                  <>
                    <Sun className="h-4 w-4 mr-2" />
                    Light Mode
                  </>
                ) : (
                  <>
                    <Moon className="h-4 w-4 mr-2" />
                    Dark Mode
                  </>
                )}
              </Button>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
