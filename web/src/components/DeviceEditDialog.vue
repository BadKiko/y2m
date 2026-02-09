<script setup lang="ts">
import axios from 'axios'
import { ref, watch, onMounted } from 'vue'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import BindingForm from '@/components/BindingForm.vue'

interface Device { id: number; name: string; yandex_type: string }

interface Props {
  open: boolean
  device: Device | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'saved'): void
}>()

const API = (import.meta.env.VITE_BACKEND_URL as string) || 'https://y2m.badkiko.ru'

const activeTab = ref('general')
const saving = ref(false)
const testing = ref<number | null>(null)

const name = ref('')
const bindings = ref<any[]>([])
const selectedBinding = ref<any | null>(null)
const editingBindingId = ref<number | null>(null)

watch(
  () => props.device,
  (d) => {
    if (!d) return
    name.value = d.name
    loadBindings()
  },
  { immediate: true }
)

async function loadBindings() {
  if (!props.device) return
  const { data } = await axios.get(API + '/api/bindings')
  bindings.value = (data || []).filter((b: any) => b.device_id === props.device!.id)
}

async function saveDevice() {
  if (!props.device) return
  saving.value = true
  try {
    await axios.put(API + `/api/devices/${props.device.id}`, { name: name.value, yandex_type: props.device.yandex_type })
    emit('saved')
  } finally {
    saving.value = false
  }
}

function startCreateBinding() {
  selectedBinding.value = { capability: 'devices.capabilities.on_off', action_type: 'adb', action_config: {} }
  editingBindingId.value = null
}

function startEditBinding(b: any) {
  selectedBinding.value = JSON.parse(JSON.stringify({ capability: b.capability, action_type: b.action_type, action_config: b.action_config }))
  editingBindingId.value = b.id
}

async function saveBinding() {
  if (!props.device || !selectedBinding.value) return
  const payload = { device_id: props.device.id, ...selectedBinding.value }
  if (editingBindingId.value) {
    await axios.put(API + `/api/bindings/${editingBindingId.value}`, payload)
  } else {
    await axios.post(API + `/api/bindings`, payload)
  }
  selectedBinding.value = null
  editingBindingId.value = null
  await loadBindings()
}

async function deleteBinding(bindingId: number) {
  if (!confirm('Удалить привязку?')) return
  await axios.delete(API + `/api/bindings/${bindingId}`)
  await loadBindings()
}

async function testBinding(bindingId: number) {
  testing.value = bindingId
  try {
    await axios.post(API + `/api/bindings/${bindingId}/invoke`, { payload: selectedBinding.value?.action_config })
  } finally {
    testing.value = null
  }
}

function close() { emit('update:open', false) }

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
</script>

<template>
  <Dialog :open="open" @update:open="v => emit('update:open', v)">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle>Редактирование устройства</DialogTitle>
        <DialogDescription>Переименование и привязка действий</DialogDescription>
      </DialogHeader>

      <Tabs v-model="activeTab" class="w-full">
        <TabsList class="grid grid-cols-2 w-full">
          <TabsTrigger value="general">Общее</TabsTrigger>
          <TabsTrigger value="actions">Действия</TabsTrigger>
        </TabsList>

        <TabsContent value="general" class="space-y-4 pt-4">
          <div class="space-y-2">
            <Label for="name">Название</Label>
            <Input id="name" v-model="name" />
          </div>
          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="close">Закрыть</Button>
            <Button :disabled="saving" @click="saveDevice">{{ saving ? 'Сохранение...' : 'Сохранить' }}</Button>
          </div>
        </TabsContent>

        <TabsContent value="actions" class="space-y-4 pt-4">
          <div class="flex justify-between items-center">
            <div class="font-medium">Привязки</div>
            <Button size="sm" @click="startCreateBinding">Добавить</Button>
          </div>
          <div class="space-y-2">
            <div v-for="b in bindings" :key="b.id" class="border rounded p-3">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-sm">{{ getCapabilityDescription(b.capability) }}</div>
                  <div class="text-xs text-muted-foreground">{{ b.action_type }}</div>
                </div>
                <div class="flex gap-2">
                  <Button size="sm" variant="outline" @click="startEditBinding(b)">Редактировать</Button>
                  <Button size="sm" variant="destructive" @click="deleteBinding(b.id)">Удалить</Button>
                  <Button size="sm" :disabled="testing === b.id" @click="testBinding(b.id)">{{ testing === b.id ? 'Проверка...' : 'Проверить' }}</Button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedBinding" class="border rounded p-3 space-y-3">
            <BindingForm :device-id="device!.id" v-model="selectedBinding" />
            <div class="flex justify-end gap-2">
              <Button size="sm" variant="outline" @click="selectedBinding = null; editingBindingId = null">Отмена</Button>
              <Button size="sm" @click="saveBinding">Сохранить привязку</Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </DialogContent>
  </Dialog>
</template>


