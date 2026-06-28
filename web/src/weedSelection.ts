export const MAX_WEED_SELECTIONS = 5

export function normalizeWeedName(weed: string): string {
  return weed.trim().replace(/\s+/g, ' ')
}

function normalizeForMatch(value: string): string {
  return normalizeWeedName(value).toLowerCase().replace(/_/g, ' ')
}

export function addWeedSelection(selected: string[], weed: string): string[] {
  const normalized = normalizeWeedName(weed)

  if (!normalized || selected.includes(normalized) || selected.length >= MAX_WEED_SELECTIONS) {
    return selected
  }

  return [...selected, normalized]
}

export function removeWeedSelection(selected: string[], weed: string): string[] {
  return selected.filter((selectedWeed) => selectedWeed !== weed)
}

export function resolveWeedOption(options: string[], query: string): string | undefined {
  const normalizedQuery = normalizeForMatch(query)

  return options.find((weed) => normalizeForMatch(weed) === normalizedQuery)
}

export function filterWeedOptions(options: string[], query: string, selected: string[]): string[] {
  const normalizedQuery = query.trim().toLowerCase()

  return options
    .filter((weed) => !selected.includes(weed))
    .filter((weed) => !normalizedQuery || weed.toLowerCase().includes(normalizedQuery))
    .slice(0, 12)
}
