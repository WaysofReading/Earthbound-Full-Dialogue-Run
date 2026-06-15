// Dialogue text presentation. The extraction preserves two control artifacts
// that are accurate but noisy to read: U+FFFD, a line-start marker (renders as a
// diamond/box) that precedes most printed lines, and the [PAUSE] timing token.
// They're stripped by default; the panel's "show control codes" toggle renders
// the raw text instead.

export function cleanDialogue(text: string): string {
  if (!text) return text
  return text
    .replace(/\uFFFD/g, '') // line-start marker
    .replace(/\[PAUSE\]/g, '') // pause timing token
    .replace(/ {2,}/g, ' ') // collapse spaces left behind
    .replace(/[ \t]+\n/g, '\n') // trim trailing spaces before newlines
    .replace(/\n{3,}/g, '\n\n') // collapse large gaps
    .trim()
}

// Respect the toggle: show raw text when control codes are enabled.
export function displayDialogue(text: string, showControlCodes: boolean): string {
  return showControlCodes ? text : cleanDialogue(text)
}
