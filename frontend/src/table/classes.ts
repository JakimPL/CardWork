/** One class attribute out of the names that apply, leaving out those that do not. */
export function classes(...names: (string | false | null)[]): string {
  return names.filter((name): name is string => typeof name === "string" && name !== "").join(" ");
}
