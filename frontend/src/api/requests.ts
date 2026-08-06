import { bodyOf } from "./parsing";
import { refusalOf } from "./refusal";

const CONTENT_TYPE = "content-type";
const JSON_BODY = "application/json";

/** How a command is sent up: one that happens once, and one that states a value. */
export const SENDING = "POST";
export const STATING = "PUT";

/** The headers one request carries, which is the credential it speaks through where it offers one. */
export type Credentials = Record<string, string>;

/**
 * One answer of the server, read as whoever asked for it.
 *
 * The page and the endpoints come out of the same application, so an address is a path and nothing about where
 * the page was loaded from reaches this.
 *
 * @throws Refused when the server answers anything other than the projection asked for.
 */
export async function asking<AnswerT>(address: string, credentials: Credentials): Promise<AnswerT> {
  const response = await fetch(address, { headers: credentials });
  if (!response.ok) {
    throw await refusalOf(response);
  }

  return bodyOf<AnswerT>(response);
}

/**
 * One thing stated to the server, answered with what it made of it.
 *
 * @param address - where the statement is made.
 * @param method - how it is made, which is a `POST` for what happens once and a `PUT` for what states a value.
 * @param credentials - the credential it speaks through, which a stranger offers none of.
 * @param stated - the body, which the server holds to a schema of its own.
 * @throws Refused when the server turns the statement down, which the status tells the kind of.
 */
export async function stating<AnswerT, StatedT>(
  address: string,
  method: string,
  credentials: Credentials,
  stated: StatedT,
): Promise<AnswerT> {
  const response = await fetch(address, {
    method,
    headers: { ...credentials, [CONTENT_TYPE]: JSON_BODY },
    body: JSON.stringify(stated),
  });
  if (!response.ok) {
    throw await refusalOf(response);
  }

  return bodyOf<AnswerT>(response);
}
