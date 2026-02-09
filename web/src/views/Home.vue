<template>
  <div class="w-full max-w-3xl">
    <div v-if="!auth.authenticated" class="text-center space-y-4">
      <h1 class="text-2xl font-semibold">Войдите через Яндекс</h1>
      <p class="text-muted-foreground">Чтобы продолжить, выполните вход.</p>
      <Button class="w-full" size="lg" @click="login">Войти через Яндекс</Button>
    </div>

    <div v-else>
      <div v-if="devices.length === 0" class="text-center space-y-4">
        <h2 class="text-xl font-medium">У вас нет ещё ни одного устройства</h2>
        <p class="text-muted-foreground">Хотите добавить?</p>
        <Button size="lg" @click="openPicker = true">Добавить устройство</Button>
      </div>

      <div v-else class="space-y-6">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold">Ваши устройства</h2>
          <Button @click="openPicker = true" variant="outline">
            <Plus class="w-4 h-4 mr-2" />
            Добавить устройство
          </Button>
        </div>
        
        <div class="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-2">
          <DeviceCard
            v-for="d in devices"
            :key="d.id"
            :device="d"
            :deleting="deleting === d.id"
            :deletable="true"
            :editable="true"
            :showIcon="true"
            :iconUrl="iconByType(d.yandex_type)"
            @delete="deleteDevice"
            @edit="openEdit"
          />
        </div>
      </div>
      </div>

      <Dialog v-model:open="openPicker">
        <DialogContent class="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader class="flex-shrink-0">
            <DialogTitle>Выберите тип устройства</DialogTitle>
            <DialogDescription>Список типов из Яндекс Дома</DialogDescription>
          </DialogHeader>
          
          <!-- Скроллируемая область с устройствами -->
          <div class="flex-1 overflow-y-auto pr-2">
            <div class="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              <button
                v-for="t in deviceTypes"
                :key="t.type"
                class="border rounded-lg p-4 hover:bg-accent hover:text-accent-foreground transition-colors flex flex-col items-center justify-between text-center aspect-square"
                :class="{ 'bg-primary text-primary-foreground': selectedType === t.type }"
                @click="selectType(t.type)"
              >
                <div class="flex-1 flex items-center justify-center">
                  <img 
                    :src="iconByType(t.type)" 
                    alt="icon" 
                    class="w-20 h-20 object-contain scale-[2]" 
                    @load="onImageLoad"
                    @error="onImageError"
                  />
                </div>
                <div class="flex-shrink-0  flex items-center justify-center">
                  <span class="text-sm font-medium leading-tight">{{ t.name }}</span>
                </div>
              </button>
            </div>
          </div>
          
          <!-- Форма создания устройства -->
          <div v-if="selectedType" class="flex-shrink-0 mt-6 space-y-4 border-t pt-4 pb-2">
            <div class="space-y-2">
              <Label for="name">Название устройства</Label>
              <input id="name" v-model="newName" placeholder="Например, Торшер в гостиной" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50" />
            </div>
            <div class="flex justify-end gap-2">
              <Button variant="outline" @click="openPicker = false">Отмена</Button>
              <Button :disabled="!newName" @click="createDevice">Создать устройство</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <DeviceEditDialog 
        :open="editOpen" 
        :device="editingDevice" 
        @update:open="v => (editOpen = v)" 
        @saved="handleSaved" 
      />
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { onMounted, reactive, ref } from 'vue'
import { Plus } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import DeviceCard from '@/components/DeviceCard.vue'
import DeviceEditDialog from '@/components/DeviceEditDialog.vue'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const API = (import.meta.env.VITE_BACKEND_URL as string) || 'https://y2m.badkiko.ru'

const auth = reactive({ authenticated: false })
const devices = ref<any[]>([])
const deviceTypes = ref<Array<{ type: string; name: string; description: string }>>([])

const openPicker = ref(false)
const selectedType = ref<string>('')
const newName = ref('')
const deleting = ref<number | null>(null)
const editOpen = ref(false)
const editingDevice = ref<any | null>(null)

