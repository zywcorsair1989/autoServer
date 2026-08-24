<template>
  <div class="chat-window">
    <div class="messages-container" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role]"
      >
        <div class="message-content">{{ msg.content }}</div>
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
      sendMessage
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