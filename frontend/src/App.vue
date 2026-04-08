<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(async () => {
  if (userStore.isLoggedIn()) {
    try {
      await userStore.fetchUserInfo()
    } catch {
      userStore.logout()
    }
  }
})
</script>
