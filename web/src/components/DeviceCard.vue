<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface Device {
  id: number
  name: string
  yandex_type: string
  adb_host?: string
  adb_port?: number
}

interface Props {
  device: Device
  deletable?: boolean
  deleting?: boolean
  showIcon?: boolean
  iconUrl?: string
  showNetworkInfo?: boolean
  editable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  deletable: true,
  deleting: false,
  showIcon: false,
  iconUrl: '',
  showNetworkInfo: false,
  editable: true,
})

const emit = defineEmits<{
  (e: 'delete', deviceId: number): void
  (e: 'edit', device: Device): void
}>()

function onDelete() {
  emit('delete', props.device.id)
}

function onEdit() {
  emit('edit', props.device)
}
</script>

<template>
  <Card class="p-4">
    <CardContent class="p-0">
      <div class="grid grid-cols-2 gap-3 items-center">
        <!-- Top left: icon -->
        <div class="flex items-center justify-center">
          <img v-if="showIcon && iconUrl" :src="iconUrl" alt="icon" class="w-12 h-12 object-contain" />
        </div>
        <!-- Top right: text -->
        <div class="min-w-0">
          <CardTitle class="text-base leading-tight truncate">{{ device.name }}</CardTitle>
          <CardDescription class="truncate">{{ device.yandex_type }}</CardDescription>
          <div v-if="showNetworkInfo" class="text-xs text-muted-foreground mt-1 truncate">
            <template v-if="device.adb_host">
              ADB: {{ device.adb_host }}:{{ device.adb_port }}
            </template>
            <template v-else>
              Только MQTT
            </template>
          </div>
        </div>

        <!-- Bottom left: Edit -->
        <div>
          <Button v-if="editable" size="sm" variant="outline" class="w-full" @click="onEdit">Редактировать</Button>
        </div>
        <!-- Bottom right: Delete -->
        <div>
          <Button v-if="deletable" size="sm" variant="destructive" class="w-full" :disabled="deleting" @click="onDelete">
            {{ deleting ? 'Удаление...' : 'Удалить' }}
          </Button>
        </div>
      </div>
    </CardContent>
  </Card>
</template>


