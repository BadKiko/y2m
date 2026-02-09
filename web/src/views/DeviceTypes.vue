<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-semibold">Типы устройств</h2>
      <div class="flex gap-2">
        <Button @click="showAddDeviceDialog = true" variant="outline">
          Добавить устройство
        </Button>
        <Button @click="load" :disabled="loading">
          {{ loading ? 'Загрузка...' : 'Обновить' }}
        </Button>
      </div>
    </div>

    <!-- Диалог добавления устройства -->
    <Dialog :open="showAddDeviceDialog" @update:open="showAddDeviceDialog = $event">
      <DialogContent class="max-w-6xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Добавить новое устройство</DialogTitle>
          <DialogDescription>
            Выберите тип устройства для добавления в ваш умный дом
          </DialogDescription>
        </DialogHeader>

        <div class="max-h-[70vh] overflow-y-auto">
          <div v-if="data" class="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <div
              v-for="deviceType in data.types"
              :key="deviceType.type"
              @click="selectDeviceType(deviceType)"
              class="p-4 border rounded-lg cursor-pointer hover:bg-accent hover:text-accent-foreground transition-colors"
              :class="{ 'bg-primary text-primary-foreground': selectedDeviceType?.type === deviceType.type }"
            >
              <div class="flex flex-col items-center text-center space-y-2">
                <img
                  :src="getDeviceIcon(deviceType.type)"
                  :alt="deviceType.name"
                  class="w-12 h-12 object-contain"
                  @error="onImageError"
                  @load="onImageLoad"
                />
                <div>
                  <h4 class="font-medium text-sm">{{ deviceType.name }}</h4>
                  <p class="text-xs text-muted-foreground line-clamp-2">{{ deviceType.description }}</p>
                </div>
                <div class="text-xs text-muted-foreground">
                  {{ deviceType.type }}
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center text-muted-foreground py-8">
            Загружаем типы устройств...
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="showAddDeviceDialog = false">
            Отмена
          </Button>
          <Button @click="addSelectedDevice" :disabled="!selectedDeviceType">
            Добавить устройство
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Основной список устройств -->
    <div v-if="data" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <Card v-for="deviceType in data.types" :key="deviceType.type" class="p-4 hover:shadow-md transition-shadow">
        <CardHeader class="pb-2">
          <CardTitle class="text-lg flex items-center gap-2">
            <img
              :src="getDeviceIcon(deviceType.type)"
              :alt="deviceType.name"
              class="w-6 h-6 object-contain"
              @error="onImageError"
              @load="onImageLoad"
            />
            {{ deviceType.name }}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            <p class="text-sm text-muted-foreground">{{ deviceType.description }}</p>
            
            <div v-if="deviceType.capabilities && deviceType.capabilities.length > 0">
              <h4 class="font-medium text-sm text-muted-foreground">Возможности ({{ deviceType.capabilities.length }}):</h4>
              <div class="flex flex-wrap gap-1 mt-1">
                <span v-for="cap in deviceType.capabilities" :key="cap.type || cap"
                      class="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded"
                      :title="getCapabilityDescription(cap)">
                  {{ typeof cap === 'string' ? cap : cap.type }}
                </span>
              </div>
            </div>
            
            <div v-if="deviceType.properties && deviceType.properties.length > 0">
              <h4 class="font-medium text-sm text-muted-foreground">Свойства:</h4>
              <div class="flex flex-wrap gap-1 mt-1">
                <span v-for="prop in deviceType.properties" :key="prop"
                      class="px-2 py-1 bg-muted text-muted-foreground text-xs rounded">
                  {{ prop }}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <div v-else-if="!loading" class="text-center text-muted-foreground py-8">
      Нажмите "Обновить" для получения списка типов устройств
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const API = (import.meta.env.VITE_BACKEND_URL as string) || 'https://y2m.badkiko.ru'
const data = ref<any>(null)
const loading = ref(false)
const showAddDeviceDialog = ref(false)
const selectedDeviceType = ref<any>(null)

