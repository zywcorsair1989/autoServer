<template>
  <div class="chat-window">
    <div class="messages-container" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role]"
      >
        <div class="message-content">
          <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
          <div v-if="msg.sources && msg.sources.length > 0" class="sources-section">
            <h4>来源文档：</h4>
            <div v-for="(source, idx) in msg.sources" :key="idx" class="source-item">
              <p class="source-header">
                <strong>{{ source.filename }}</strong>
                <span class="source-score">(得分: {{ source.score.toFixed(2) }})</span>
              </p>
              <p class="source-content">{{ source.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <textarea
        v-model="inputMessage"
        @keydown.enter.prevent="sendMessage"
        placeholder="请输入消息..."
        rows="3"
      ></textarea>
      <button @click="sendMessage" class="send-btn">发送</button>
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
    messages: Array
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

    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    const sendMessage = () => {
      if (!inputMessage.value.trim()) return

      emit('send-message', inputMessage.value)
      inputMessage.value = ''

      setTimeout(scrollToBottom, 100)
    }

    watch(() => props.messages, scrollToBottom, { deep: true })

    return {
      inputMessage,
      messagesContainer,
      sendMessage,
      renderMarkdown
    }
  }
}
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #f5f5f5;
}

.message {
  margin-bottom: 1rem;
  max-width: 70%;
}

.message.user {
  margin-left: auto;
  text-align: right;
}

.message.assistant {
  margin-right: auto;
  text-align: left;
}

.message-content {
  display: inline-block;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  word-wrap: break-word;
}

.message.user .message-content {
  background: #667eea;
  color: white;
}

.message.assistant .message-content {
  background: white;
  color: #333;
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
  background: #f0f0f0;
  padding: 0.5rem 0.75rem;
  border-radius: 5px;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.message-text :deep(code) {
  background: #f0f0f0;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.9em;
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

/* 用户气泡内代码块背景适配蓝底白字 */
.message.user .message-text :deep(pre),
.message.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message.user .message-text :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.5);
  color: #eee;
}

.sources-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.sources-section h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #666;
}

.source-item {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: #f9f9f9;
  border-radius: 5px;
  border-left: 3px solid #667eea;
}

.source-header {
  margin: 0 0 0.25rem 0;
  font-size: 0.85rem;
}

.source-score {
  color: #999;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.source-content {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
}

.input-area {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-top: 1px solid #eee;
}

textarea {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  resize: none;
  font-family: inherit;
}

textarea:focus {
  outline: none;
  border-color: #667eea;
}

.send-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 0 2rem;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s;
}

.send-btn:hover {
  background: #5568d3;
}
</style>