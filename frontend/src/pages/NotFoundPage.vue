<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center gap-6 px-4">
    <h1 class="text-8xl font-black tracking-tighter">404</h1>
    <p class="text-xl font-semibold text-center max-w-md">
      Page not found
    </p>
    <button
      class="px-6 py-3 border-[3px] border-black font-bold shadow-neo-lg hover:shadow-neo-lg-hover transition-shadow"
      @click="router.push('/documents')"
    >
      Back to documents
    </button>
  </div>
</template>
