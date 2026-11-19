# 🎬 Animated Visuals

HTML/CSS pages that animate every illustration in the guides (and `practicals/README.md`), with CSS `@keyframes`. Open [`index.html`](index.html) in a browser.

- **Mermaid** diagrams: boxes light up as the flow reaches them, arrows draw in the order the Markdown defines them, and glowing packets travel along the edges. Sequence diagrams play message by message.
- **ASCII** diagrams: revealed line by line, with pulsing arrows and ✅ / ❌ marks that pop in.
- Every figure sits next to the chapter's own text and a **Step by step** list that lights up in sync. Each figure has **Replay**, **Pause** and **speed** controls.

The pages are generated. Don't edit the HTML by hand; change the Markdown and rebuild.

## 🔁 Rebuild

```bash
cd visuals/build
npm install            # pinned @mermaid-js/mermaid-cli 11.4.2; uses the system Chromium (puppeteer.json)
python3 build.py       # needs the Python `markdown` package
```

Rendered SVGs are cached in `build/.cache/` by diagram hash, so only changed diagrams are re-rendered.
