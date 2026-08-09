/** How long the clipboard is given to answer, past which the page takes the line back and offers it by hand. */
const ANSWERS_WITHIN = 1000;

/**
 * Hand one line to the clipboard, and answer with whether it was taken.
 *
 * Three things stand between a press and the clipboard: a table on a home network is reached over plain HTTP,
 * where the browser keeps the clipboard closed to a page; a browser may turn one write down; and a page the
 * window is not showing is left waiting on an answer that never comes. All three read the same way here, so the
 * one thing a caller learns is whether the line is on the clipboard, and a press always ends in a word.
 */
export async function copied(line: string): Promise<boolean> {
  if (!("clipboard" in navigator)) {
    return false;
  }

  try {
    await Promise.race([navigator.clipboard.writeText(line), refusedAfter(ANSWERS_WITHIN)]);
  } catch {
    return false;
  }

  return true;
}

/** The refusal a wait comes to, which is what stands where the clipboard answers neither way. */
function refusedAfter(wait: number): Promise<never> {
  return new Promise((_, refuse) => {
    setTimeout(() => {
      refuse(new Error("The clipboard did not answer"));
    }, wait);
  });
}
