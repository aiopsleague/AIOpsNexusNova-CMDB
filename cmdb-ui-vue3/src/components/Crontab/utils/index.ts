// Cron expression validation.
//
// The expression is split into: second, minute, hour, day, month, week, year.
// Returns `true` when valid, otherwise a human-readable error message.
export function cronValidate(cronExpression: string): string | true {
  let message: CheckResult = true
  const cronParams = cronExpression.split(' ')
  // The expression must contain 6 (no year) or 7 (with year) fields.
  if (cronParams.length < 6 || cronParams.length > 7) {
    return 'cron表达式需要输入6-7位参数，请重新输入'
  }
  // Day and week must have exactly one `?`, or both be `*`.
  if (
    (cronParams[3] === '?' && cronParams[5] !== '?') ||
    (cronParams[5] === '?' && cronParams[3] !== '?') ||
    (cronParams[3] === '*' && cronParams[5] === '*')
  ) {
    message = checkSecondsField(cronParams[0])
    if (message !== true) return message

    message = checkMinutesField(cronParams[1])
    if (message !== true) return message

    message = checkHoursField(cronParams[2])
    if (message !== true) return message

    message = checkDayOfMonthField(cronParams[3])
    if (message !== true) return message

    message = checkMonthsField(cronParams[4])
    if (message !== true) return message

    message = checkDayOfWeekField(cronParams[5])
    if (message !== true) return message

    if (cronParams.length > 6) {
      message = checkYearField(cronParams[6])
      if (message !== true) return message
    }

    return true
  }
  return '指定日时周必须设为不指定(?),指定周时日必须设为不指定(?)'
}

type CheckResult = string | true

// Shared mutable message used by the check helpers below.
let message: CheckResult = true

function checkSecondsField(secondsField: string): CheckResult {
  return checkField(secondsField, 0, 59, '秒')
}

function checkMinutesField(minutesField: string): CheckResult {
  return checkField(minutesField, 0, 59, '分')
}

function checkHoursField(hoursField: string): CheckResult {
  return checkField(hoursField, 0, 23, '时')
}

function checkDayOfMonthField(dayOfMonthField: string): CheckResult {
  if (dayOfMonthField === '?') {
    return true
  }
  if (dayOfMonthField.indexOf('L') >= 0) {
    return checkFieldWithLetter(dayOfMonthField, 'L', 1, 7, '日')
  } else if (dayOfMonthField.indexOf('W') >= 0) {
    return checkFieldWithLetter(dayOfMonthField, 'W', 1, 31, '日')
  } else if (dayOfMonthField.indexOf('C') >= 0) {
    return checkFieldWithLetter(dayOfMonthField, 'C', 1, 31, '日')
  }
  return checkField(dayOfMonthField, 1, 31, '日')
}

function checkMonthsField(monthsField: string): CheckResult {
  if (monthsField !== '*') {
    monthsField = monthsField
      .replace('JAN', '1')
      .replace('FEB', '2')
      .replace('MAR', '3')
      .replace('APR', '4')
      .replace('MAY', '5')
      .replace('JUN', '6')
      .replace('JUL', '7')
      .replace('AUG', '8')
      .replace('SEP', '9')
      .replace('OCT', '10')
      .replace('NOV', '11')
      .replace('DEC', '12')
    return checkField(monthsField, 1, 12, '月份')
  }
  return true
}

function checkDayOfWeekField(dayOfWeekField: string): CheckResult {
  dayOfWeekField = dayOfWeekField
    .replace('SUN', '1')
    .replace('MON', '2')
    .replace('TUE', '3')
    .replace('WED', '4')
    .replace('THU', '5')
    .replace('FRI', '6')
    .replace('SAT', '7')
  if (dayOfWeekField === '?') {
    return true
  }
  if (dayOfWeekField.indexOf('L') >= 0) {
    return checkFieldWithLetterWeek(dayOfWeekField, 'L', 1, 7, '星期')
  } else if (dayOfWeekField.indexOf('C') >= 0) {
    return checkFieldWithLetterWeek(dayOfWeekField, 'C', 1, 7, '星期')
  } else if (dayOfWeekField.indexOf('#') >= 0) {
    return checkFieldWithLetterWeek(dayOfWeekField, '#', 1, 7, '星期')
  }
  return checkField(dayOfWeekField, 1, 7, '星期')
}

