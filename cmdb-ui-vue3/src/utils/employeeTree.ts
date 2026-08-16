// Helpers for building department + employee tree options. Ported from the
// legacy `@/utils/util` (formatOption / isEmptySubDepartments), with lodash
// cloneDeep replaced by a JSON-based clone (the payload is plain JSON data).

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

interface DepartmentNode {
  [key: string]: any
  employees: any[]
  sub_departments: any[]
  isDisabled?: boolean
}

function isEmptySubDepartments(item: DepartmentNode): boolean {
  if (item.employees.length) {
    return false
  }
  for (let i = 0; i < item.sub_departments.length; i++) {
    if (!isEmptySubDepartments(item.sub_departments[i])) {
      return false
    }
  }
  return true
}

/**
 * Normalize the department tree into vue3-treeselect options.
 * - idType 1: employee id is `${departmentKey}-${employeeKey}`
 * - idType 2: `department-${departmentKey}` / `employee-${employeeKey}`
 * - idType 3: plain `${departmentKey}` / `${employeeKey}`
 */
export function formatOption(
  data: any[],
  idType = 1,
  isDisabledAllCompany?: boolean,
  departmentKey = 'department_id',
  employeeKey = 'employee_id'
): any[] {
  let result: any[] = cloneDeep(data)
  result = result.filter((item) => {
    return item.employees.length || (item.sub_departments.length && !isEmptySubDepartments(item))
  })

  const switchEmployeeIdType = (item: any, employee: any) => {
    switch (idType) {
      case 1:
        return `${item[departmentKey]}-${employee[employeeKey]}`
      case 2:
        return `employee-${employee[employeeKey]}`
      case 3:
        return `${employee[employeeKey]}`
    }
  }

  result.forEach((item) => {
    if (isDisabledAllCompany) {
      item.isDisabled = !item.department_id
    }
    item.id = [1, 3].includes(idType) ? item[departmentKey] : `department-${item[departmentKey]}`
    item.label = item.department_name
    item.children = [
      ...formatOption(
        item.sub_departments.map((dep: any) => ({
          ...dep,
          id: [1, 3].includes(idType) ? dep[departmentKey] : `department-${dep[departmentKey]}`,
          label: dep.department_name,
        })),
        idType,
        isDisabledAllCompany,
        departmentKey,
        employeeKey
      ),
      ...item.employees.map((employee: any) => ({
        ...employee,
        id: switchEmployeeIdType(item, employee),
        label: employee.nickname,
      })),
    ]
  })
  return result
}
