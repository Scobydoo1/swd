// Render công thức toán bằng KaTeX. Hỗ trợ inline ($...$ hoặc \(...\))
// và block ($$...$$). Dùng trong chat (Markdown) và đề quiz.
import katex from "katex";
import type { ReactNode } from "react";

function render(tex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      output: "html",
    });
  } catch {
    return tex;
  }
}

export function MathInline({ tex }: { tex: string }) {
  return (
    <span
      className="katex-inline"
      dangerouslySetInnerHTML={{ __html: render(tex, false) }}
    />
  );
}

export function MathBlock({ tex }: { tex: string }) {
  return (
    <div
      className="katex-block my-2 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: render(tex, true) }}
    />
  );
}

// Tách inline math khỏi đoạn text thường. Trả về mảng ReactNode đan xen
// text và <MathInline>. Hỗ trợ $...$ và \(...\).
const INLINE_RE = /\$([^$\n]+?)\$|\\\(([^]+?)\\\)/g;

export function splitInlineMath(
  text: string,
  keyPrefix: string | number,
  renderText: (chunk: string, key: string) => ReactNode
): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  INLINE_RE.lastIndex = 0;
  while ((m = INLINE_RE.exec(text))) {
    if (m.index > last)
      out.push(renderText(text.slice(last, m.index), `${keyPrefix}-t${i}`));
    const tex = (m[1] ?? m[2] ?? "").trim();
    out.push(<MathInline key={`${keyPrefix}-m${i}`} tex={tex} />);
    last = m.index + m[0].length;
    i++;
  }
  if (last < text.length)
    out.push(renderText(text.slice(last), `${keyPrefix}-t${i}`));
  return out;
}

// Văn bản thường có thể chứa inline math ($...$) — dùng cho đề/đáp án quiz.
export function MathText({ children }: { children: string }) {
  return <>{splitInlineMath(children, "mt", (chunk) => chunk)}</>;
}
