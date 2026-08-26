const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

// Backend Decimal fields arrive as strings (e.g. "1234.56"); this accepts
// either that or a plain number so callers don't have to convert first.
export function formatCurrency(value: string | number): string {
  const amount = typeof value === "string" ? parseFloat(value) : value;
  return currencyFormatter.format(amount);
}