function checkYearField(yearField: string): CheckResult {
  return checkField(yearField, 1970, 2099, '年的')
}

// Generic value check handling `-`, `,`, `/`, `*` and single values.
function checkField(value: string, minimal: number, maximal: number, attribute: string): CheckResult {
  if (value.indexOf('-') > -1) {
    return checkRangeAndCycle(value, minimal, maximal, attribute)
  } else if (value.indexOf(',') > -1) {
    return checkListField(value, minimal, maximal, attribute)
  } else if (value.indexOf('/') > -1) {
    return checkIncrementField(value, minimal, maximal, attribute)
  } else if (value === '*') {
    return true
  }
  return checkIntValue(value, minimal, maximal, true, attribute)
}

// Check that a value is an integer within the given range.
function checkIntValue(
  value: string,
  minimal: number,
  maximal: number,
  checkExtremity: boolean,
  attribute: string
): CheckResult {
  const val = parseInt(value, 10)
  if (Number(value) === val) {
    if (checkExtremity) {
      if (val < minimal || val > maximal) {
        return attribute + '的参数取值范围必须在' + minimal + '-' + maximal + '之间'
      }
      return true
    }
    return true
  }
  return attribute + '的参数存在非法字符，必须为整数或允许的大写英文'
}

// Check an enumeration of comma-separated values.
function checkListField(value: string, minimal: number, maximal: number, attribute: string): CheckResult {
  const values = value.split(',')
  for (let i = 0; i < values.length; i++) {
    message = checkIntValue(values[i], minimal, maximal, true, attribute)
    if (message !== true) {
      return message
    }
    let count = 0
    for (let j = 0; j < values.length; j++) {
      if (values[i] === values[j]) {
        count++
      }
      if (count > 1) {
        return attribute + '中的参数重复'
      }
    }
  }
  let previousValue = -1
  // Ensure values are ordered from small to large.
  for (let i = 0; i < values.length; i++) {
    const currentValue = values[i]
    const val = parseInt(currentValue, 10)
    if (val < previousValue) {
      return attribute + '的参数应该从小到大'
    }
    previousValue = val
  }
  return true
}

// Check an increment (`start/increment`) expression.
function checkIncrementField(value: string, minimal: number, maximal: number, attribute: string): CheckResult {
  if (value.split('/').length > 2) {
    return attribute + "中的参数只能有一个'/'"
  }
  const start = value.substring(0, value.indexOf('/'))
  const increment = value.substring(value.indexOf('/') + 1)
  if (start !== '*') {
    message = checkIntValue(start, minimal, maximal, true, attribute)
    if (message !== true) return message
    message = checkIntValue(increment, minimal, maximal, true, attribute)
    if (message !== true) return message
    return true
  }
  return checkIntValue(increment, minimal, maximal, false, attribute)
}

