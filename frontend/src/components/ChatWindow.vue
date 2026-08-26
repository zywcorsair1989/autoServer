<template>
  <div class="chat-window">
    <div class="chat-titlebar">
      <div class="titlebar-info">
        <div class="ai-avatar-sm">AI</div>
        <div>
          <div class="titlebar-title">智能助手</div>
          <div class="titlebar-sub">基于食尚订产品文档解答</div>
        </div>
      </div>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-if="!messages.length" class="welcome">
        <div class="welcome-icon">👋</div>
        <h3>您好，有什么可以帮您？</h3>
        <p>试试问我："智能话机拨打外地号码要加什么？"</p>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-row', msg.role]"
      >
        <div v-if="msg.role === 'assistant'" class="avatar ai-avatar">AI</div>
        <div class="message-content">
          <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
          <details v-if="msg.sources && msg.sources.length > 0" class="sources-section">
            <summary>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              引用来源（{{ msg.sources.length }} 篇文档）
            </summary>
            <div v-for="(source, idx) in msg.sources" :key="idx" class="source-item">
              <p class="source-header">
                <span class="source-name">{{ source.filename }}</span>
                <span class="source-score">相关度 {{ formatScore(source.score) }}</span>
              </p>
              <p class="source-content">{{ source.content }}</p>
            </div>
          </details>
        </div>
        <div v-if="msg.role === 'user'" class="avatar user-avatar">我</div>
      </div>

      <div v-if="sending" class="message-row assistant">
        <div class="avatar ai-avatar">AI</div>
        <div class="message-content thinking">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="thinking-label">正在查阅文档…</span>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-box">
        <textarea
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="输入您的问题，Enter 发送，Shift+Enter 换行…"
          rows="2"
          :disabled="sending"
        ></textarea>
        <button
          @click="sendMessage"
          class="send-btn"
          :disabled="!inputMessage.trim() || sending"
          title="发送"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
      <p class="input-hint">回答由 AI 基于产品文档生成，请以实际系统功能为准</p>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 单个换行符也转换为 <br>，匹配 LLM 输出习惯
marked.setOptions({ breaks: true, gfm: true })

export default {
  name: 'ChatWindow',
  props: {
    conversation: Object,
    messages: Array,
    sending: {
      type: Boolean,
      default: false
    }
  },
  emits: ['send-message'],
  setup(props, { emit }) {
    const inputMessage = ref('')
    const messagesContainer = ref(null)

    // 将 Markdown 文本渲染为安全 HTML（换行/加粗/列表/代码块）
    const renderMarkdown = (content) => {
      if (!content) return ''
      const html = marked.parse(String(content))
      return DOMPurify.sanitize(html)
    }

    const formatScore = (score) => {
      const n = Number(score)
      return Number.isFinite(n) ? `${Math.round(n * 100)}%` : '—'
    }

    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    const sendMessage = () => {
      if (!inputMessage.value.trim() || props.sending) return

      emit('send-message', inputMessage.value)
      inputMessage.value = ''

      setTimeout(scrollToBottom, 100)
    }

    watch(() => props.messages, scrollToBottom, { deep: true })
    watch(() => props.sending, scrollToBottom)

    return {
      inputMessage,
      messagesContainer,
      sendMessage,
      renderMarkdown,
      formatScore
    }
  }
}
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f7f8fc;
}

/* ============ 顶栏 ============ */
.chat-titlebar {
  padding: 0.85rem 1.5rem;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.titlebar-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ai-avatar-sm {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 0.8rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 8px rgba(102, 126, 234, 0.35);
}

.titlebar-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: #2d2d3a;
}

.titlebar-sub {
  font-size: 0.75rem;
  color: #9a9ab0;
}

/* ============ 消息区 ============ */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.welcome {
  margin: auto;
  text-align: center;
  padding: 2rem;
}

.welcome-icon {
  font-size: 2.6rem;
  margin-bottom: 0.8rem;
}

.welcome h3 {
  color: #2d2d3a;
  font-size: 1.25rem;
  margin: 0 0 0.5rem;
}

