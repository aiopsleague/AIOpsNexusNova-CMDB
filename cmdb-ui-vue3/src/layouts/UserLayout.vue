<script setup lang="ts"></script>

<template>
  <div class="user-layout">
    <router-view />
  </div>
</template>

<style scoped>
.user-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
</style>
