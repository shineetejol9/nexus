/**
 * Utility functions for dataset handling in NEXUS frontend.
 */

/**
 * Filter out processed clean datasets (*_clean.csv).
 * Works for any filename ending with _clean.csv regardless of case.
 */
export function isOriginalDataset(dataset) {
  const name = dataset?.file_name ?? dataset?.filename ?? ''
  const lower = name.trim().toLowerCase()
  return (
    !lower.endsWith('_clean.csv') &&
    !lower.endsWith('_bad.csv') &&
    !lower.endsWith('_rejected.csv') &&
    !lower.endsWith('_transformed.csv')
  )
}

/**
 * Groups dataset records by file_name, excluding *_clean.csv files.
 * For duplicate versions of the same filename, selects the latest version
 * (highest version number, then highest ID).
 * Returns an array of latest dataset objects with a `history` property containing all versions.
 */
export function groupDatasetsByFilename(allDatasets = []) {
  const map = new Map()

  for (const d of allDatasets) {
    if (!isOriginalDataset(d)) continue

    const rawName = d.file_name ?? d.filename ?? `Dataset ${d.id ?? d.dataset_id}`
    const key = rawName.trim().toLowerCase()
    if (!map.has(key)) {
      map.set(key, [])
    }
    map.get(key).push(d)
  }

  const grouped = []
  for (const [, records] of map) {
    // Sort versions descending by version number, then dataset ID
    records.sort((a, b) => {
      const vA = Number(a.version) || 0
      const vB = Number(b.version) || 0
      if (vA !== vB) return vB - vA
      const idA = Number(a.id ?? a.dataset_id) || 0
      const idB = Number(b.id ?? b.dataset_id) || 0
      return idB - idA
    })
    const latest = records[0]
    grouped.push({
      ...latest,
      history: records,
      totalVersions: records.length
    })
  }

  // Sort grouped dataset list descending by dataset ID
  grouped.sort((a, b) => (Number(b.id ?? b.dataset_id) || 0) - (Number(a.id ?? a.dataset_id) || 0))

  return grouped
}
