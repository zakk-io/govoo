/** @odoo-module **/

/**
 * Turn a small, whitelisted subset of markdown-ish AI output into a safe,
 * structured representation for the template to render -- never raw HTML.
 * Supports only: paragraphs, "- "/"* " bullet lines, and **bold** inline
 * spans. Anything else is treated as plain text, still safely escaped by
 * the template via t-esc (never t-raw) -- an LLM response is untrusted
 * input and must never be injected as HTML.
 */

function parseInlineRuns(line) {
    const runs = [];
    const boldRe = /\*\*(.+?)\*\*/g;
    let lastIndex = 0;
    let match;
    while ((match = boldRe.exec(line))) {
        if (match.index > lastIndex) {
            runs.push({ text: line.slice(lastIndex, match.index), bold: false });
        }
        runs.push({ text: match[1], bold: true });
        lastIndex = boldRe.lastIndex;
    }
    if (lastIndex < line.length) {
        runs.push({ text: line.slice(lastIndex), bold: false });
    }
    return runs.length ? runs : [{ text: line, bold: false }];
}

export function formatAiText(text) {
    const lines = (text || "").split("\n");
    const blocks = [];
    let currentList = null;
    for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
            currentList = null;
            continue;
        }
        const bulletMatch = line.match(/^[-*]\s+(.*)$/);
        if (bulletMatch) {
            if (!currentList) {
                currentList = { type: "list", items: [] };
                blocks.push(currentList);
            }
            currentList.items.push(parseInlineRuns(bulletMatch[1]));
            continue;
        }
        currentList = null;
        blocks.push({ type: "paragraph", runs: parseInlineRuns(line) });
    }
    return blocks;
}