.welcome p {
  color: #9a9ab0;
  font-size: 0.88rem;
  margin: 0;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  max-width: 82%;
}

.message-row.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  margin-top: 2px;
}

.ai-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 3px 8px rgba(102, 126, 234, 0.3);
}

.user-avatar {
  background: #2d2d3a;
  color: white;
}

.message-content {
  padding: 0.85rem 1.1rem;
  border-radius: 16px;
  word-wrap: break-word;
  min-width: 0;
  line-height: 1.65;
  font-size: 0.92rem;
}

.message-row.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #5a6ad0 100%);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.message-row.assistant .message-content {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* 思考中动画 */
.message-content.thinking {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0.9rem 1.1rem;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #667eea;
  opacity: 0.4;
  animation: bounce 1.2s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.15s;
}

.dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

.thinking-label {
  margin-left: 0.5rem;
  font-size: 0.82rem;
  color: #9a9ab0;
}

/* Markdown 渲染样式 */
.message-text :deep(p) {
  margin: 0 0 0.5rem 0;
  white-space: pre-wrap;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.message-text :deep(li) {
  margin: 0.25rem 0;
}

.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4) {
  margin: 0.75rem 0 0.5rem 0;
  font-size: 1.05rem;
}

.message-text :deep(h1:first-child),
.message-text :deep(h2:first-child),
.message-text :deep(h3:first-child) {
  margin-top: 0;
}

.message-text :deep(pre) {
  background: #f4f4f8;
  padding: 0.6rem 0.85rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.message-text :deep(code) {
  background: #f4f4f8;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.88em;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
}

.message-text :deep(blockquote) {
  margin: 0.5rem 0;
  padding: 0.25rem 0.75rem;
  border-left: 3px solid #ccc;
  color: #666;
}

.message-text :deep(table) {
  border-collapse: collapse;
  margin: 0.5rem 0;
  font-size: 0.88em;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid #e5e5ee;
  padding: 0.35rem 0.6rem;
}

/* 用户气泡内代码块背景适配蓝底白字 */
.message-row.user .message-text :deep(pre),
.message-row.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-row.user .message-text :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.5);
  color: #eee;
}

/* ============ 引用来源 ============ */
.sources-section {
  margin-top: 0.9rem;
  border-top: 1px dashed #e5e5ee;
  padding-top: 0.7rem;
}

.sources-section summary {
  cursor: pointer;
  font-size: 0.8rem;
  color: #667eea;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  user-select: none;
  list-style: none;
}

.sources-section summary::-webkit-details-marker {
  display: none;
}

.sources-section summary:hover {
  color: #5568d3;
}

.source-item {
  margin-top: 0.6rem;
  padding: 0.6rem 0.75rem;
  background: #f9f9fd;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.source-header {
  margin: 0 0 0.35rem 0;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.source-name {
  font-weight: 600;
  color: #2d2d3a;
}

.source-score {
  color: #9a9ab0;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.source-content {
  margin: 0;
  font-size: 0.82rem;
  color: #77778c;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ============ 输入区 ============ */
.input-area {
  padding: 1rem 1.5rem 0.9rem;
  background: transparent;
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  background: white;
  border-radius: 16px;
  padding: 0.6rem 0.6rem 0.6rem 1rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1.5px solid transparent;
  transition: border-color 0.25s, box-shadow 0.25s;
}

.input-box:focus-within {
  border-color: #667eea;
  box-shadow: 0 4px 24px rgba(102, 126, 234, 0.18);
}

textarea {
  flex: 1;
  border: none;
  resize: none;
  font-family: inherit;
  font-size: 0.92rem;
  line-height: 1.5;
  outline: none;
  color: #2d2d3a;
  background: transparent;
  max-height: 140px;
}

textarea::placeholder {
  color: #b8b8c8;
}

textarea:disabled {
  opacity: 0.6;
}

.send-btn {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.25s;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.35);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(102, 126, 234, 0.5);
}

.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.input-hint {
  text-align: center;
  font-size: 0.72rem;
  color: #b0b0c2;
  margin: 0.55rem 0 0;
}

/* 细滚动条 */
.messages-container::-webkit-scrollbar {
  width: 5px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
</style>
