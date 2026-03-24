/**
 * Strips all HTML tags from a string and returns safe plain text.
 * Used for rendering scraped job descriptions without XSS risk.
 */
export function stripHtml(html: string): string {
  // Replace block-level tags with newlines for readability
  const withBreaks = html
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n")
    .replace(/<\/li>/gi, "\n")
    .replace(/<\/h[1-6]>/gi, "\n\n")
    .replace(/<\/div>/gi, "\n");

  // Strip remaining tags
  const stripped = withBreaks.replace(/<[^>]+>/g, "");

  // Decode common HTML entities
  const decoded = stripped
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ");

  // Collapse excessive blank lines
  return decoded.replace(/\n{3,}/g, "\n\n").trim();
}
