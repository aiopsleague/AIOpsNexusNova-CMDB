<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({ username: '', password: '' })

async function onSubmit() {
  if (!form.username || !form.password) {
    message.error('Please enter username and password')
    return
  }
  loading.value = true
  try {
    await userStore.login({ username: form.username, password: form.password })
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch {
    // 错误提示由 request 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login">
    <a-card title="Login" style="width: 360px">
      <a-form layout="vertical" @submit.prevent="onSubmit">
        <a-form-item>
          <a-input v-model:value="form.username" size="large" placeholder="Username">
            <template #prefix><UserOutlined /></template>
          </a-input>
        </a-form-item>
        <a-form-item>
          <a-input-password v-model:value="form.password" size="large" placeholder="Password">
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" block :loading="loading">
            Login
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<style scoped>
.login {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
