<template>
  <div class="knowledge-page">
    <div class="header">
      <h2>Knowledge Base Management</h2>
      <button @click="showCreateDialog = true" class="create-btn">
        + New Collection
      </button>
    </div>

    <div class="collections-grid">
      <div v-for="collection in collections" :key="collection.id" class="collection-card">
        <div class="card-header">
          <h3>{{ collection.name }}</h3>
          <button @click="deleteCollection(collection.id)" class="delete-btn">x</button>
        </div>
        <p class="description">{{ collection.description }}</p>

        <div class="card-actions">
          <input type="file" @change="(e) => uploadFile(collection.id, e)" accept=".pdf,.docx,.txt" />
          <button @click="openQueryDialog(collection)" class="query-btn">Query</button>
        </div>

        <div v-if="documents[collection.id]" class="documents-list">
          <h4>Documents ({{ documents[collection.id].length }})</h4>
          <div
            v-for="doc in documents[collection.id]"
            :key="doc.id"
            class="doc-item"
          >
            <span>{{ doc.filename }}</span>
            <span :class="['status', doc.status]">{{ doc.status }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Collection Dialog -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click="showCreateDialog = false">
      <div class="dialog" @click.stop>
        <h3>Create New Collection</h3>
        <input v-model="newCollection.name" placeholder="Collection Name" />
        <textarea v-model="newCollection.description" placeholder="Description"></textarea>
        <div class="dialog-actions">
          <button @click="createCollection" class="primary-btn">Create</button>
          <button @click="showCreateDialog = false">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Query Dialog -->
    <div v-if="showQueryDialog" class="dialog-overlay" @click="showQueryDialog = false">
      <div class="dialog query-dialog" @click.stop>
        <h3>Query: {{ selectedCollection?.name }}</h3>
        <textarea v-model="queryText" placeholder="Enter your question..."></textarea>
        <div v-if="queryResult" class="query-result">
          <h4>Answer:</h4>
          <p>{{ queryResult.answer }}</p>
          <h4>Sources:</h4>
          <div v-for="source in queryResult.sources" :key="source.document_id" class="source">
            <p><strong>{{ source.filename }}</strong> (Score: {{ source.score.toFixed(2) }})</p>
            <p>{{ source.content }}</p>
          </div>
        </div>
        <div class="dialog-actions">
          <button @click="executeQuery" class="primary-btn">Query</button>
          <button @click="showQueryDialog = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, reactive } from 'vue'
import knowledgeApi from '@/api/knowledge'

export default {
  name: 'Knowledge',
  setup() {
    const collections = ref([])
    const documents = reactive({})
    const showCreateDialog = ref(false)
    const showQueryDialog = ref(false)
    const selectedCollection = ref(null)
    const queryText = ref('')
    const queryResult = ref(null)

    const newCollection = reactive({
      name: '',
      description: ''
    })

    const loadCollections = async () => {
      const response = await knowledgeApi.getCollections()
      collections.value = response.items

      // Load documents for each collection
      for (const collection of collections.value) {
        const docs = await knowledgeApi.getDocuments(collection.id)
        documents[collection.id] = docs.items
      }
    }

    const createCollection = async () => {
      await knowledgeApi.createCollection(
        newCollection.name,
        newCollection.description
      )

      newCollection.name = ''
      newCollection.description = ''
      showCreateDialog.value = false
      await loadCollections()
    }

    const deleteCollection = async (id) => {
      if (confirm('Delete this collection?')) {
        await knowledgeApi.deleteCollection(id)
        await loadCollections()
      }
    }

    const uploadFile = async (collectionId, event) => {
      const file = event.target.files[0]
      if (file) {
        await knowledgeApi.uploadDocument(collectionId, file)
        await loadCollections()
      }
    }

    const openQueryDialog = (collection) => {
      selectedCollection.value = collection
      queryText.value = ''
      queryResult.value = null
      showQueryDialog.value = true
    }

    const executeQuery = async () => {
      const result = await knowledgeApi.query(
        selectedCollection.value.id,
        queryText.value
      )
      queryResult.value = result
    }

    onMounted(loadCollections)

    return {
      collections,
      documents,
      showCreateDialog,
      showQueryDialog,
      selectedCollection,
      queryText,
      queryResult,
      newCollection,
      createCollection,
      deleteCollection,
      uploadFile,
      openQueryDialog,
      executeQuery
    }
  }
}
</script>

<style scoped>
.knowledge-page {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h2 {
  margin: 0;
  color: #333;
}

.create-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 5px;
  cursor: pointer;
}

.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.collection-card {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-header h3 {
  margin: 0;
  color: #333;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #e74c3c;
  font-size: 1.5rem;
  cursor: pointer;
}

.description {
  color: #666;
  margin-bottom: 1rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.card-actions input[type="file"] {
  flex: 1;
}

.query-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
}

.documents-list {
  border-top: 1px solid #eee;
  padding-top: 1rem;
  margin-top: 1rem;
}

.documents-list h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.doc-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f5f5f5;
}

.status {
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
}

.status.completed {
  background: #27ae60;
  color: white;
}

.status.processing {
  background: #f39c12;
  color: white;
}

.status.failed {
  background: #e74c3c;
  color: white;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.dialog {
  background: white;
  padding: 2rem;
  border-radius: 10px;
  width: 500px;
}

.dialog h3 {
  margin: 0 0 1rem 0;
}

.dialog input,
.dialog textarea {
  width: 100%;
  margin-bottom: 1rem;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.dialog textarea {
  min-height: 100px;
  resize: vertical;
}

.dialog-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.dialog-actions button {
  padding: 0.75rem 1.5rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  cursor: pointer;
}

.primary-btn {
  background: #667eea !important;
  color: white !important;
  border-color: #667eea !important;
}

.query-dialog {
  width: 700px;
}

.query-result {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 5px;
  max-height: 400px;
  overflow-y: auto;
}

.source {
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: white;
  border-radius: 5px;
}
</style>