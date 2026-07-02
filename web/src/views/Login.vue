<template>
  <div class="login-container">
    <div class="login-left">
      <el-carousel class="login-carousel" height="calc(100vh - 120px)" indicator-position="outside" :interval="5000" autoplay>
        <el-carousel-item v-for="src in carouselImages" :key="src">
          <div class="carousel-slide">
            <img class="carousel-image" :src="src" alt="login banner" />
          </div>
        </el-carousel-item>
      </el-carousel>
    </div>
    <div class="login-right">
      <div class="login-right-content">
        <img class="login-logo" :src="logoUrl" alt="logo" />
        <div class="login-box">
          <h2>{{ $t('login.title') }}</h2>
          <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                :placeholder="$t('login.username')"
                prefix-icon="User"
                size="large"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                :placeholder="$t('login.password')"
                prefix-icon="Lock"
                size="large"
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleLogin"
                style="width: 100%"
              >
                {{ $t('login.login') }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)

const carouselImages = [
  new URL('../assets/1.jpg', import.meta.url).href,
  new URL('../assets/2.jpg', import.meta.url).href,
  new URL('../assets/3.jpg', import.meta.url).href
]

const logoUrl = new URL('../assets/logo color.png', import.meta.url).href

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.passwordRequired'), trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await authStore.login(form.username, form.password)
        ElMessage.success(t('login.loginSuccess'))
        router.push('/')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || t('login.loginFailed'))
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

.login-left {
  flex: 1 1 60%;
  min-width: 0;
  background: #f5f5f5;
  padding: 60px 30px;
}

.login-carousel {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
}

.login-carousel :deep(.el-carousel__container) {
  border-radius: 12px;
  overflow: hidden;
}

.login-carousel :deep(.el-carousel__item) {
  border-radius: 12px;
  overflow: hidden;
}

.carousel-slide {
  height: 100%;
  width: 100%;
}

.carousel-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.login-right {
  flex: 0 0 440px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 60px 30px;
  background: #f5f5f5;
  border-left: 1px solid #e4e4e4;
}

.login-right-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
}

.login-logo {
  width: 100%;
  max-width: 360px;
  height: auto;
  object-fit: contain;
}

.login-box {
  width: 100%;
  max-width: 360px;
  padding: 32px;
  border-radius: 8px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.login-box h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

@media (max-width: 900px) {
  .login-container {
    flex-direction: column;
  }

  .login-left {
    flex: 0 0 40vh;
    padding: 50px 30px;
  }

  .login-right {
    flex: 1 1 auto;
    width: 100%;
    border-left: none;
    border-top: 1px solid #ebeef5;
    padding: 50px 30px;
  }
}
</style>
