<template>
  <div class="sign-document-page">
    <div v-loading="loading" class="sign-container">
      <h1 v-if="docInfo" class="title">{{ docInfo.document_name }}</h1>
      <p v-if="error" class="error-msg">{{ error }}</p>
      <template v-if="docInfo && !error">
        <div class="flow-steps">
          <div class="step-item" :class="{ active: step >= 0, completed: step > 0 }">
            <div class="step-number">1</div>
            <div class="step-label">{{ $t('signDoc.stepSelect') }}</div>
          </div>
          <div class="step-connector" :class="{ completed: step > 0 }"></div>
          <div class="step-item" :class="{ active: step >= 1, completed: step > 1 }">
            <div class="step-number">2</div>
            <div class="step-label">{{ $t('signDoc.stepSign') }}</div>
          </div>
          <div class="step-connector" :class="{ completed: step > 1 }"></div>
          <div class="step-item" :class="{ active: step >= 2, completed: step > 2 }">
            <div class="step-number">3</div>
            <div class="step-label">{{ $t('signDoc.stepConfirm') }}</div>
          </div>
        </div>

        <div v-if="step === 0" class="step-content">
          <p class="section-label">{{ $t('signDoc.selectHint') }}</p>
          <div v-if="isCoarsePointer" class="position-toolbar">
            <div class="position-toolbar-left">
              <el-button
                size="small"
                :type="selectionMode === 'select' ? 'primary' : 'default'"
                @click="setSelectionMode('select')"
              >
                {{ $t('signDoc.selectMode') }}
              </el-button>
              <el-button
                size="small"
                :type="selectionMode === 'scroll' ? 'primary' : 'default'"
                @click="setSelectionMode('scroll')"
              >
                {{ $t('signDoc.scrollMode') }}
              </el-button>
            </div>
            <div class="position-toolbar-right">
              <el-button size="small" :disabled="pdfZoom <= 1" @click="decreasePdfZoom">-</el-button>
              <div class="zoom-text">{{ Math.round(pdfZoom * 100) }}%</div>
              <el-button size="small" :disabled="pdfZoom >= 2.5" @click="increasePdfZoom">+</el-button>
            </div>
          </div>
          <div
            ref="positionContainerRef"
            class="position-container"
            :class="{
              selecting: isSelectingPosition,
              'select-mode': selectionMode === 'select',
              'scroll-mode': selectionMode === 'scroll'
            }"
            @pointerdown="handlePositionPointerDown"
            @pointermove="handlePositionPointerMove"
            @pointerup="handlePositionPointerUp"
            @pointercancel="handlePositionPointerUp"
            @touchstart="handlePositionTouchStart"
            @touchmove="handlePositionTouchMove"
            @touchend="handlePositionTouchEnd"
            @touchcancel="handlePositionTouchEnd"
          >
            <div ref="positionPdfContainerRef" class="position-pdf">
              <div ref="positionPdfCanvasWrapperRef" class="position-pdf-canvases"></div>
              <div
                v-if="positionRect && positionRect.width > 0 && positionRect.height > 0"
                class="position-rect"
                :style="{
                  left: positionRect.left + 'px',
                  top: positionRect.top + 'px',
                  width: positionRect.width + 'px',
                  height: positionRect.height + 'px'
                }"
              ></div>
            </div>
          </div>
          <div v-if="positionNormalized" class="selected-info">
            <el-card>
              <div>{{ $t('signDoc.selected') }}</div>
              <div>X: {{ positionNormalized.x.toFixed(3) }}, Y: {{ positionNormalized.y.toFixed(3) }}</div>
              <div>{{ $t('signDoc.size') }}: {{ positionNormalized.width.toFixed(3) }} × {{ positionNormalized.height.toFixed(3) }}</div>
              <div>{{ $t('signDoc.page') }}: {{ positionNormalized.page }}</div>
            </el-card>
          </div>
          <div class="step-actions">
            <el-button type="primary" :disabled="!positionNormalized" @click="step = 1">
              {{ $t('signDoc.next') }}
            </el-button>
          </div>
        </div>

        <div v-if="step === 1" class="step-content">
          <p class="section-label">{{ $t('signDoc.signature') }}</p>
          <div class="canvas-wrap">
            <canvas ref="canvasRef" />
          </div>
          <div class="actions">
            <el-button @click="clearSignature">{{ $t('signDoc.clear') }}</el-button>
            <el-button type="primary" :disabled="!hasSignature || !positionNormalized" @click="handleSubmit">
              {{ $t('signDoc.submit') }}
            </el-button>
            <el-button @click="handleCancelFromSign">{{ $t('signDoc.cancel') }}</el-button>
          </div>
        </div>

        <div v-if="step === 2" class="step-content">
          <div class="preview-section">
            <p class="section-label">{{ $t('signDoc.preview') }}</p>
            <div
              v-if="previewUrl && isCoarsePointer"
              ref="finalPreviewContainerRef"
              class="preview-pdfjs"
            >
              <div ref="finalPreviewCanvasWrapperRef" class="preview-pdfjs-canvases"></div>
            </div>
            <iframe
              v-else-if="previewUrl"
              :src="withNoCache(previewUrl)"
              :key="previewNonce"
              class="preview-iframe"
              title="Document preview"
            />
            <a v-if="previewUrl" :href="previewUrl" target="_blank" class="preview-link">
              {{ $t('signDoc.openInNewTab') }}
            </a>
          </div>
          <div class="step-actions">
            <el-button :disabled="confirmLoading" @click="handleCancelFromPreview">
              {{ $t('signDoc.cancel') }}
            </el-button>
            <el-button :disabled="confirmLoading" @click="handleResign">
              {{ $t('signDoc.resign') }}
            </el-button>
            <el-button type="success" :disabled="confirmLoading" :loading="confirmLoading" @click="handleConfirm">
              {{ $t('signDoc.confirm') }}
            </el-button>
          </div>
        </div>
      </template>
      <div v-if="completed" class="success-msg">
        {{ $t('signDoc.success') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { getSignDocumentInfo, submitDocumentSignature, confirmDocumentSignature, discardDocumentSignature } from '@/api/documentSign'

defineOptions({ name: 'SignDocument' })

const { t, locale } = useI18n()
const route = useRoute()
const token = computed(() => route.params.token)

const normalizeLang = (value) => {
  if (!value) return null
  const raw = String(value).trim().toLowerCase()
  if (!raw) return null
  if (raw === 'zh' || raw === 'zh-cn' || raw.startsWith('zh')) return 'zh'
  if (raw === 'en' || raw === 'en-us' || raw === 'en-gb' || raw.startsWith('en')) return 'en'
  return null
}

const queryLang = computed(() => {
  const langValue = route.query?.lang ?? route.query?.language
  if (Array.isArray(langValue)) return normalizeLang(langValue[0])
  return normalizeLang(langValue)
})

const previousLocale = ref(locale.value)
const appliedQueryLocale = ref(null)
const applyLocaleFromQuery = () => {
  const nextLocale = queryLang.value
  appliedQueryLocale.value = nextLocale
  if (nextLocale && locale.value !== nextLocale) {
    locale.value = nextLocale
  }
}

applyLocaleFromQuery()

watch(
  () => route.query,
  () => applyLocaleFromQuery(),
  { deep: true }
)

onBeforeUnmount(() => {
  if (submitSuccess.value && !completed.value) {
    discardDocumentSignature(token.value, apiLang.value).catch(() => {})
  }
  if (initializedCanvasEl) {
    detachCanvasListeners(initializedCanvasEl)
  }
  if (appliedQueryLocale.value && previousLocale.value) {
    locale.value = previousLocale.value
  }
})
const loading = ref(false)
const error = ref('')
const docInfo = ref(null)
const canvasRef = ref(null)
const hasSignature = ref(false)
const submitSuccess = ref(false)
const completed = ref(false)
const confirmLoading = ref(false)
const previewUrl = ref('')
const previewNonce = ref(0)
const step = ref(0)

const apiLang = computed(() => queryLang.value || null)

const discardDraft = async () => {
  try {
    await discardDocumentSignature(token.value, apiLang.value)
  } catch {
  }
}

let pdfjsReady = null
const loadPdfjs = async () => {
  if (pdfjsReady) return pdfjsReady
  pdfjsReady = (async () => {
    const resolvePdfjsLib = (pdfMod) => {
      let cur = pdfMod
      const seen = new Set()
      for (let i = 0; i < 6 && cur && !seen.has(cur); i += 1) {
        if (typeof cur?.getDocument === 'function') return cur
        seen.add(cur)
        cur = cur.default
      }
      return null
    }
    const resolveWorkerSrc = (workerMod) => {
      if (!workerMod) return ''
      if (typeof workerMod === 'string') return workerMod
      let cur = workerMod
      const seen = new Set()
      for (let i = 0; i < 4 && cur && !seen.has(cur); i += 1) {
        if (typeof cur?.default === 'string') return cur.default
        seen.add(cur)
        cur = cur.default
      }
      return ''
    }
    const candidates = [
      {
        pdf: () => import('pdfjs-dist/build/pdf.js'),
        worker: () => import('pdfjs-dist/build/pdf.worker.min.js?url')
      },
      {
        pdf: () => import('pdfjs-dist/legacy/build/pdf.js'),
        worker: () => import('pdfjs-dist/legacy/build/pdf.worker.min.js?url')
      }
    ]
    let lastErr = null
    for (const c of candidates) {
      try {
        const [pdfMod, workerMod] = await Promise.all([c.pdf(), c.worker()])
        const lib = resolvePdfjsLib(pdfMod)
        if (!lib) {
          lastErr = new Error(`pdfjs load failed: getDocument not found, keys: ${(Object.keys(pdfMod || {}) || []).slice(0, 12).join(',')}`)
          continue
        }
        if (lib?.GlobalWorkerOptions) {
          const workerSrc = resolveWorkerSrc(workerMod)
          if (workerSrc) lib.GlobalWorkerOptions.workerSrc = workerSrc
        }
        return lib
      } catch (e) {
        lastErr = e
      }
    }
    throw lastErr || new Error('pdfjs load failed')
  })()
  return pdfjsReady
}

const positionContainerRef = ref(null)
const positionPdfContainerRef = ref(null)
const positionPdfCanvasWrapperRef = ref(null)
const finalPreviewContainerRef = ref(null)
const finalPreviewCanvasWrapperRef = ref(null)
const isSelectingPosition = ref(false)
const positionRect = ref(null)
const positionNormalized = ref(null)
const positionStart = ref({ x: 0, y: 0 })
const pdfPageMetrics = ref([])
const selectingPointerId = ref(null)
const isCoarsePointer = window.matchMedia?.('(pointer: coarse)')?.matches === true
const selectionMode = ref('select')
const pdfZoom = ref(isCoarsePointer ? 1.8 : 1)
const lastPdfPreviewUrl = ref('')
const cachedPdfBytes = ref(null)
const cachedPdfDoc = shallowRef(null)
const finalPreviewRenderedKey = ref('')

const normalizePreviewUrl = (url) => {
  if (!url) return ''
  let normalizedUrl = url
  if (/^https?:\/\//i.test(normalizedUrl)) {
    try {
      const u = new URL(normalizedUrl)
      normalizedUrl = `${u.pathname}${u.search}${u.hash}`
    } catch {
      return normalizedUrl
    }
  }

  const origin = window.location.origin
  const apiBase = (api?.defaults?.baseURL || '').replace(/\/$/, '')
  const apiBaseAbs = /^https?:\/\//i.test(apiBase) ? apiBase : `${origin}${apiBase.startsWith('/') ? apiBase : `/${apiBase}`}`
  const apiBasePath = (() => {
    if (!apiBase) return ''
    if (/^https?:\/\//i.test(apiBase)) {
      try {
        return new URL(apiBase).pathname.replace(/\/$/, '')
      } catch {
        return ''
      }
    }
    return apiBase.startsWith('/') ? apiBase : `/${apiBase}`
  })()

  const path = normalizedUrl.startsWith('/') ? normalizedUrl : `/${normalizedUrl}`
  if (apiBasePath && path.startsWith(`${apiBasePath}/`)) return `${origin}${path}`

  if (path.startsWith('/api/')) {
    if (apiBaseAbs.endsWith('/api')) return `${apiBaseAbs}${path.slice(4)}`
    return `${origin}${path}`
  }
  if (path.startsWith('/public/')) {
    if (apiBaseAbs.endsWith('/api')) return `${apiBaseAbs}${path}`
    return `${origin}/api${path}`
  }
  if (apiBaseAbs.endsWith('/api')) return `${apiBaseAbs}${path}`
  return `${origin}${path}`
}

const withNoCache = (url) => {
  if (!url) return ''
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}_ts=${previewNonce.value}`
}

let drawing = false
let ctx = null
let initializedCanvasEl = null
let activeInput = null
let activePointerId = null

const attachCanvasListeners = (canvas) => {
  if (!canvas) return
  if (window.PointerEvent) {
    canvas.addEventListener('pointerdown', onPointerDown)
    canvas.addEventListener('pointermove', onPointerMove)
    canvas.addEventListener('pointerup', onPointerUp)
    canvas.addEventListener('pointercancel', onPointerUp)
    canvas.addEventListener('touchstart', onTouchStart, { passive: false })
    canvas.addEventListener('touchmove', onTouchMove, { passive: false })
    canvas.addEventListener('touchend', onTouchEnd)
    canvas.addEventListener('touchcancel', onTouchEnd)
  } else {
    canvas.addEventListener('mousedown', onMouseDown)
    canvas.addEventListener('mousemove', onMouseMove)
    canvas.addEventListener('mouseup', onMouseUp)
    canvas.addEventListener('mouseleave', onMouseUp)
    canvas.addEventListener('touchstart', onTouchStart, { passive: false })
    canvas.addEventListener('touchmove', onTouchMove, { passive: false })
    canvas.addEventListener('touchend', onTouchEnd)
    canvas.addEventListener('touchcancel', onTouchEnd)
  }
}

const detachCanvasListeners = (canvas) => {
  if (!canvas) return
  canvas.removeEventListener('pointerdown', onPointerDown)
  canvas.removeEventListener('pointermove', onPointerMove)
  canvas.removeEventListener('pointerup', onPointerUp)
  canvas.removeEventListener('pointercancel', onPointerUp)
  canvas.removeEventListener('mousedown', onMouseDown)
  canvas.removeEventListener('mousemove', onMouseMove)
  canvas.removeEventListener('mouseup', onMouseUp)
  canvas.removeEventListener('mouseleave', onMouseUp)
  canvas.removeEventListener('touchstart', onTouchStart)
  canvas.removeEventListener('touchmove', onTouchMove)
  canvas.removeEventListener('touchend', onTouchEnd)
  canvas.removeEventListener('touchcancel', onTouchEnd)
}

const initCanvas = () => {
  if (!canvasRef.value) return
  const canvas = canvasRef.value
  if (initializedCanvasEl && initializedCanvasEl !== canvas) {
    detachCanvasListeners(initializedCanvasEl)
    ctx = null
    drawing = false
    activeInput = null
    activePointerId = null
  }
  if (initializedCanvasEl === canvas && ctx) return
  initializedCanvasEl = canvas
  const dpr = Math.min(window.devicePixelRatio || 1, 2.5)
  const rect = canvas.getBoundingClientRect()
  const cssWidth = Math.max(1, Math.floor(rect.width || canvas.offsetWidth || 400))
  const cssHeight = Math.max(1, Math.floor(rect.height || 280))
  canvas.width = Math.floor(cssWidth * dpr)
  canvas.height = Math.floor(cssHeight * dpr)
  ctx = canvas.getContext('2d')
  ctx.strokeStyle = '#000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  attachCanvasListeners(canvas)
}

const getPoint = (e) => {
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasRef.value.width / rect.width
  const scaleY = canvasRef.value.height / rect.height
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  }
}

const onMouseDown = (e) => {
  drawing = true
  const p = getPoint(e)
  ctx.beginPath()
  ctx.moveTo(p.x, p.y)
  hasSignature.value = true
}

const onMouseMove = (e) => {
  if (!drawing) return
  const p = getPoint(e)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
}

const onMouseUp = () => {
  drawing = false
}

const onPointerDown = (e) => {
  if (e.pointerType === 'mouse' && e.button !== 0) return
  if (activeInput === 'touch') return
  e.preventDefault()
  try {
    canvasRef.value?.setPointerCapture?.(e.pointerId)
  } catch {}
  activeInput = 'pointer'
  activePointerId = e.pointerId
  drawing = true
  const p = getPoint(e)
  ctx.beginPath()
  ctx.moveTo(p.x, p.y)
  hasSignature.value = true
}

const onPointerMove = (e) => {
  if (activePointerId != null && e.pointerId !== activePointerId) return
  if (!drawing) return
  e.preventDefault()
  const p = getPoint(e)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
}

const onPointerUp = (e) => {
  if (activePointerId != null && e?.pointerId != null && e.pointerId !== activePointerId) return
  drawing = false
  activePointerId = null
  activeInput = null
  try {
    canvasRef.value?.releasePointerCapture?.(e.pointerId)
  } catch {}
}

const onTouchStart = (e) => {
  if (activeInput === 'pointer') return
  e.preventDefault()
  const t = e.touches[0]
  activeInput = 'touch'
  drawing = true
  const p = { x: t.clientX - canvasRef.value.getBoundingClientRect().left, y: t.clientY - canvasRef.value.getBoundingClientRect().top }
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasRef.value.width / rect.width
  const scaleY = canvasRef.value.height / rect.height
  p.x *= scaleX
  p.y *= scaleY
  ctx.beginPath()
  ctx.moveTo(p.x, p.y)
  hasSignature.value = true
}

const onTouchMove = (e) => {
  e.preventDefault()
  if (!drawing || !e.touches.length) return
  const t = e.touches[0]
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasRef.value.width / rect.width
  const scaleY = canvasRef.value.height / rect.height
  const x = (t.clientX - rect.left) * scaleX
  const y = (t.clientY - rect.top) * scaleY
  ctx.lineTo(x, y)
  ctx.stroke()
}

const onTouchEnd = () => {
  drawing = false
  activeInput = null
}

const clearSignature = () => {
  if (!ctx || !canvasRef.value) return
  ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  hasSignature.value = false
}

const getSignatureData = () => {
  if (!canvasRef.value) return null
  return canvasRef.value.toDataURL('image/png')
}

const ensurePreviewPdfDoc = async () => {
  const url = previewUrl.value
  if (!url) return null

  const pdfjs = await loadPdfjs()
  const origin = window.location.origin
  const appBase = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  const tryFetch = async (u) => {
    const res = await fetch(u)
    if (!res.ok) {
      const err = new Error(`${res.status} ${res.statusText}`)
      err.status = res.status
      throw err
    }
    return res
  }
  const candidates = (() => {
    const first = url
    const list = [first]
    if (appBase && first.startsWith(`${origin}${appBase}/api/`)) {
      list.push(first.replace(`${origin}${appBase}/api/`, `${origin}/api/`))
    } else if (first.startsWith(`${origin}/api/`) && appBase) {
      list.push(first.replace(`${origin}/api/`, `${origin}${appBase}/api/`))
    }
    return [...new Set(list)]
  })()

  let res = null
  let lastErr = null
  for (const u of candidates) {
    try {
      res = await tryFetch(withNoCache(u))
      if (previewUrl.value !== u) previewUrl.value = u
      lastErr = null
      break
    } catch (e) {
      lastErr = e
    }
  }
  if (!res) throw lastErr || new Error(t('signDoc.previewFailed'))

  const currentKey = `${previewUrl.value}@@${previewNonce.value}`
  if (lastPdfPreviewUrl.value !== currentKey) {
    lastPdfPreviewUrl.value = currentKey
    cachedPdfBytes.value = null
    cachedPdfDoc.value = null
  }
  if (!cachedPdfBytes.value) {
    cachedPdfBytes.value = await res.arrayBuffer()
  }
  if (!cachedPdfDoc.value) {
    cachedPdfDoc.value = await pdfjs.getDocument({ data: cachedPdfBytes.value, disableWorker: true }).promise
  }
  return cachedPdfDoc.value
}

const renderPdfForSelection = async () => {
  if (!positionPdfContainerRef.value || !positionPdfCanvasWrapperRef.value) return
  const canvasWrapper = positionPdfCanvasWrapperRef.value
  canvasWrapper.innerHTML = ''
  pdfPageMetrics.value = []
  positionRect.value = null
  positionNormalized.value = null

  try {
    const pdf = await ensurePreviewPdfDoc()
    if (!pdf) throw new Error(t('signDoc.previewFailed'))
    const containerWidth = positionPdfContainerRef.value.clientWidth || 1000
    const container = positionContainerRef.value
    const previousScrollLeft = container?.scrollLeft ?? 0
    const previousScrollTop = container?.scrollTop ?? 0
    const dpr = Math.min(2, window.devicePixelRatio || 1)

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber)
      const baseViewport = page.getViewport({ scale: 1 })
      const scale = (containerWidth / baseViewport.width) * pdfZoom.value
      const viewport = page.getViewport({ scale })
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = Math.floor(viewport.width * dpr)
      canvas.height = Math.floor(viewport.height * dpr)
      canvas.style.width = `${Math.floor(viewport.width)}px`
      canvas.style.height = `${Math.floor(viewport.height)}px`
      canvas.style.display = 'block'
      canvas.style.margin = '0 auto 16px'
      canvasWrapper.appendChild(canvas)
      await page.render({
        canvasContext: context,
        viewport,
        transform: [dpr, 0, 0, dpr, 0, 0]
      }).promise
      pdfPageMetrics.value.push({
        offsetTop: canvas.offsetTop,
        offsetLeft: canvas.offsetLeft,
        renderedWidth: canvas.offsetWidth,
        renderedHeight: canvas.offsetHeight
      })
    }
    await nextTick()
    if (container) {
      container.scrollLeft = previousScrollLeft
      container.scrollTop = previousScrollTop
    }
  } catch (e) {
    canvasWrapper.innerHTML = `<div style="padding: 20px; text-align: center; color: #999;">${t('signDoc.previewFailed')}: ${e.message || e}</div>`
  }
}

const renderPdfForFinalPreview = async () => {
  if (!finalPreviewContainerRef.value || !finalPreviewCanvasWrapperRef.value) return
  if (!previewUrl.value) return
  const currentKey = `${previewUrl.value}@@${previewNonce.value}`
  if (finalPreviewRenderedKey.value === currentKey) return
  finalPreviewRenderedKey.value = currentKey

  const canvasWrapper = finalPreviewCanvasWrapperRef.value
  canvasWrapper.innerHTML = ''
  try {
    const pdf = await ensurePreviewPdfDoc()
    if (!pdf) throw new Error(t('signDoc.previewFailed'))
    const containerWidth = finalPreviewContainerRef.value.clientWidth || 1000
    const dpr = Math.min(2.5, window.devicePixelRatio || 1)
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber)
      const baseViewport = page.getViewport({ scale: 1 })
      const scale = containerWidth / baseViewport.width
      const viewport = page.getViewport({ scale })
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = Math.floor(viewport.width * dpr)
      canvas.height = Math.floor(viewport.height * dpr)
      canvas.style.width = `${Math.floor(viewport.width)}px`
      canvas.style.height = `${Math.floor(viewport.height)}px`
      canvas.style.display = 'block'
      canvas.style.margin = '0 auto 16px'
      canvasWrapper.appendChild(canvas)
      await page.render({
        canvasContext: context,
        viewport,
        transform: [dpr, 0, 0, dpr, 0, 0]
      }).promise
    }
  } catch (e) {
    canvasWrapper.innerHTML = `<div style="padding: 20px; text-align: center; color: #999;">${t('signDoc.previewFailed')}: ${e.message || e}</div>`
  }
}

const getPageFromRectPosition = (renderY) => {
  const pages = pdfPageMetrics.value || []
  for (let i = 0; i < pages.length; i += 1) {
    const top = pages[i].offsetTop
    const bottom = top + pages[i].renderedHeight
    if (renderY >= top && renderY < bottom) return i
  }
  return pages.length ? pages.length - 1 : 0
}

const startPositionSelectFromEvent = async (event) => {
  if (!positionContainerRef.value) return
  if (!previewUrl.value) return
  if (!pdfPageMetrics.value.length) {
    await nextTick()
    await renderPdfForSelection()
  }
  const container = positionContainerRef.value
  const rect = container.getBoundingClientRect()
  const clamp = (v, min, max) => Math.max(min, Math.min(v, max))
  const relativeX = clamp(event.clientX - rect.left, 0, rect.width)
  const relativeY = clamp(event.clientY - rect.top, 0, rect.height)
  const renderX = relativeX + container.scrollLeft
  const renderY = relativeY + container.scrollTop
  isSelectingPosition.value = true
  positionStart.value = { x: renderX, y: renderY }
  positionRect.value = { left: renderX, top: renderY, width: 0, height: 0 }
}

const handlePositionPointerDown = async (event) => {
  if (!positionContainerRef.value) return
  if (event.pointerType === 'mouse') {
    selectingPointerId.value = event.pointerId
    try {
      positionContainerRef.value.setPointerCapture?.(event.pointerId)
    } catch {}
    await startPositionSelectFromEvent(event)
    return
  }

  if (selectionMode.value !== 'select') return
  event.preventDefault()
  selectingPointerId.value = event.pointerId
  try {
    positionContainerRef.value.setPointerCapture?.(event.pointerId)
  } catch {}
  await startPositionSelectFromEvent(event)
}

const handlePositionPointerMove = (event) => {
  if (selectingPointerId.value !== null && event.pointerId !== selectingPointerId.value) return

  if (!isSelectingPosition.value || !positionContainerRef.value || !positionRect.value) return
  event.preventDefault()
  const container = positionContainerRef.value
  const rect = container.getBoundingClientRect()
  const clamp = (v, min, max) => Math.max(min, Math.min(v, max))
  const relativeX = clamp(event.clientX - rect.left, 0, rect.width)
  const relativeY = clamp(event.clientY - rect.top, 0, rect.height)
  const currentX = relativeX + container.scrollLeft
  const currentY = relativeY + container.scrollTop

  const left = Math.min(positionStart.value.x, currentX)
  const top = Math.min(positionStart.value.y, currentY)
  const width = Math.abs(currentX - positionStart.value.x)
  const height = Math.abs(currentY - positionStart.value.y)
  positionRect.value = { left, top, width, height }
}

const handlePositionPointerUp = (event) => {
  if (selectingPointerId.value !== null && event?.pointerId && event.pointerId !== selectingPointerId.value) return
  selectingPointerId.value = null
  if (!isSelectingPosition.value) return
  isSelectingPosition.value = false
  if (!positionRect.value) return
  if (positionRect.value.width < 10 || positionRect.value.height < 10) {
    const tapX = positionStart.value?.x ?? positionRect.value.left
    const tapY = positionStart.value?.y ?? positionRect.value.top
    const tapPageIndex = getPageFromRectPosition(tapY)
    const tapPage = pdfPageMetrics.value?.[tapPageIndex]
    if (!tapPage) {
      positionRect.value = null
      positionNormalized.value = null
      return
    }
    const w = Math.min(240, Math.max(120, tapPage.renderedWidth * 0.5))
    const h = Math.min(110, Math.max(60, tapPage.renderedHeight * 0.12))
    const leftMin = tapPage.offsetLeft
    const leftMax = tapPage.offsetLeft + tapPage.renderedWidth - w
    const topMin = tapPage.offsetTop
    const topMax = tapPage.offsetTop + tapPage.renderedHeight - h
    const left = Math.max(leftMin, Math.min(tapX - w / 2, leftMax))
    const top = Math.max(topMin, Math.min(tapY - h / 2, topMax))
    positionRect.value = { left, top, width: w, height: h }
  }

  const pageIndex = getPageFromRectPosition(positionRect.value.top)
  const page = pdfPageMetrics.value?.[pageIndex]
  if (!page) {
    positionNormalized.value = null
    return
  }

  const x = (positionRect.value.left - page.offsetLeft) / page.renderedWidth
  const y = (positionRect.value.top - page.offsetTop) / page.renderedHeight
  const width = positionRect.value.width / page.renderedWidth
  const height = positionRect.value.height / page.renderedHeight
  const clamp = (v) => Math.max(0, Math.min(v, 1))
  positionNormalized.value = {
    x: clamp(x),
    y: clamp(y),
    width: Math.max(0.01, clamp(width)),
    height: Math.max(0.01, clamp(height)),
    page: pageIndex
  }
}

const getTouchPoint = (touchEvent) => {
  if (!touchEvent?.touches?.length) return null
  const t = touchEvent.touches[0]
  return { clientX: t.clientX, clientY: t.clientY }
}

const handlePositionTouchStart = async (event) => {
  if (selectionMode.value !== 'select') return
  const point = getTouchPoint(event)
  if (!point) return
  event.preventDefault()
  await startPositionSelectFromEvent(point)
}

const handlePositionTouchMove = (event) => {
  if (!isSelectingPosition.value || !positionContainerRef.value || !positionRect.value) return
  const point = getTouchPoint(event)
  if (!point) return
  event.preventDefault()
  const container = positionContainerRef.value
  const rect = container.getBoundingClientRect()
  const clamp = (v, min, max) => Math.max(min, Math.min(v, max))
  const relativeX = clamp(point.clientX - rect.left, 0, rect.width)
  const relativeY = clamp(point.clientY - rect.top, 0, rect.height)
  const currentX = relativeX + container.scrollLeft
  const currentY = relativeY + container.scrollTop

  const left = Math.min(positionStart.value.x, currentX)
  const top = Math.min(positionStart.value.y, currentY)
  const width = Math.abs(currentX - positionStart.value.x)
  const height = Math.abs(currentY - positionStart.value.y)
  positionRect.value = { left, top, width, height }
}

const handlePositionTouchEnd = () => {
  if (!isSelectingPosition.value) return
  isSelectingPosition.value = false
  if (!positionRect.value) return
  if (positionRect.value.width < 10 || positionRect.value.height < 10) {
    const tapX = positionStart.value?.x ?? positionRect.value.left
    const tapY = positionStart.value?.y ?? positionRect.value.top
    const tapPageIndex = getPageFromRectPosition(tapY)
    const tapPage = pdfPageMetrics.value?.[tapPageIndex]
    if (!tapPage) {
      positionRect.value = null
      positionNormalized.value = null
      return
    }
    const w = Math.min(240, Math.max(120, tapPage.renderedWidth * 0.5))
    const h = Math.min(110, Math.max(60, tapPage.renderedHeight * 0.12))
    const leftMin = tapPage.offsetLeft
    const leftMax = tapPage.offsetLeft + tapPage.renderedWidth - w
    const topMin = tapPage.offsetTop
    const topMax = tapPage.offsetTop + tapPage.renderedHeight - h
    const left = Math.max(leftMin, Math.min(tapX - w / 2, leftMax))
    const top = Math.max(topMin, Math.min(tapY - h / 2, topMax))
    positionRect.value = { left, top, width: w, height: h }
  }

  const pageIndex = getPageFromRectPosition(positionRect.value.top)
  const page = pdfPageMetrics.value?.[pageIndex]
  if (!page) {
    positionNormalized.value = null
    return
  }

  const x = (positionRect.value.left - page.offsetLeft) / page.renderedWidth
  const y = (positionRect.value.top - page.offsetTop) / page.renderedHeight
  const width = positionRect.value.width / page.renderedWidth
  const height = positionRect.value.height / page.renderedHeight
  const clamp = (v) => Math.max(0, Math.min(v, 1))
  positionNormalized.value = {
    x: clamp(x),
    y: clamp(y),
    width: Math.max(0.01, clamp(width)),
    height: Math.max(0.01, clamp(height)),
    page: pageIndex
  }
}

const applySelectionModeToContainer = () => {
  const el = positionContainerRef.value
  if (!el) return
  el.style.overflow = selectionMode.value === 'select' ? 'hidden' : 'auto'
}

const setSelectionMode = async (mode) => {
  selectionMode.value = mode
  if (mode !== 'select') {
    isSelectingPosition.value = false
  }
  await nextTick()
  applySelectionModeToContainer()
}

const increasePdfZoom = async () => {
  pdfZoom.value = Math.min(2.5, Math.round((pdfZoom.value + 0.15) * 100) / 100)
  await nextTick()
  await renderPdfForSelection()
}

const decreasePdfZoom = async () => {
  pdfZoom.value = Math.max(1, Math.round((pdfZoom.value - 0.15) * 100) / 100)
  await nextTick()
  await renderPdfForSelection()
}

const handleSubmit = async () => {
  const data = getSignatureData()
  if (!data) return
  if (!positionNormalized.value) {
    ElMessage.error(t('signDoc.selectRequired'))
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await submitDocumentSignature(token.value, {
      signature_data: data,
      x: positionNormalized.value.x,
      y: positionNormalized.value.y,
      width: positionNormalized.value.width,
      height: positionNormalized.value.height,
      page: positionNormalized.value.page
    }, apiLang.value)
    submitSuccess.value = true
    completed.value = false
    const draftPreview = res?.preview_full_url || res?.preview_url
    if (draftPreview) {
      previewUrl.value = normalizePreviewUrl(draftPreview)
    } else {
      try {
        docInfo.value = await getSignDocumentInfo(token.value, apiLang.value)
        previewUrl.value = normalizePreviewUrl(docInfo.value?.preview_full_url || docInfo.value?.preview_url)
      } catch {
      }
    }
    previewNonce.value = Date.now()
    step.value = 2
  } catch (e) {
    error.value = e.response?.data?.detail || t('signDoc.submitFailed')
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

const handleConfirm = async () => {
  if (!submitSuccess.value) return
  confirmLoading.value = true
  error.value = ''
  try {
    await confirmDocumentSignature(token.value, apiLang.value)
    ElMessage.success(t('signDoc.confirmSuccess'))
    completed.value = true
    try {
      docInfo.value = await getSignDocumentInfo(token.value, apiLang.value)
      previewUrl.value = normalizePreviewUrl(docInfo.value?.preview_full_url || docInfo.value?.preview_url)
    } catch {
    }
    previewNonce.value = Date.now()
  } catch (e) {
    const msg = e.response?.data?.detail || t('signDoc.confirmFailed')
    error.value = msg
    ElMessage.error(msg)
  } finally {
    confirmLoading.value = false
  }
}

const handleResign = async () => {
  await discardDraft()
  completed.value = false
  submitSuccess.value = false
  clearSignature()
  if (docInfo.value?.preview_full_url || docInfo.value?.preview_url) {
    previewUrl.value = normalizePreviewUrl(docInfo.value.preview_full_url || docInfo.value.preview_url)
    previewNonce.value = Date.now()
  } else {
    try {
      docInfo.value = await getSignDocumentInfo(token.value, apiLang.value)
      previewUrl.value = normalizePreviewUrl(docInfo.value?.preview_full_url || docInfo.value?.preview_url)
      previewNonce.value = Date.now()
    } catch {
    }
  }
  step.value = 1
}

const handleCancelFromSign = async () => {
  clearSignature()
  hasSignature.value = false
  step.value = 0
}

const handleCancelFromPreview = async () => {
  if (submitSuccess.value && !completed.value) {
    await discardDraft()
  }
  submitSuccess.value = false
  completed.value = false
  clearSignature()
  hasSignature.value = false
  if (docInfo.value?.preview_full_url || docInfo.value?.preview_url) {
    previewUrl.value = normalizePreviewUrl(docInfo.value.preview_full_url || docInfo.value.preview_url)
    previewNonce.value = Date.now()
  }
  step.value = 0
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    docInfo.value = await getSignDocumentInfo(token.value, apiLang.value)
    previewUrl.value = normalizePreviewUrl(docInfo.value?.preview_full_url || docInfo.value?.preview_url)
  } catch (e) {
    error.value = e.response?.data?.detail || t('signDoc.loadFailed')
  } finally {
    loading.value = false
    await nextTick()
    if (previewUrl.value) {
      await renderPdfForSelection()
    }
    applySelectionModeToContainer()
  }
})

watch(
  step,
  async (nextStep) => {
    if (nextStep === 1) {
      await nextTick()
      initCanvas()
    }
    if (nextStep === 2 && isCoarsePointer) {
      await nextTick()
      await renderPdfForFinalPreview()
    }
  },
  { immediate: true }
)

watch(
  [previewUrl, previewNonce],
  async () => {
    lastPdfPreviewUrl.value = ''
    cachedPdfBytes.value = null
    cachedPdfDoc.value = null
    finalPreviewRenderedKey.value = ''
    if (finalPreviewCanvasWrapperRef.value) {
      finalPreviewCanvasWrapperRef.value.innerHTML = ''
    }
    if (step.value === 2 && isCoarsePointer) {
      await nextTick()
      await renderPdfForFinalPreview()
    }
  }
)
</script>

<style scoped>
.sign-document-page {
  min-height: 100vh;
  padding: 0;
  background: #f5f5f5;
  display: flex;
}

.sign-container {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  background: #fff;
  padding: 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
}


.title {
  margin: 0 0 24px;
  font-size: 1.8rem;
  font-weight: 600;
}

.error-msg {
  color: #f56c6c;
  margin: 12px 0;
  font-size: 15px;
}

.position-container.selecting {
  touch-action: none;
  user-select: none;
}

.position-container.select-mode {
  touch-action: none;
  user-select: none;
}

.success-msg {
  color: #67c23a;
  font-weight: 500;
  margin-top: 16px;
  font-size: 16px;
}

.section-label {
  font-weight: 600;
  margin: 20px 0 12px;
  font-size: 16px;
}

.preview-section {
  margin-bottom: 24px;
}

.preview-iframe {
  width: 100%;
  height: 90vh;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.preview-pdfjs {
  width: 100%;
  height: 90vh;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: auto;
  background: #fff;
}

.preview-pdfjs-canvases {
  padding: 16px 0;
}

.preview-link {
  display: inline-block;
  margin-top: 8px;
  color: #409eff;
  font-size: 15px;
}

.signature-section {
  padding-top: 16px;
}

.canvas-wrap {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.canvas-wrap canvas {
  display: block;
  width: 100%;
  height: 280px;
  cursor: crosshair;
  touch-action: none;
}

.actions {
  margin-top: 12px;
  display: flex;
  gap: 16px;
}

.flow-steps {
  display: flex;
  align-items: center;
  gap: 20px;
  margin: 16px 0 28px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #909399;
}

.step-item.active {
  color: #303133;
}

.step-item.completed {
  color: #67c23a;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid currentColor;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
  font-size: 16px;
}

.step-connector {
  height: 1px;
  flex: 1;
  background: #dcdfe6;
}

.step-connector.completed {
  background: #67c23a;
}

.step-label {
  font-size: 16px;
  font-weight: 600;
}

.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.position-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  position: sticky;
  top: 0;
  z-index: 5;
  background: #fff;
  padding: 8px 0;
}

.position-toolbar-left,
.position-toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zoom-text {
  min-width: 56px;
  text-align: center;
  font-weight: 600;
  color: #606266;
}

.position-container {
  flex: 1;
  height: auto !important;
  min-height: 400px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: auto;
  position: relative;
  user-select: none;
  -webkit-overflow-scrolling: touch;
}

.position-container.selecting {
  cursor: crosshair;
}

.position-pdf {
  position: relative;
  padding: 12px 8px;
}

.position-pdf-canvases {
  position: relative;
}

.position-rect {
  position: absolute;
  border: 2px dashed #409eff;
  background: rgba(64, 158, 255, 0.08);
  pointer-events: none;
}

.selected-info {
  margin-top: 12px;
}

.step-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}
@media (max-width: 768px) {
  .sign-container {
    max-width: 100%;
    padding: 16px;
  }
  .position-container {
    height: 500px;
  }
  .canvas-wrap canvas {
    height: 220px;
  }
  .position-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .position-toolbar-left,
  .position-toolbar-right {
    justify-content: center;
  }
}
</style>
