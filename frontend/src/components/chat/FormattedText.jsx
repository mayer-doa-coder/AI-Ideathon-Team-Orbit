const BULLET_RE = /^[•*-]\s+(.*)/;
const NUMBERED_RE = /^\d+[.)]\s+(.*)/;

function parseBlocks(text) {
  const lines = text.split("\n");
  const blocks = [];
  let listItems = null;
  let listType = null;

  const flush = () => {
    if (listItems) {
      blocks.push({ type: listType, items: listItems });
      listItems = null;
      listType = null;
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      flush();
      continue;
    }

    const bulletMatch = line.match(BULLET_RE);
    const numberedMatch = !bulletMatch && line.match(NUMBERED_RE);

    if (bulletMatch) {
      if (listType !== "ul") flush();
      listType = "ul";
      if (!listItems) listItems = [];
      listItems.push(bulletMatch[1]);
    } else if (numberedMatch) {
      if (listType !== "ol") flush();
      listType = "ol";
      if (!listItems) listItems = [];
      listItems.push(numberedMatch[1]);
    } else {
      flush();
      blocks.push({ type: "p", text: line });
    }
  }
  flush();

  return blocks;
}

// Renders plain-text assistant messages (paragraphs + "- "/"•"/"1." list
// lines, one convention already produced by the backend's node/prompt
// text) as real block-level HTML instead of one flat run of text.
export default function FormattedText({ text }) {
  if (!text) return null;

  return parseBlocks(text).map((block, i) => {
    if (block.type === "ul") {
      return (
        <ul key={i}>
          {block.items.map((item, j) => (
            <li key={j}>{item}</li>
          ))}
        </ul>
      );
    }
    if (block.type === "ol") {
      return (
        <ol key={i}>
          {block.items.map((item, j) => (
            <li key={j}>{item}</li>
          ))}
        </ol>
      );
    }
    return <p key={i}>{block.text}</p>;
  });
}
