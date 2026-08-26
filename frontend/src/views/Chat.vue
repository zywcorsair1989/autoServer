<template>
  <div class="chat-page">
    <div class="sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-logo">食</div>
          <span class="brand-name">食尚订AI客服</span>
        </div>
        <router-link to="/home" class="home-link" title="返回首页">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        </router-link>
      </div>

      <button @click="createNewConversation" class="new-chat-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建对话
      </button>

      <div class="conversation-list">
        <div class="list-label" v-if="conversations.length">历史对话</div>
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['conv-item', { active: currentConversation?.id === conv.id }]"
          @click="selectConversation(conv)"
        >
          <svg class="conv-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <div class="conv-title">{{ conv.title }}</div>
          <button @click.stop="deleteConversation(conv.id)" class="delete-btn" title="删除对话">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>

      <div class="sidebar-footer">
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <div class="chat-area">
      <ChatWindow
        v-if="currentConversation"
        :conversation="currentConversation"
        :messages="messages"
        :sending="sending"
        @send-message="handleSendMessage"
      />
      <div v-else class="no-conversation">
        <div class="empty-icon">💬</div>
        <h3>开始新的对话</h3>
        <p>选择左侧历史对话，或创建一个新对话<br>AI 将基于食尚订产品文档为您解答</p>
        <button @click="createNewConversation" class="empty-cta">+ 新建对话</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import ChatWindow from '@/components/ChatWindow.vue'
import chatApi from '@/api/chat'

export default {
  name: 'Chat',
  components: {
    ChatWindow
  },
  setup() {
    const router = useRouter()
    const userStore = useUserStore()
    const conversations = ref([])
    const currentConversation = ref(null)
    const messages = ref([])
    const sending = ref(false)

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
        if (sending.value) return
        sending.value = true
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
      } finally {
        sending.value = false
      }
    }

    const logout = () => {
      userStore.logout()
      router.push('/login')
    }

    onMounted(loadConversations)

    return {
      conversations,
      currentConversation,
      messages,
      sending,
      createNewConversation,
      selectConversation,
      deleteConversation,
      handleSendMessage,
      logout
    }
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ============ 侧边栏 ============ */
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #1e1f2e 0%, #171827 100%);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 1.25rem 1.1rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.brand-logo {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.brand-name {
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: 0.5px;
}

.home-link {
  color: rgba(255, 255, 255, 0.45);
  display: flex;
  padding: 6px;
  border-radius: 8px;
  transition: all 0.2s;
}

.home-link:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.new-chat-btn {
  margin: 0.25rem 1.1rem 1rem;
  padding: 0.7rem 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(102, 126, 234, 0.5);
}

.new-chat-btn:active {
  transform: translateY(0);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.7rem;
}

.list-label {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.72rem;
  padding: 0.4rem 0.6rem 0.6rem;
  letter-spacing: 1px;
}

.conv-item {
  padding: 0.7rem 0.75rem;
  margin-bottom: 2px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: rgba(255, 255, 255, 0.75);
  transition: all 0.2s;
}

.conv-item:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #fff;
}

.conv-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.35) 0%, rgba(118, 75, 162, 0.25) 100%);
  color: #fff;
}

.conv-icon {
  flex-shrink: 0;
  opacity: 0.6;
}

.conv-title {
  flex: 1;
  font-size: 0.86rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  opacity: 0;
  transition: all 0.2s;
  flex-shrink: 0;
}

.conv-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.15);
}

.sidebar-footer {
  padding: 1rem 1.1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.logout-btn {
  width: 100%;
  background: transparent;
  color: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 0.6rem;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.logout-btn:hover {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.06);
}

/* ============ 主聊天区 ============ */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.no-conversation {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 0.8rem;
  background: #f7f8fc;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.no-conversation h3 {
  color: #333;
  font-size: 1.4rem;
  margin: 0;
}

.no-conversation p {
  color: #999;
  text-align: center;
  line-height: 1.7;
  margin: 0;
}

.empty-cta {
  margin-top: 1.2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 24px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
}

.empty-cta:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

/* 细滚动条 */
.conversation-list::-webkit-scrollbar {
  width: 4px;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}
</style>
