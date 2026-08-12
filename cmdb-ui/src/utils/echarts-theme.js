/**
 * ECharts dark theme helper.
 * Chart background is kept transparent so it inherits the page theme;
 * the echarts built-in 'dark' theme takes care of text/axis/legend colors.
 */
export function getEchartsTheme () {
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? 'dark' : undefined
}
