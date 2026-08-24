<template>
  <div class="chat-page">
    <div class="sidebar">
      <div class="sidebar-header">
        <h3>对话</h3>
        <button @click="createNewConversation" class="new-btn">+ 新建</button>
      </div>

      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['conv-item', { active: currentConversation?.id === conv.id }]"
          @click="selectConversation(conv)"
        >
          <div class="conv-title">{{ conv.title }}</div>
          <button @click.stop="deleteConversation(conv.id)" class="delete-btn">x</button>
        </div>
      </div>
    </div>

    <div class="chat-area">
      <ChatWindow
        v-if="currentConversation"
        :conversation="currentConversation"
        :messages="messages"
        @send-message="handleSendMessage"
      />
      <div v-else class="no-conversation">
        <p>选择一个对话或创建一个新对话</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import ChatWindow from '@/components/ChatWindow.vue'
import chatApi from '@/api/chat'

export default {
  name: 'Chat',
  components: {
    ChatWindow
  },
  setup() {
    const conversations = ref([])
    const currentConversation = ref(null)
    const messages = ref([])

    const loadConversations = async () => {
      const response = await chatApi.getConversations()
      conversations.value = response.items
    }

    const createNewConversation = async () => {
      const conv = await chatApi.createConversation('新对话')
      conversations.value.unshift(conv)
      selectConversation(conv)
    }

    const selectConversation = async (conv) => {
      currentConversation.value = conv
      const response = await chatApi.getConversation(conv.id)
      messages.value = response.messages
    }

    const deleteConversation = async (id) => {
      await chatApi.deleteConversation(id)
      conversations.value = conversations.value.filter(c => c.id !== id)
      if (currentConversation.value?.id === id) {
        currentConversation.value = null
        messages.value = []
      }
    }

    const handleSendMessage = async (message) => {
      const response = await chatApi.sendMessage(currentConversation.value.id, message)
      messages.value.push({
        role: 'user',
        content: message
      })
      messages.value.push(response)
    }

    onMounted(loadConversations)

    return {
      conversations,
      currentConversation,
      messages,
      createNewConversation,
      selectConversation,
      deleteConversation,
      handleSendMessage
    }
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 300px;
  background: #f9f9f9;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.sidebar-header h3 {
  margin: 0;
  color: #333;
}

.new-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conv-item {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.2s;
}

.conv-item:hover,
.conv-item.active {
  background: #e8e8e8;
}

.conv-title {
  font-weight: 500;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #e74c3c;
  font-size: 1.5rem;
  cursor: pointer;
  opacity: 0.5;
}

.delete-btn:hover {
  opacity: 1;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.no-conversation {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #999;
}
</style>