// Функция получения иконки устройства
function getDeviceIcon(deviceType: string): string {
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
    'devices.types.thermostat.ac': 'ac',
    'devices.types.media_device': 'media_device',
    'devices.types.media_device.receiver': 'receiver',
    'devices.types.media_device.tv': 'tv',
    'devices.types.media_device.tv_box': 'tv_box',
    'devices.types.cooking': 'cooking',
    'devices.types.cooking.coffee_maker': 'coffee_maker',
    'devices.types.cooking.kettle': 'kettle',
    'devices.types.cooking.multicooker': 'multicooker',
    'devices.types.dishwasher': 'dishwasher',
    'devices.types.iron': 'iron',
    'devices.types.vacuum_cleaner': 'vacuum_cleaner',
    'devices.types.washing_machine': 'washing_machine',
    'devices.types.pet_drinking_fountain': 'pet_drinking_fountain',
    'devices.types.pet_feeder': 'pet_feeder',
    'devices.types.humidifier': 'humidifier',
    'devices.types.purifier': 'purifier',
    'devices.types.ventilation': 'ventilation',
    'devices.types.ventilation.fan': 'fan',
    'devices.types.openable': 'openable',
    'devices.types.openable.curtain': 'curtain',
    'devices.types.openable.valve': 'valve',
    'devices.types.sensor': 'sensor',
    'devices.types.sensor.button': 'button',
    'devices.types.sensor.climate': 'climate',
    'devices.types.sensor.gas': 'gas',
    'devices.types.sensor.illumination': 'illumination',
    'devices.types.sensor.motion': 'motion',
    'devices.types.sensor.open': 'open',
    'devices.types.sensor.smoke': 'smoke',
    'devices.types.sensor.vibration': 'vibration',
    'devices.types.sensor.water_leak': 'water_leak',
    'devices.types.smart_meter': 'smart_meter',
    'devices.types.smart_meter.cold_water': 'cold_water',
    'devices.types.smart_meter.electricity': 'electricity',
    'devices.types.smart_meter.gas': 'gas',
    'devices.types.smart_meter.heat': 'heat',
    'devices.types.smart_meter.hot_water': 'hot_water',
    'devices.types.camera': 'camera',
    'devices.types.other': 'other'
  }

  const iconName = iconMap[deviceType] || 'other'

  // Используем иконки из документации Яндекса
  return `https://yandex.ru/dev/dialogs/smart-home/doc/docs-assets/dev-dialogs-smart-home/rev/211f89014024eea324d5bc4927ec83767c6fac3f/ru/_images/concept.devices/${iconName}.png`
}

// Обработка успешной загрузки изображения
function onImageLoad(event: Event) {
  const img = event.target as HTMLImageElement
  const src = img.src
  
  // Извлекаем название иконки из URL
  const iconName = src.split('/').pop()?.replace('.png', '') || 'unknown'
  
  console.log(`✅ Иконка устройства успешно загружена: ${iconName}`)
}

// Обработка ошибки загрузки изображения
function onImageError(event: Event) {
  const img = event.target as HTMLImageElement
  const failedSrc = img.src
  
  // Извлекаем название иконки из URL
  const iconName = failedSrc.split('/').pop()?.replace('.png', '') || 'unknown'
  
  console.warn(`❌ Не удалось загрузить иконку устройства: ${iconName}`)
  console.log(`🔄 Заменяем на стандартную иконку "other"`)
  
  img.src = 'https://yandex.ru/dev/dialogs/smart-home/doc/docs-assets/dev-dialogs-smart-home/rev/211f89014024eea324d5bc4927ec83767c6fac3f/ru/_images/concept.devices/other.png'
}

// Получение описания capability
function getCapabilityDescription(cap: any): string {
  if (typeof cap === 'string') {
    return cap
  }
  
  if (cap.type && cap.instances && cap.instances.length > 0) {
    const instances = cap.instances.map((inst: any) => {
      if (inst.function && inst.values && inst.values.length > 0) {
        return `${inst.function}: ${inst.values.join(', ')}`
      } else if (inst.function) {
        return inst.function
      }
      return ''
    }).filter(Boolean).join('; ')
    
    return instances ? `${cap.type} (${instances})` : cap.type
  }
  
  return cap.type || 'Unknown capability'
}

// Выбор типа устройства
function selectDeviceType(deviceType: any) {
  selectedDeviceType.value = deviceType
  console.log('Выбран тип устройства:', deviceType.name)
}

// Добавление выбранного устройства
async function addSelectedDevice() {
  try {
    if (!selectedDeviceType.value) return
    
    console.log('Добавляем устройство:', selectedDeviceType.value.name)
    
    // Здесь можно добавить логику для отправки на сервер
    // await axios.post(API + '/api/devices', {
    //   type: selectedDeviceType.value.type,
    //   name: selectedDeviceType.value.name
    // })
    
    showAddDeviceDialog.value = false
    selectedDeviceType.value = null
    
    // Показываем уведомление об успехе
    console.log('✅ Устройство успешно добавлено!')
    
  } catch (error) {
    console.error('Ошибка при добавлении устройства:', error)
  }
}

async function load() {
  loading.value = true
  try {
    const { data: d } = await axios.get(API + '/api/device-types')
    data.value = d
    console.log('Загружены типы устройств:', d.types?.length || 0)
    
    // Отладочная информация для телевизора
    const tv = d.types?.find((t: any) => t.type === 'devices.types.media_device.tv')
    if (tv) {
      console.log('TV capabilities:', tv.capabilities?.length || 0)
      console.log('TV capabilities data:', tv.capabilities)
    }
  } catch (error) {
    console.error('Ошибка при загрузке типов устройств:', error)
  } finally {
    loading.value = false
  }
}

// Автоматически загружаем данные при монтировании компонента
load()
</script>
