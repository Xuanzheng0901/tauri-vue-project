<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const canvas = ref<HTMLCanvasElement>()
const detectResults = ref<any>(null)
let ctx: CanvasRenderingContext2D
let ws: WebSocket | null = null

function detectMime(bytes: Uint8Array): string {
  if (bytes[0] === 0xFF && bytes[1] === 0xD8) return 'image/jpeg'
  if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47) return 'image/png'
  if (bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46) return 'image/webp'
  return 'image/jpeg'
}

function renderBlob(bytes: Uint8Array) {
  try {
    const blob = new Blob([bytes], { type: detectMime(bytes) })
    const img = new Image()
    img.onload = () => {
      if (!canvas.value) return;
      if (canvas.value.width !== img.naturalWidth || canvas.value.height !== img.naturalHeight) {
        canvas.value.width = img.naturalWidth
        canvas.value.height = img.naturalHeight
      }
      ctx.drawImage(img, 0, 0)
      URL.revokeObjectURL(img.src)
    }
    img.src = URL.createObjectURL(blob)
  } catch {}
}

function renderFrame(b64: string) {
  if (!b64) return
  try {
    const bin = atob(b64)
    const bytes = new Uint8Array(bin.length)
    for (let i = 0; i < bin.length; i++) {
      bytes[i] = bin.charCodeAt(i)
    }
    renderBlob(bytes)
  } catch {}
}

function processJsonMessage(data: any) {
  if (data.frame) {
    renderFrame(data.frame)
  }
  if (data.type === 'results') {
    detectResults.value = data.objects
  }
}

function handleWsMessage(event: MessageEvent) {
  if (event.data instanceof ArrayBuffer) {
    renderBlob(new Uint8Array(event.data))
    return
  }

  if (typeof event.data === 'string') {
    try {
      const data = JSON.parse(event.data)
      processJsonMessage(data)
    } catch (e) {
      console.error("Failed to parse websocket message", e)
    }
  }
}

onMounted(() => {
  ctx = canvas.value!.getContext('2d')!

  ws = new WebSocket('ws://127.0.0.1:8000/ws')
  ws.binaryType = 'arraybuffer'
  ws.onmessage = handleWsMessage
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<template>
  <div class="layout-container">
    <div class="video-section">
      <canvas ref="canvas" width="1920" height="1080"></canvas>
    </div>
    <div class="info-section">
      <h3>识别附加信息</h3>
      <ul v-if="detectResults">
        <li v-for="(count, name) in detectResults" :key="name">
          <span class="label">{{ name }}</span>
          <span class="value">{{ count }}</span>
        </li>
      </ul>
      <div v-else class="no-data">等待数据接入...</div>
    </div>
  </div>
</template>

<style scoped>
.layout-container {
  display: flex;
  flex-direction: row;
  gap: 20px;
  padding: 20px;
  box-sizing: border-box;
  width: 100%;
  height: 90vh;
  //margin: 5vh auto 0; /* 这里加上了 5vh 的顶部外边距，把它往下推，使其视觉上居中 */
}

.video-section {
  flex: 0 0 70%; /* 视频占据 70% 宽度 */
  background-color: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

canvas {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
}

.info-section {
  flex: 1; /* 信息框占据剩余 30% 宽度 */
  background: #ffffff;
  color: #333333;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

/* 适配深色模式 */
@media (prefers-color-scheme: dark) {
  .info-section {
    background: #2a2a2a;
    color: #eeeeee;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  }
}

.info-section h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 20px;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 10px;
}

@media (prefers-color-scheme: dark) {
  .info-section h3 {
    border-bottom: 2px solid #444444;
  }
}

.info-section ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-section li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(128, 128, 128, 0.1);
  padding: 10px 15px;
  border-radius: 6px;
  font-size: 16px;
}

.label {
  font-weight: bold;
  text-transform: capitalize;
}

.value {
  background: #4caf50;
  color: white;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: bold;
}

.no-data {
  color: #888888;
  font-style: italic;
  text-align: center;
  margin-top: 20px;
}
</style>
