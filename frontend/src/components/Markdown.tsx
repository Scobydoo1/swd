// Lightweight markdown → React renderer for chat messages, Maple-styled.
// Supports: code fences, inline code, bold, italic, headings, ul/ol,
// blockquote, links, hr, paragraphs. Plus a CodeBlock with copy button.
import { useState, type ReactNode } from "react";
import { IconCheck, IconCopy } from "./Icons";

function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(code).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };
  return (
    <div className="md-code">
      <div className="md-code-bar">
        <span className="md-code-lang">{lang || "code"}</span>
        <button className="md-code-copy" onClick={copy}>
          {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
          {copied ? "Đã chép" : "Sao chép"}
        </button>
      </div>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}

// inline formatting: `code`, **bold**, *italic*, [text](url)
function renderInline(text: string, keyPrefix: string | number): ReactNode[] {
  const tokens: ReactNode[] = [];
  let rest = text;
  let i = 0;
  const re = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(\[[^\]]+\]\([^)]+\))/;
  while (rest.length) {
    const m = rest.match(re);
    if (!m || m.index === undefined) {
      tokens.push(rest);
      break;
    }
    if (m.index > 0) tokens.push(rest.slice(0, m.index));
    const tok = m[0];
    const k = `${keyPrefix}-${i++}`;
    if (tok.startsWith("`"))
      tokens.push(
        <code key={k} className="md-inline-code">
          {tok.slice(1, -1)}
        </code>
      );
    else if (tok.startsWith("**"))
      tokens.push(<strong key={k}>{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("*"))
      tokens.push(<em key={k}>{tok.slice(1, -1)}</em>);
    else if (tok.startsWith("[")) {
      const lm = tok.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (lm)
        tokens.push(
          <a key={k} href={lm[2]} target="_blank" rel="noreferrer">
            {lm[1]}
          </a>
        );
    }
    rest = rest.slice(m.index + tok.length);
  }
  return tokens;
}

export function Markdown({ src }: { src: string }) {
  const lines = src.replace(/\r/g, "").split("\n");
  const out: ReactNode[] = [];
  let i = 0;
  let key = 0;
  while (i < lines.length) {
    const line = lines[i];
    // code fence
    if (/^```/.test(line)) {
      const lang = line.slice(3).trim();
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) {
        buf.push(lines[i]);
        i++;
      }
      i++; // closing fence
      out.push(<CodeBlock key={key++} code={buf.join("\n")} lang={lang} />);
      continue;
    }
    // heading
    const h = line.match(/^(#{1,4})\s+(.*)/);
    if (h) {
      const lvl = h[1].length;
      const Tag = `h${Math.min(lvl + 1, 5)}` as "h2" | "h3" | "h4" | "h5";
      out.push(
        <Tag key={key} className="md-h">
          {renderInline(h[2], key++)}
        </Tag>
      );
      i++;
      continue;
    }
    // hr
    if (/^(---|\*\*\*|___)\s*$/.test(line)) {
      out.push(<hr key={key++} className="md-hr" />);
      i++;
      continue;
    }
    // blockquote
    if (/^>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        buf.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      out.push(
        <blockquote key={key} className="md-quote">
          {renderInline(buf.join(" "), key++)}
        </blockquote>
      );
      continue;
    }
    // unordered list
    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i++;
      }
      const lk = key++;
      out.push(
        <ul key={lk} className="md-ul">
          {items.map((it, n) => (
            <li key={n}>{renderInline(it, `${lk}-${n}`)}</li>
          ))}
        </ul>
      );
      continue;
    }
    // ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      const lk = key++;
      out.push(
        <ol key={lk} className="md-ol">
          {items.map((it, n) => (
            <li key={n}>{renderInline(it, `${lk}-${n}`)}</li>
          ))}
        </ol>
      );
      continue;
    }
    // blank
    if (/^\s*$/.test(line)) {
      i++;
      continue;
    }
    // paragraph (gather consecutive non-special lines)
    const buf = [line];
    i++;
    while (
      i < lines.length &&
      !/^\s*$/.test(lines[i]) &&
      !/^```/.test(lines[i]) &&
      !/^(#{1,4})\s/.test(lines[i]) &&
      !/^\s*[-*]\s/.test(lines[i]) &&
      !/^\s*\d+\.\s/.test(lines[i]) &&
      !/^>\s?/.test(lines[i])
    ) {
      buf.push(lines[i]);
      i++;
    }
    out.push(
      <p key={key} className="md-p">
        {renderInline(buf.join(" "), key++)}
      </p>
    );
  }
  return <>{out}</>;
}
