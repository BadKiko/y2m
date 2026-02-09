<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref, computed } from 'vue'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CheckCircle, Mic, MessageSquare } from 'lucide-vue-next'

interface Props {
  deviceId: number
  modelValue?: {
    id?: number
    capability: string
    action_type: 'adb' | 'station' | 'mqtt'
    action_config: Record<string, any>
  }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: any): void
}>()

const API = (import.meta.env.VITE_BACKEND_URL as string) || 'https://y2m.badkiko.ru'

const capabilities = ref<Array<{ type: string; retrievable: boolean; reportable: boolean; parameters?: Record<string, any> }>>([])

// Используем computed для синхронизации с props без watch
const form = computed({
  get: () => ({
    capability: props.modelValue?.capability || 'devices.capabilities.on_off',
    action_type: (props.modelValue?.action_type as 'adb' | 'station' | 'mqtt') || 'adb',
    action_config: { ...(props.modelValue?.action_config || {}) },
  }),
  set: (value) => {
    emit('update:modelValue', {
      capability: value.capability,
      action_type: value.action_type,
      action_config: { ...value.action_config }
    })
  }
})

function updateForm(updates: Partial<typeof form.value>) {
  const newValue = {
    ...form.value,
    ...updates
  }
  form.value = newValue
}

async function loadCapabilities() {
  const { data } = await axios.get(API + `/api/devices/${props.deviceId}/capabilities`)
  capabilities.value = data.capabilities || []
}

onMounted(loadCapabilities)

const isADB = computed(() => form.value.action_type === 'adb')
const isStation = computed(() => form.value.action_type === 'station')
const isMQTT = computed(() => form.value.action_type === 'mqtt')

function getCapabilityValue(capability: any): string {
  if (capability.parameters && capability.parameters.instance) {
    return `${capability.type}:${capability.parameters.instance}`
  }
  return capability.type
}

function getCapabilityTypeFromValue(value: string): string {
  if (value.includes(':')) {
    return value.split(':')[0]
  }
  return value
}
</script>

<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <Label>Возможность (capability)</Label>
      <Select :model-value="form.capability" @update:model-value="(v) => updateForm({ capability: v })">
        <SelectTrigger>
          <SelectValue placeholder="Выберите capability" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem v-for="c in capabilities" :key="getCapabilityValue(c)" :value="getCapabilityValue(c)">
              {{ c.description || c.type }}
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>

    <div class="space-y-2">
      <Label>Тип действия</Label>
      <div class="grid grid-cols-3 gap-3">
        <button
          type="button"
          @click="updateForm({ action_type: 'adb' })"
          :class="[
            'p-4 border-2 rounded-lg transition-all hover:shadow-md',
            form.action_type === 'adb' 
              ? 'border-blue-500 bg-blue-50 text-blue-700' 
              : 'border-gray-200 bg-white hover:border-gray-300'
          ]"
        >
          <div class="flex flex-col items-center space-y-2">
            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <CheckCircle class="w-5 h-5 text-white" />
            </div>
            <span class="font-medium text-sm">ADB</span>
            <span class="text-xs text-gray-500">Android Debug Bridge</span>
          </div>
        </button>
        
        <button
          type="button"
          @click="updateForm({ action_type: 'station' })"
          :class="[
            'p-4 border-2 rounded-lg transition-all hover:shadow-md',
            form.action_type === 'station' 
              ? 'border-red-500 bg-red-50 text-red-700' 
              : 'border-gray-200 bg-white hover:border-gray-300'
          ]"
        >
          <div class="flex flex-col items-center space-y-2">
            <div class="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
              <Mic class="w-5 h-5 text-white" />
            </div>
            <span class="font-medium text-sm">Яндекс.Станция</span>
            <span class="text-xs text-gray-500">Голосовые команды</span>
          </div>
        </button>

        <button
          type="button"
          @click="updateForm({ action_type: 'mqtt' })"
          :class="[
            'p-4 border-2 rounded-lg transition-all hover:shadow-md',
            form.action_type === 'mqtt' 
              ? 'border-purple-500 bg-purple-50 text-purple-700' 
              : 'border-gray-200 bg-white hover:border-gray-300'
          ]"
        >
          <div class="flex flex-col items-center space-y-2">
            <div class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
              <MessageSquare class="w-5 h-5 text-white" />
            </div>
            <span class="font-medium text-sm">MQTT</span>
            <span class="text-xs text-gray-500">MQTT топик</span>
          </div>
        </button>
      </div>
    </div>

    <div v-if="isADB" class="space-y-2">
      <Label for="cmd">ADB команда</Label>
      <Input id="cmd" :model-value="form.action_config.cmd" @update:model-value="(v) => updateForm({ action_config: { ...form.action_config, cmd: v } })" placeholder="input keyevent 26" />
      <div class="grid grid-cols-2 gap-2">
        <div>
          <Label for="host">Host (опц.)</Label>
          <Input id="host" :model-value="form.action_config.host" @update:model-value="(v) => updateForm({ action_config: { ...form.action_config, host: v } })" placeholder="192.168.1.10" />
        </div>
        <div>
          <Label for="port">Port (опц.)</Label>
          <Input id="port" type="number" :model-value="form.action_config.port" @update:model-value="(v) => updateForm({ action_config: { ...form.action_config, port: v } })" placeholder="5555" />
        </div>
      </div>
    </div>

    <div v-if="isStation" class="space-y-2">
      <Label for="deviceId">ID Станции</Label>
      <Input id="deviceId" :model-value="form.action_config.deviceId" @update:model-value="(v) => updateForm({ action_config: { ...form.action_config, deviceId: v } })" placeholder="ya-device-id" />
      <Label for="phrase">Голосовая команда</Label>
      <Input id="phrase" :model-value="form.action_config.phrase" @update:model-value="(v) => updateForm({ action_config: { ...form.action_config, phrase: v } })" placeholder="Включи свет в гостиной" />
    </div>

    <div v-if="isMQTT" class="space-y-2">
      <Label for="topic">MQTT топик</Label>
      <Input id="topic" :model-value="form.action_config.topic" @update:model-value="(v) => updateForm({ action_config: { ...form.action_config, topic: v } })" placeholder="home/device/command" />
      <Label for="payload">Полезная нагрузка (JSON)</Label>
      <Input id="payload" :model-value="form.action_config.payload" @update:model-value="(v) => updateForm({ action_config: { ...form.action_config, payload: v } })" placeholder='{"state": "on", "brightness": 50}' />
      <div class="text-xs text-gray-500">
        <p>Доступные переменные:</p>
        <ul class="list-disc list-inside mt-1 space-y-1">
          <li><code>{{value}}</code> - значение от Яндекса (on/off, число, строка)</li>
          <li><code>{{capability}}</code> - тип capability</li>
          <li><code>{{instance}}</code> - instance capability (если есть)</li>
          <li><code>{{device_id}}</code> - ID устройства</li>
        </ul>
      </div>
    </div>
  </div>
</template>


