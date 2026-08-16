// src/utils/dom.ts
export const domTitle = 'CMDB'

export function setDocumentTitle(title: string) {
  document.title = `${title} - ${domTitle}`
}
