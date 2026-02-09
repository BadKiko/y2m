<template>
  <Card class="max-w-md mx-auto">
    <CardHeader>
      <CardTitle>Авторизация</CardTitle>
    </CardHeader>
    <CardContent>
      <p v-if="ok" class="text-green-600">Успешно авторизованы!</p>
      <p v-else class="text-red-600">Ошибка авторизации</p>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const ok = ref(false)

onMounted(() => {
  const params = new URLSearchParams(location.search)
  ok.value = params.get('ok') === '1'
})
</script>
