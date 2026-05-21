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

function renderBlob(bytes: Uint8Array) {
  try {
    const blob = new Blob([bytes], { type: detectMime(bytes) })
    const img = new Image()
    img.onload = () => {
      if (canvas.value!.width !== img.naturalWidth || canvas.value!.height !== img.naturalHeight) {
        canvas.value!.width = img.naturalWidth
        canvas.value!.height = img.naturalHeight
      }
      ctx.drawImage(img, 0, 0)
      URL.revokeObjectURL(img.src)
    }
    img.src = URL.createObjectURL(blob)
  } catch {}
}

onMounted(() => {
  ctx = canvas.value!.getContext('2d')!

  ws = new WebSocket('ws://127.0.0.1:8000/ws')
  // 核心改动：指定接收二进制数据，这对于视频数据传输至关重要
  ws.binaryType = 'arraybuffer' 
  
  ws.onmessage = (event) => {
    // 方案 1：最高效的二进制视频帧/图片流（推荐服务端直接发二进制）
    if (event.data instanceof ArrayBuffer) {
      renderBlob(new Uint8Array(event.data))
      return
    }

    // 方案 2：向下兼容 JSON + Base64 控制帧（目前你的方式）
    if (typeof event.data === 'string') {
      try {
        const data = JSON.parse(event.data)
        if (data.frame) {
          renderFrame(data.frame)
        }

        // 专门处理标注结果等元数据
        if (data.type === 'results') {
          detectResults.value = data.objects
        }
      } catch (e) {
        console.error("Failed to parse websocket message", e)
      }
    }
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<template>
  <div class="video-container">
    <canvas ref="canvas" width="1920" height="1080"></canvas>
    <div class="overlay" v-if="detectResults">
      <h3>识别结果</h3>
      <ul>
        <li v-for="(count, name) in detectResults" :key="name">
          {{ name }}: {{ count }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.video-container {
  position: relative;
  display: inline-block;
}
.overlay {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 15px;
  border-radius: 8px;
  pointer-events: none;
}
.overlay h3 {
  margin: 0 0 10px 0;
  font-size: 18px;
}
.overlay ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.overlay li {
  font-size: 16px;
  margin-bottom: 5px;
}
canvas {
  max-width: 100%;
  height: auto;
  display: block;
}
</style>
