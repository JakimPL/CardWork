/**
 * A join code read as the hand of ranks it is, which mirrors `cardserver.codes`.
 *
 * The alphabet is the ranks of a standard deck (`cardwork.cards.rank.Rank`), so a code is something one person
 * says and another writes down. The page reads one to show it back and to say whether what somebody typed is a
 * code at all; whether it admits them is the server's answer alone.
 */
const RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];

/** How many ranks a code is, which mirrors `cardserver.codes.CODE_LENGTH`. */
export const CODE_LENGTH = 6;

/** The ranks a code is drawn from, which are the twelve of them written in one character. */
const CODE_RANKS = RANKS.filter((rank) => rank.length === 1);

/** The marks a person writes a code with that name no rank, which reading drops. */
const SEPARATORS = /[ \-_]/g;

/** One rank apart from the next, which is how a code is read out. */
const APART = " ";

const LONGEST_RANK = Math.max(...RANKS.map((rank) => rank.length));

/**
 * The hand of ranks a code reads as, and nothing where what was offered reads as no hand at all.
 *
 * Reading runs left to right over the code in capitals with the spaces and dashes a person writes it with
 * dropped, and takes the longest rank standing at each place, so `10` is read where `1` would be. Neither `1`
 * nor `0` names a rank on its own, which leaves one reading for every code: `K10AJ2` reads as five ranks and
 * `012345` as none.
 */
export function ranksIn(offered: string): string[] | null {
  const tidy = tidied(offered);
  if (tidy === "") {
    return null;
  }

  const read: string[] = [];
  let place = 0;
  while (place < tidy.length) {
    const rank = rankAt(tidy, place);
    if (rank === null) {
      return null;
    }

    read.push(rank);
    place += rank.length;
  }

  return read;
}

/**
 * The code what was offered stands as, and nothing where it is no code a table gathers on.
 *
 * A code is `CODE_LENGTH` ranks of `CODE_RANKS`, so it stands six ranks long and six characters wide at once.
 * The page reads that much to say when somebody has typed a whole code, and leaves whether it admits them to
 * the server.
 */
export function codeIn(offered: string): string | null {
  const ranks = ranksIn(offered);
  if (ranks?.length !== CODE_LENGTH) {
    return null;
  }

  return ranks.every((rank) => CODE_RANKS.includes(rank)) ? written(ranks) : null;
}

/** A hand of ranks as a code is written down, which is the form an address carries. */
export function written(ranks: string[]): string {
  return ranks.join("");
}

/**
 * One code as it is read out, and as it stands where it reads as no hand of ranks.
 *
 * This is the form a code is shown in wherever a person is meant to pass it on, since ranks apart from one
 * another are what one person says and another writes down.
 */
export function readOut(offered: string): string {
  const ranks = ranksIn(offered);
  return ranks === null ? offered : ranks.join(APART);
}

/** A code as it comes to be read: in capitals, with the separators a person writes it with dropped. */
function tidied(offered: string): string {
  return offered.toUpperCase().replace(SEPARATORS, "");
}

/** The rank standing at one place of a tidied code, which is the longest one reading there. */
function rankAt(tidy: string, place: number): string | null {
  for (let length = LONGEST_RANK; length > 0; length -= 1) {
    const rank = tidy.slice(place, place + length);
    if (RANKS.includes(rank)) {
      return rank;
    }
  }

  return null;
}