// Check a range expression, optionally with an increment (`a-b/c`).
function checkRangeAndCycle(params: string, minimal: number, maximal: number, attribute: string): CheckResult {
  if (params.split('-').length > 2) {
    return attribute + "中的参数只能有一个'-'"
  }
  let value: string
  let cycle: string | null = null
  if (params.indexOf('/') > -1) {
    if (params.split('/').length > 2) {
      return attribute + "中的参数只能有一个'/'"
    }
    value = params.split('/')[0]
    cycle = params.split('/')[1]
    message = checkIntValue(cycle, minimal, maximal, true, attribute)
    if (message !== true) {
      return message
    }
  } else {
    value = params
  }
  const startValue = value.substring(0, value.indexOf('-'))
  const endValue = value.substring(value.indexOf('-') + 1)
  message = checkIntValue(startValue, minimal, maximal, true, attribute)
  if (message !== true) return message
  message = checkIntValue(endValue, minimal, maximal, true, attribute)
  if (message !== true) return message
  const startVal = parseInt(startValue, 10)
  const endVal = parseInt(endValue, 10)
  if (endVal < startVal) {
    return attribute + '的取值范围错误，前值必须小于后值'
  }
  if (endVal - startVal < parseInt(cycle ?? '', 10)) {
    return attribute + '的取值范围内的循环无意义'
  }
  return true
}

// Check special letter suffixes for the day-of-month field (`L`, `W`, `C`).
function checkFieldWithLetter(
  value: string,
  letter: string,
  minimalBefore: number,
  maximalBefore: number,
  attribute: string
): CheckResult {
  if (letter === 'L') {
    if (value === 'LW') {
      return true
    }
    if (value === 'L') {
      return true
    }
    if (value.endsWith('LW') && value.length > 2) {
      return attribute + '中的参数，最后的LW前面不能有任何字母参数'
    }
    if (!value.endsWith('L')) {
      return attribute + '中的参数，L字母后面不能有W以外的字符、数字等'
    }
    const num = value.substring(0, value.indexOf(letter))
    return checkIntValue(num, minimalBefore, maximalBefore, true, attribute)
  }

  if (letter === 'W') {
    if (!value.endsWith('W')) {
      return attribute + '中的参数的W必须作为结尾'
    }
    if (value === 'W') {
      return attribute + '中的参数的W前面必须有数字'
    }
    const num = value.substring(0, value.indexOf(letter))
    return checkIntValue(num, minimalBefore, maximalBefore, true, attribute)
  }

  if (letter === 'C') {
    if (!value.endsWith('C')) {
      return attribute + '中的参数的C必须作为结尾'
    }
    if (value === 'C') {
      return attribute + '中的参数的C前面必须有数字'
    }
    const num = value.substring(0, value.indexOf(letter))
    return checkIntValue(num, minimalBefore, maximalBefore, true, attribute)
  }
  return true
}

// Check special letter suffixes for the day-of-week field (`L`, `C`, `#`).
function checkFieldWithLetterWeek(
  value: string,
  letter: string,
  minimalBefore: number,
  maximalBefore: number,
  attribute: string
): CheckResult {
  if (letter === 'L') {
    if (value === 'L') {
      return true
    }
    if (!value.endsWith('L')) {
      return attribute + '中的参数，L字母必须是最后一位'
    }
    const num = value.substring(0, value.indexOf(letter))
    return checkIntValue(num, minimalBefore, maximalBefore, true, attribute)
  }

  if (letter === 'C') {
    if (!value.endsWith('C')) {
      return attribute + '中的参数的C必须作为结尾'
    }
    if (value === 'C') {
      return attribute + '中的参数的C前面必须有数字'
    }
    const num = value.substring(0, value.indexOf(letter))
    return checkIntValue(num, minimalBefore, maximalBefore, true, attribute)
  }

  if (letter === '#') {
    if (value === '#') {
      return attribute + '中的#前后必须有整数'
    }
    if (value.charAt(0) === letter) {
      return attribute + '中的#前面必须有整数'
    }
    if (value.endsWith('#')) {
      return attribute + '中的#后面必须有整数'
    }
    const num1 = value.substring(0, value.indexOf(letter))
    const num2 = value.substring(value.indexOf(letter) + 1, value.length)
    message = checkIntValue(num1, 1, 4, true, attribute + '的#前面')
    if (message !== true) return message
    message = checkIntValue(num2, minimalBefore, maximalBefore, true, attribute + '的#后面')
    if (message !== true) return message
    return true
  }
  return true
}
