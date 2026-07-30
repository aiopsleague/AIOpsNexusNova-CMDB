/* eslint-disable no-useless-constructor */
import { TreeNode } from 'butterfly-dag'
import i18n from '@/lang'

import $ from 'jquery'

// ---------- 节点单击详情卡片 ----------
// 整个画布共享一个详情卡片 DOM，避免节点多的时候产生大量节点
let detailCardEl = null
let activeNodeContainer = null

const escapeHtml = (str) => String(str).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
}[c]))

const formatValue = (value) => {
    if (Array.isArray(value)) {
        return value.join(', ')
    }
    if (typeof value === 'object' && value !== null) {
        return JSON.stringify(value)
    }
    return `${value}`
}

const buildDetailContent = (options) => {
    const rows = (options.attributes || [])
        .map((attr) => {
            let value = options.ci?.[attr.name]
            if (value === undefined || value === null || value === '') {
                return null
            }
            if (attr.is_password) {
                value = '******'
            }
            return `
              <div class="ci-detail-card-row">
                <span class="ci-detail-card-label">${escapeHtml(attr.alias || attr.name)}</span>
                <span class="ci-detail-card-value">${escapeHtml(formatValue(value))}</span>
              </div>`
        })
        .filter(Boolean)
        .join('')

    const uniqueInfo = options.unique_alias && options.unique_value
        ? `<div class="ci-detail-card-unique">${escapeHtml(options.unique_alias || options.unique_name)}：${escapeHtml(options.unique_value)}</div>`
        : ''

    const iconHtml = options.icon
        ? (options.icon.split('$$')[2]
            ? `<img class="ci-detail-card-icon-img" src="/api/common-setting/v1/file/${options.icon.split('$$')[3]}" />`
            : `<span class="ci-detail-card-icon-text">${escapeHtml(options.name?.[0]?.toUpperCase() || '?')}</span>`)
        : `<span class="ci-detail-card-icon-text ci-detail-card-icon-default">${escapeHtml(options.name?.[0]?.toUpperCase() || '?')}</span>`

    return `
      <div class="ci-detail-card-header">
        <div class="ci-detail-card-header-left">
          ${iconHtml}
          <span class="ci-detail-card-title">${escapeHtml(options.title || '')}</span>
        </div>
        <button class="ci-detail-card-close" aria-label="Close">&times;</button>
      </div>
      ${uniqueInfo}
      <div class="ci-detail-card-divider"></div>
      <div class="ci-detail-card-body">
        ${rows || `<div class="ci-detail-card-empty">${i18n.t('noData')}</div>`}
      </div>`
}

const showDetailCard = (container, options) => {
    // 如果同一个节点再次点击，则关闭
    if (activeNodeContainer === container && detailCardEl) {
        hideDetailCard()
        return
    }

    hideDetailCard()
    activeNodeContainer = container

    detailCardEl = document.createElement('div')
    detailCardEl.className = 'ci-detail-card'
    detailCardEl.innerHTML = buildDetailContent(options)
    document.body.appendChild(detailCardEl)

    // 绑定关闭按钮事件
    const closeBtn = detailCardEl.querySelector('.ci-detail-card-close')
    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation()
            hideDetailCard()
        })
    }

    // 计算位置：默认在节点右侧，超出视口则放到左侧/向上收
    const rect = container.getBoundingClientRect()
    const cardWidth = 380
    const cardHeight = Math.min(detailCardEl.scrollHeight, 480)

    let left = rect.right + 12
    if (left + cardWidth > window.innerWidth - 16) {
        left = Math.max(8, rect.left - cardWidth - 12)
    }
    let top = rect.top
    if (top + cardHeight > window.innerHeight - 16) {
        top = Math.max(8, window.innerHeight - cardHeight - 16)
    }

    detailCardEl.style.left = `${left}px`
    detailCardEl.style.top = `${top}px`
    detailCardEl.style.maxHeight = '480px'

    // 动画入场
    requestAnimationFrame(() => {
        detailCardEl.classList.add('ci-detail-card--visible')
    })

    // 点击卡片外部关闭
    setTimeout(() => {
        document.addEventListener('click', handleClickOutside, true)
    }, 0)
}

