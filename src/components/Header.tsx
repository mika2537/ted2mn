import { Button } from "@/components/ui/button";
import { Sparkles, Globe } from "lucide-react";
import { useTranslation } from "@/components/hooks/useTranslation";

const Header = () => {
  const { t, currentLanguage, setLanguage, languages } = useTranslation();

  return (
    <header className="bg-background border-b border-border px-8 sm:px-12 lg:px-16 py-6">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        {/* Logo */}
        <div className="flex items-center gap-4 sm:gap-6">
          <div className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-7 h-7 sm:w-8 sm:h-8 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-foreground whitespace-nowrap">
            Ted2mn
          </h1>
        </div>

        {/* Navigation - Hidden on mobile */}
        <nav className="hidden md:flex items-center gap-8 lg:gap-12">
          <a
            href="#"
            className="text-lg font-medium text-foreground hover:text-primary transition-colors duration-200 whitespace-nowrap"
          >
            {t("nav.home")}
          </a>
        </nav>

        {/* Right side actions */}
        <div className="flex items-center gap-4 sm:gap-6 lg:gap-8">
          {/* Language Selector */}
          <div className="relative">
            <select
              value={currentLanguage}
              onChange={(e) => setLanguage(e.target.value)}
              className="text-base sm:text-lg bg-background border border-border rounded-lg px-4 py-3 sm:px-5 sm:py-4 text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent appearance-none pr-12 min-w-0"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4">
              <svg className="w-5 h-5 text-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* New Video Button */}
          <Button 
            variant="default" 
            size="lg"
            className="text-base sm:text-lg px-6 py-3 sm:px-8 sm:py-4 h-12 sm:h-14 whitespace-nowrap font-semibold"
          >
            {t("header.newVideo")}
          </Button>

          {/* User Avatar */}
          <div className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
            <Globe className="w-6 h-6 sm:w-7 sm:h-7 text-white" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;