function iconByType(t: string): string {
  // Карта типов устройств на их иконки
  const iconMap: Record<string, string> = {
    'devices.types.light': 'light',
    'devices.types.light.lamp': 'lamp',
    'devices.types.light.ceiling': 'ceiling',
    'devices.types.light.strip': 'strip',
    'devices.types.socket': 'socket',
    'devices.types.switch': 'switch',
    'devices.types.switch.relay': 'relay',
    'devices.types.thermostat': 'thermostat',
    'devices.types.thermostat.ac': 'thermostat-ac',
    'devices.types.media_device': 'media-device',
    'devices.types.media_device.receiver': 'media-device-receiver',
    'devices.types.media_device.tv': 'media-device-tv',
    'devices.types.media_device.tv_box': 'media-device-tv-box',
    'devices.types.cooking': 'cooking',
    'devices.types.cooking.coffee_maker': 'cooking-coffee-maker',
    'devices.types.cooking.kettle': 'cooking-kettle',
    'devices.types.cooking.multicooker': 'cooking-multicooker',
    'devices.types.dishwasher': 'dishwasher',
    'devices.types.iron': 'iron',
    'devices.types.vacuum_cleaner': 'vacuum-cleaner',
    'devices.types.washing_machine': 'washing-machine',
    'devices.types.pet_drinking_fountain': 'pet-drinking-fountain',
    'devices.types.pet_feeder': 'pet-feeder',
    'devices.types.humidifier': 'humidifier',
    'devices.types.purifier': 'purifier',
    'devices.types.ventilation': 'ventilation',
    'devices.types.ventilation.fan': 'ventilation-fan',
    'devices.types.openable': 'openable',
    'devices.types.openable.curtain': 'openable-curtain',
    'devices.types.openable.valve': 'openable-valve',
    'devices.types.sensor': 'sensor',
    'devices.types.sensor.button': 'sensor-button',
    'devices.types.sensor.climate': 'sensor-climate',
    'devices.types.sensor.gas': 'sensor-gas',
    'devices.types.sensor.illumination': 'sensor-illumination',
    'devices.types.sensor.motion': 'sensor-motion',
    'devices.types.sensor.open': 'sensor-open',
    'devices.types.sensor.smoke': 'sensor-smoke',
    'devices.types.sensor.vibration': 'sensor-vibration',
    'devices.types.sensor.water_leak': 'sensor-water-leak',
    'devices.types.smart_meter': 'smart-meter',
    'devices.types.smart_meter.cold_water': 'smart-meter-cold-water',
    'devices.types.smart_meter.electricity': 'smart-meter-electricity',
    'devices.types.smart_meter.gas': 'smart-meter-gas',
    'devices.types.smart_meter.heat': 'smart-meter-heat',
    'devices.types.smart_meter.hot_water': 'smart-meter-hot-water',
    'devices.types.camera': 'camera',
    'devices.types.other': 'other'
  }

  const iconName = iconMap[t] || 'other'

  // Используем иконки из документации Яндекса
  return `https://yandex.ru/dev/dialogs/smart-home/doc/docs-assets/dev-dialogs-smart-home/rev/211f89014024eea324d5bc4927ec83767c6fac3f/ru/_images/concept.devices/${iconName}.png`
}

async function fetchAuth() {
  const { data } = await axios.get(API + '/api/auth/yandex/status')
  auth.authenticated = !!data.authenticated
}

async function fetchDevices() {
  const { data } = await axios.get(API + '/api/devices')
  devices.value = data
}

async function fetchDeviceTypes() {
  const { data } = await axios.get(API + '/api/device-types')
  deviceTypes.value = data.types
}

function login() {
  window.location.href = API + '/api/auth/yandex/login'
}

function selectType(t: string) {
  selectedType.value = t
}

function onImageLoad(event: Event) {
  const img = event.target as HTMLImageElement
  const src = img.src
  const iconName = src.split('/').pop()?.replace('.png', '') || 'unknown'
  console.log(`✅ Иконка устройства успешно загружена: ${iconName}`)
}

function onImageError(event: Event) {
  const img = event.target as HTMLImageElement
  const failedSrc = img.src
  const iconName = failedSrc.split('/').pop()?.replace('.png', '') || 'unknown'
  console.warn(`❌ Не удалось загрузить иконку устройства: ${iconName}`)
  console.log(`🔄 Заменяем на стандартную иконку "other"`)
  img.src = 'https://yandex.ru/dev/dialogs/smart-home/doc/docs-assets/dev-dialogs-smart-home/rev/211f89014024eea324d5bc4927ec83767c6fac3f/ru/_images/concept.devices/other.png'
}

async function createDevice() {
  await axios.post(API + '/api/devices', { name: newName.value, yandex_type: selectedType.value })
  openPicker.value = false
  newName.value = ''
  selectedType.value = ''
  await fetchDevices()
}

async function deleteDevice(deviceId: number) {
  if (!confirm('Вы уверены, что хотите удалить это устройство? Оно будет отвязано от Яндекс Дома.')) {
    return
  }
  
  deleting.value = deviceId
  try {
    await axios.delete(API + `/api/devices/${deviceId}`)
    await fetchDevices()
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
  await fetchDevices()
}

onMounted(async () => {
  await fetchAuth()
  if (auth.authenticated) {
    await Promise.all([fetchDevices(), fetchDeviceTypes()])
  }
})
</script>
