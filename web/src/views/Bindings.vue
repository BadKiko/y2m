<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-semibold">Привязки действий</h2>
      <Button @click="load" :disabled="loading">
        {{ loading ? 'Загрузка...' : 'Обновить' }}
      </Button>
    </div>
    
    <Card>
      <CardHeader>
        <CardTitle>Добавить привязку</CardTitle>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="create" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="device_id">ID устройства</Label>
              <Input id="device_id" v-model.number="form.device_id" type="number" placeholder="1" required />
            </div>
            <div class="space-y-2">
              <Label for="capability">Возможность</Label>
              <Input id="capability" v-model="form.capability" placeholder="on_off" required />
            </div>
            <div class="space-y-2">
              <Label for="action_type">Тип действия</Label>
              <Input id="action_type" v-model="form.action_type" placeholder="adb" required />
            </div>
            <div class="space-y-2">
              <Label for="config">Конфигурация (JSON)</Label>
              <Input id="config" v-model="form.config" placeholder='{"command": "input keyevent 26"}' required />
            </div>
          </div>
          <Button type="submit" :disabled="creating">
            {{ creating ? 'Создание...' : 'Создать привязку' }}
          </Button>
        </form>
      </CardContent>
    </Card>
    
    <div v-if="items.length > 0" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card v-for="binding in items" :key="binding.id" class="p-4">
        <CardHeader class="pb-2">
          <CardTitle class="text-lg">Привязка #{{ binding.id }}</CardTitle>
          <CardDescription>{{ getCapabilityDescription(binding.capability) }} → {{ binding.action_type }}</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="text-sm text-muted-foreground">
            Устройство: {{ binding.device_id }}
          </div>
          <div class="text-sm text-muted-foreground mt-1">
            Конфиг: {{ binding.config }}
          </div>
        </CardContent>
      </Card>
    </div>
    
    <div v-else-if="!loading" class="text-center text-muted-foreground">
      Привязки не найдены. Создайте первую привязку выше.
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const API = (import.meta.env.VITE_BACKEND_URL as string) || 'https://y2m.badkiko.ru'
const items = ref<any[]>([])
const loading = ref(false)
const creating = ref(false)
const form = ref({ device_id: 1, capability: 'on_off', action_type: 'adb', config: '{"command": "input keyevent 26"}' })

async function load() {
  loading.value = true
  try {
    const { data } = await axios.get(API + '/api/bindings')
    items.value = data
  } finally {
    loading.value = false
  }
}

async function create() {
  creating.value = true
  try {
    await axios.post(API + '/api/bindings', form.value)
    form.value = { device_id: 1, capability: 'on_off', action_type: 'adb', config: '{"command": "input keyevent 26"}' }
    await load()
  } finally {
    creating.value = false
  }
}

function getCapabilityDescription(capability: string): string {
  // Если capability содержит instance (формат "type:instance")
  if (capability.includes(':')) {
    const [type, instance] = capability.split(':')
    const typeDescriptions: Record<string, Record<string, string>> = {
      "devices.capabilities.range": {
        "brightness": "Яркость",
        "volume": "Громкость",
        "temperature": "Температура",
        "channel": "Канал"
      },
      "devices.capabilities.mode": {
        "input_source": "Источник сигнала",
        "work_mode": "Режим работы",
        "tea_mode": "Режим заваривания чая"
      },
      "devices.capabilities.toggle": {
        "backlight": "Подсветка",
        "controls_locked": "Блокировка управления",
        "mute": "Отключение звука",
        "pause": "Пауза"
      }
    }
    
    if (type in typeDescriptions && instance in typeDescriptions[type]) {
      return typeDescriptions[type][instance]
    }
    
    return `${getBaseCapabilityDescription(type)} (${instance})`
  }
  
  // Базовые описания
  const descriptions: Record<string, string> = {
    "devices.capabilities.on_off": "Включение/выключение",
    "devices.capabilities.range": "Диапазон",
    "devices.capabilities.mode": "Режим",
    "devices.capabilities.toggle": "Переключатель",
    "devices.capabilities.color_setting": "Настройка цвета",
    "devices.capabilities.video_stream": "Видеопоток"
  }
  
  return descriptions[capability] || capability.split('.').pop()?.replace('_', ' ') || capability
}

function getBaseCapabilityDescription(capability: string): string {
  const descriptions: Record<string, string> = {
    "devices.capabilities.on_off": "Включение/выключение",
    "devices.capabilities.range": "Диапазон",
    "devices.capabilities.mode": "Режим",
    "devices.capabilities.toggle": "Переключатель",
    "devices.capabilities.color_setting": "Настройка цвета",
    "devices.capabilities.video_stream": "Видеопоток"
  }
  
  return descriptions[capability] || capability.split('.').pop()?.replace('_', ' ') || capability
}

// Загружаем привязки при монтировании
load()
</script>
