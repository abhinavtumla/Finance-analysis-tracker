// Combines a user-entered (always positive) magnitude with a category's
// income/expense type to produce the signed decimal string the backend
// expects. Stays on strings the whole way through — no parseFloat — so we
// never risk floating-point rounding on a value the backend treats as an
// exact Decimal.
export function toSignedAmount(magnitude: string, categoryType: string): string {
  const digitsOnly = magnitude.trim().replace(/^-/, "");
  return categoryType === "expense" ? `-${digitsOnly}` : digitsOnly;
}

// Inverse: strip any sign so a signed amount can be shown back in a form
// field that only ever collects a positive magnitude.
export function toMagnitude(signedAmount: string): string {
  return signedAmount.replace(/^-/, "");
}
