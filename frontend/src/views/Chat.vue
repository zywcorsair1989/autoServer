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
      try {
        const response = await chatApi.getConversations()
        // 后端返回 {conversations: [...], total: N} 格式
        conversations.value = response?.conversations || []
        console.log('已加载对话列表:', conversations.value)
      } catch (error) {
        console.error('加载对话列表失败:', error)
        conversations.value = []
      }
    }

    const createNewConversation = async () => {
      try {
        console.log('正在创建新对话...')
        const conv = await chatApi.createConversation('新对话')
        console.log('已创建对话:', conv)
        // Check if conv has an id property
        if (!conv || !conv.id) {
          console.error('收到的对话数据无效:', conv)
          return
        }
        // Add the new conversation to the beginning of the list
        if (Array.isArray(conversations.value)) {
          // If conversations is an array, use unshift
          conversations.value.unshift(conv)
        } else {
          // If conversations is not an array, initialize it as an array with the new conversation
          conversations.value = [conv]
        }
        // Select the newly created conversation
        selectConversation(conv)
      } catch (error) {
        console.error('创建对话失败:', error)
      }
    }

    const selectConversation = async (conv) => {
      try {
        console.log('正在选择对话:', conv)
        if (!conv || !conv.id) {
          console.error('对话数据无效:', conv)
          return
        }
        currentConversation.value = conv
        const response = await chatApi.getConversation(conv.id)
        // Ensure messages are properly formatted
        if (response && response.messages) {
          messages.value = response.messages
        } else {
          messages.value = response || []
        }
        console.log('已加载对话消息:', messages.value)
      } catch (error) {
        console.error('加载对话失败:', error)
        messages.value = []
      }
    }

    const deleteConversation = async (id) => {
      try {
        console.log('尝试删除对话，ID:', id)
        if (!id) {
          console.error('无法删除对话：ID 未定义或为空')
          return
        }
        await chatApi.deleteConversation(id)
        // Remove from the conversations list
        conversations.value = conversations.value.filter(c => c.id !== id)
        // If current conversation is deleted, clear it
        if (currentConversation.value?.id === id) {
          currentConversation.value = null
          messages.value = []
        }
        console.log('成功删除对话')
      } catch (error) {
        console.error('删除对话失败:', error)
      }
    }

    const handleSendMessage = async (message) => {
      try {
        if (!currentConversation.value?.id) {
          console.error('无法发送消息：未选择对话')
          return
        }
        console.log('正在发送消息，对话:', currentConversation.value?.id)
        const response = await chatApi.sendMessage(currentConversation.value.id, message)
        messages.value.push({
          role: 'user',
          content: message
        })
        // 后端返回 {message: {...}, sources: [...]} 格式
        if (response?.message) {
          messages.value.push(response.message)
        }
        // 标题仍为默认值时，将侧边栏标题更新为首条消息话题（与后端逻辑一致）
        if (currentConversation.value.title === '新对话') {
          const text = String(message).split(/\s+/).filter(Boolean).join(' ')
          const newTitle = text.length > 50 ? text.slice(0, 50) + '...' : text
          currentConversation.value.title = newTitle
          const conv = conversations.value.find(c => c.id === currentConversation.value.id)
          if (conv) conv.title = newTitle
        }
      } catch (error) {
        console.error('发送消息失败:', error)
      }
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