const handleClickOutside = (e) => {
    if (detailCardEl && !detailCardEl.contains(e.target)) {
        // 排除节点本身的点击（会在 toggle 逻辑里处理）
        if (activeNodeContainer && !activeNodeContainer.contains(e.target)) {
            hideDetailCard()
        }
    }
}

const hideDetailCard = () => {
    document.removeEventListener('click', handleClickOutside, true)
    if (detailCardEl) {
        detailCardEl.classList.remove('ci-detail-card--visible')
        const el = detailCardEl
        el.addEventListener('transitionend', () => {
            if (el.parentNode) {
                el.remove()
            }
        }, { once: true })
        // 兜底：如果 transitionend 没触发，300ms 后强制移除
        setTimeout(() => {
            if (el.parentNode) {
                el.remove()
            }
        }, 350)
        detailCardEl = null
    }
    activeNodeContainer = null
}
// ---------- detail card end ----------

class BaseNode extends TreeNode {
    constructor(opts) {
        super(opts)
    }

    draw = (opts) => {
        const container = $(`<div class="${opts.id.startsWith('Root') ? 'root' : ''} ci-detail-relation-topo-node"></div>`)
            .css('top', opts.top)
            .css('left', opts.left)
            .attr('id', opts.id)
        let icon
        if (opts.options.icon) {
            if (opts.options.icon.split('$$')[2]) {
                icon = $(`<img style="max-width:16px;max-height:16px;" src="/api/common-setting/v1/file/${opts.options.icon.split('$$')[3]}" />`)
            } else {
                icon = $(`<svg class="icon" style="color:${opts.options.icon.split('$$')[1]}" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false" class=""><use data-v-5bd421da="" xlink:href="#${opts.options.icon.split('$$')[0]}"></use></svg>`)
            }
        } else {
            icon = $(`<span class="icon icon-default">${opts.options.name[0].toUpperCase()}</span>`)
        }

        const titleContent = $(`<div title=${opts.options.title} class="title">${opts.options.title}</div>`)
        const uniqueDom = $(`<div class="unique">${opts.options.unique_alias || opts.options.unique_name}：${opts.options.unique_value}<div>`)
        container.append(icon)
        container.append(titleContent)
        container.append(uniqueDom)

        // 单击显示该 CI 的详细信息卡片（构造节点时传入的 ci + attributes）
        if (opts.options.ci && opts.options.attributes) {
            container.on('click', (e) => {
                e.stopPropagation()
                showDetailCard(container[0], opts.options)
            })
            container.css('cursor', 'pointer')
        }

        // 双击节点：跳转到该 CI 的拓扑关系页（根节点不传 ci_id/ci_type_id，不触发）
        if (opts.options.ci_id && opts.options.ci_type_id) {
            container.on('dblclick', () => {
                // 双击时关闭详情卡片
                hideDetailCard()
                this.emit('events', {
                    type: 'custom:dblclickNode',
                    data: { ci_id: opts.options.ci_id, ci_type_id: opts.options.ci_type_id }
                })
            })
        }

        if (opts.options.side && (!opts.options.children.length && !(opts.options.edges && opts.options.edges.length && opts.options.edges.find(e => e.source === opts.options.side && e.sourceNode === opts.options.id)))) {
            const addIcon = $(`<i aria-label="${i18n.t('icon')}: plus-square" class="anticon anticon-plus-square add-icon-${opts.options.side}"><svg viewBox="64 64 896 896" data-icon="plus-square" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false" class=""><path d="M328 544h152v152c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V544h152c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8H544V328c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v152H328c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8z"></path><path d="M880 112H144c-17.7 0-32 14.3-32 32v736c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V144c0-17.7-14.3-32-32-32zm-40 728H184V184h656v656z"></path></svg></i>`)
            container.append(addIcon)
            addIcon.on('click', (e) => {
                e.stopPropagation()
                if (opts.options.side === 'left') {
                    this.emit('events', {
                        type: 'custom:clickLeft',
                        data: { ...this }
                    })
                }
                if (opts.options.side === 'right') {
                    this.emit('events', {
                        type: 'custom:clickRight',
                        data: { ...this }
                    })
                }
            })
        }

        return container[0]
    }
}

export default BaseNode
