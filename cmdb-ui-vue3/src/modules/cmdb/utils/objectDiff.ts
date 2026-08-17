// src/modules/cmdb/utils/objectDiff.ts

export interface DeepCompareDiff {
  path: string
  value1: string
  value2: string
}

export interface DeepCompareOptions {
  obj1: any
  obj2: any
  directDeepKeys?: string[]
  ignoreKeys?: string[]
}

/** Plain deep equality check (drop-in for lodash.isEqual on JSON-like data). */
function isEqual(a: any, b: any): boolean {
  if (a === b) return true
  if (typeof a !== typeof b) return false
  if (a === null || b === null) return false
  if (typeof a !== 'object') return a === b
  const aKeys = Object.keys(a)
  const bKeys = Object.keys(b)
  if (aKeys.length !== bKeys.length) return false
  return aKeys.every((key) => Object.prototype.hasOwnProperty.call(b, key) && isEqual(a[key], b[key]))
}

/** Compute the list of field-level differences between two objects. */
export function deepCompare({
  obj1,
  obj2,
  directDeepKeys = [],
  ignoreKeys = [],
}: DeepCompareOptions): DeepCompareDiff[] {
  const diffs: DeepCompareDiff[] = []

  const formatValue = (val: any): string => {
    if (val === null) return 'null'
    if (val === undefined) return 'undefined'
    if (typeof val === 'object') {
      return JSON.stringify(val)
    }
    return String(val)
  }

  function compare(a: any, b: any, path = ''): void {
    if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) {
      if (a !== b) {
        diffs.push({
          path,
          value1: formatValue(a),
          value2: formatValue(b),
        })
      }
      return
    }

    const keys1 = new Set(Object.keys(a))
    const keys2 = new Set(Object.keys(b))
    const allKeys = new Set([...keys1, ...keys2])

    allKeys.forEach((key) => {
      if (ignoreKeys.includes(key)) return

      const newPath = path ? `${path}.${key}` : key

      if (directDeepKeys.includes(key)) {
        if (!isEqual(a[key], b[key])) {
          diffs.push({
            path: newPath,
            value1: formatValue(a[key]),
            value2: formatValue(b[key]),
          })
        }
        return
      }

      if (!keys1.has(key)) {
        diffs.push({ path: newPath, value1: 'undefined', value2: formatValue(b[key]) })
      } else if (!keys2.has(key)) {
        diffs.push({ path: newPath, value1: formatValue(a[key]), value2: 'undefined' })
      } else {
        compare(a[key], b[key], newPath)
      }
    })
  }

  compare(obj1, obj2)
  return diffs
}
