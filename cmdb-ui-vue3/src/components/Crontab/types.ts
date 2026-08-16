// Shared shape of the parsed cron fields (mirrors `contabValueObj`).
export interface CronValue {
  second: string
  min: string
  hour: string
  day: string
  mouth: string
  week: string
  year: string
}

// Numeric clamp helper injected from the parent via the `check` prop.
export type CheckFn = (value: number, min: number, max: number) => number
