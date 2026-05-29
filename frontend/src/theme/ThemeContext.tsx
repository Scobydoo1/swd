import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

interface ThemeCtx {
  dark: boolean;
  toggle: () => void;
}

const Ctx = createContext<ThemeCtx>(null!);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem("maple-theme") === "dark";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    try {
      localStorage.setItem("maple-theme", dark ? "dark" : "light");
    } catch {
      /* ignore */
    }
  }, [dark]);

  const value = useMemo(
    () => ({ dark, toggle: () => setDark((d) => !d) }),
    [dark]
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);
