import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { translations, type Lang } from "./translations";

type TParams = Record<string, string | number>;

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, params?: TParams) => string;
}

const Ctx = createContext<LangCtx>(null!);

function detectInitial(): Lang {
  try {
    const saved = localStorage.getItem("maple-lang");
    if (saved === "vi" || saved === "en") return saved;
  } catch {
    /* ignore */
  }
  return "vi"; // dự án mặc định tiếng Việt
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>(detectInitial);

  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem("maple-lang", lang);
    } catch {
      /* ignore */
    }
  }, [lang]);

  const t = useCallback(
    (key: string, params?: TParams) => {
      const table = translations[lang] ?? translations.vi;
      let str = table[key] ?? translations.vi[key] ?? key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          str = str.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
        }
      }
      return str;
    },
    [lang]
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, t]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useLang = () => useContext(Ctx);
