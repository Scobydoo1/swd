import { useEffect, useRef } from "react";

// Client ID OAuth từ Google Cloud Console; thiếu env -> ẩn nút.
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (res: { credential: string }) => void;
          }) => void;
          renderButton: (el: HTMLElement, options: object) => void;
        };
      };
    };
  }
}

export function GoogleSignInButton({
  onCredential,
}: {
  onCredential: (idToken: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!CLIENT_ID) return;
    const init = () => {
      if (!window.google || !ref.current) return;
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: (res) => onCredential(res.credential),
      });
      window.google.accounts.id.renderButton(ref.current, {
        theme: "outline",
        size: "large",
        width: 300,
      });
    };
    if (window.google) {
      init();
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = init;
    document.head.appendChild(script);
  }, [onCredential]);

  if (!CLIENT_ID) return null;
  return <div ref={ref} className="flex justify-center" />;
}
