<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-semibold">Устройства</h2>
      <Button @click="load" :disabled="loading">
        {{ loading ? 'Загрузка...' : 'Обновить' }}
      </Button>
    </div>

    <DeviceEditDialog 
      :open="editOpen" 
      :device="editingDevice" 
      @update:open="v => (editOpen = v)" 
      @saved="handleSaved" 
    />
    
    <Card>
      <CardHeader>
        <CardTitle>Добавить устройство</CardTitle>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="create" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="name">Название</Label>
              <Input id="name" v-model="form.name" placeholder="Название устройства" required />
            </div>
            <div class="space-y-2">
              <Label for="type">Тип устройства</Label>
              <Input id="type" v-model="form.yandex_type" placeholder="devices.types.switch" required />
            </div>
            <div class="space-y-2">
              <Label for="adb_host">ADB Host</Label>
              <Input id="adb_host" v-model="form.adb_host" placeholder="192.168.1.10" />
            </div>
            <div class="space-y-2">
              <Label for="adb_port">ADB Port</Label>
              <Input id="adb_port" v-model.number="form.adb_port" type="number" placeholder="5555" />
            </div>
          </div>
          <Button type="submit" :disabled="creating">
            {{ creating ? 'Создание...' : 'Создать устройство' }}
          </Button>
        </form>
      </CardContent>
    </Card>
    
    <div v-if="items.length > 0" class="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
      <DeviceCard
        v-for="device in items"
        :key="device.id"
        :device="device"
        :deleting="deleting === device.id"
        :deletable="true"
        :showNetworkInfo="true"
        :editable="true"
        @delete="deleteDevice"
        @edit="openEdit"
      />
    </div>
    
    <div v-else-if="!loading" class="text-center text-muted-foreground">
      Устройства не найдены. Создайте первое устройство выше.
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import DeviceCard from '@/components/DeviceCard.vue'
import DeviceEditDialog from '@/components/DeviceEditDialog.vue'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const API = (import.meta.env.VITE_BACKEND_URL as string) || 'https://y2m.badkiko.ru'
const items = ref<any[]>([])
const loading = ref(false)
const creating = ref(false)
const deleting = ref<number | null>(null)
const form = ref({ name: '', yandex_type: 'devices.types.switch', adb_host: '', adb_port: 5555 })
const editOpen = ref(false)
const editingDevice = ref<any | null>(null)

async function load() {
  loading.value = true
  try {
    const { data } = await axios.get(API + '/api/devices')
    items.value = data
  } finally {
    loading.value = false
  }
}

async function create() {
  creating.value = true
  try {
    await axios.post(API + '/api/devices', form.value)
    form.value = { name: '', yandex_type: 'devices.types.switch', adb_host: '', adb_port: 5555 }
    await load()
  } finally {
    creating.value = false
  }
}

async function deleteDevice(deviceId: number) {
  if (!confirm('Вы уверены, что хотите удалить это устройство? Оно будет отвязано от Яндекс Дома.')) {
    return
  }
  
  deleting.value = deviceId
  try {
    await axios.delete(API + `/api/devices/${deviceId}`)
    await load()
  } catch (error) {
    console.error('Ошибка при удалении устройства:', error)
    alert('Ошибка при удалении устройства')
  } finally {
    deleting.value = null
  }
}

function openEdit(device: any) {
  editingDevice.value = device
  editOpen.value = true
}

async function handleSaved() {
  editOpen.value = false
  editingDevice.value = null
  await load()
}

// Загружаем устройства при монтировании
load()
</script>
