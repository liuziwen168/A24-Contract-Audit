<template>
  <router-view />
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
userStore.initFromStorage()
</script>

<style>
#app {
  width: 100%;
  height: 100%;
}
</style>
