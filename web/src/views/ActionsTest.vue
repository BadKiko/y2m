<template>
  <div class="space-y-6">
    <h2 class="text-2xl font-semibold">Тест действий</h2>
    
    <Card>
      <CardHeader>
        <CardTitle>Доступные модули действий</CardTitle>
      </CardHeader>
      <CardContent>
        <Button @click="loadModules" :disabled="loading">
          {{ loading ? 'Загрузка...' : 'Загрузить модули' }}
        </Button>
        
        <div v-if="modules" class="mt-4 space-y-2">
          <div v-for="module in modules" :key="module.name" class="p-3 border rounded">
            <h3 class="font-medium">{{ module.name }}</h3>
            <p class="text-sm text-muted-foreground">{{ module.description }}</p>
          </div>
        </div>
      </CardContent>
    </Card>
    
    <Card>
      <CardHeader>
        <CardTitle>Тест выполнения действия</CardTitle>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="testAction" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="action_type">Тип действия</Label>
              <Input id="action_type" v-model="testForm.action_type" placeholder="adb" required />
            </div>
            <div class="space-y-2">
              <Label for="config">Конфигурация (JSON)</Label>
              <Input id="config" v-model="testForm.config" placeholder='{"command": "echo test"}' required />
            </div>
          </div>
          <Button type="submit" :disabled="testing">
            {{ testing ? 'Выполнение...' : 'Выполнить действие' }}
          </Button>
        </form>
        
        <div v-if="testResult" class="mt-4 p-3 border rounded">
          <h4 class="font-medium">Результат:</h4>
          <pre class="text-sm mt-2">{{ testResult }}</pre>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const API = (import.meta.env.VITE_BACKEND_URL as string) || 'https://y2m.badkiko.ru'
const modules = ref<any>(null)
const loading = ref(false)
const testing = ref(false)
const testResult = ref('')
const testForm = ref({ action_type: 'adb', config: '{"command": "echo test"}' })

async function loadModules() {
  loading.value = true
  try {
    const { data } = await axios.get(API + '/api/actions/modules')
    modules.value = data
  } finally {
    loading.value = false
  }
}

async function testAction() {
  testing.value = true
  testResult.value = ''
  try {
    const { data } = await axios.post(API + '/api/actions/test', testForm.value)
    testResult.value = JSON.stringify(data, null, 2)
  } catch (error: any) {
    testResult.value = `Ошибка: ${error.response?.data?.detail || error.message}`
  } finally {
    testing.value = false
  }
}
</script>

