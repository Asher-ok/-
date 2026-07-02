<template>
  <div class="home-safety-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('homeSafety.categories') }}</el-divider>
      <div v-for="(cat, key) in categories" :key="key" class="category-row">
        <el-form-item :label="cat.label" :label-width="formLabelWidth">
          <el-checkbox v-model="form.categories[key].checked">{{ $t('homeSafety.checked') }}</el-checkbox>
          <el-input v-model="form.categories[key].notes" type="textarea" :rows="2" :placeholder="$t('homeSafety.notes')" style="margin-top: 8px; max-width: 400px" />
        </el-form-item>
      </div>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'HomeSafetyEditor' })
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  doc: { type: Object, required: true },
  customerId: { type: String, required: true }
})

const CATEGORY_KEYS = ['entrance', 'general', 'meds_devices', 'living', 'bath_bed', 'violence', 'electrical', 'hazards', 'outdoor']

const formLabelWidth = '160px'

const categories = computed(() => ({
  entrance: { label: t('homeSafety.entrance'), key: 'entrance' },
  general: { label: t('homeSafety.general'), key: 'general' },
  meds_devices: { label: t('homeSafety.medsDevices'), key: 'meds_devices' },
  living: { label: t('homeSafety.living'), key: 'living' },
  bath_bed: { label: t('homeSafety.bathBed'), key: 'bath_bed' },
  violence: { label: t('homeSafety.violence'), key: 'violence' },
  electrical: { label: t('homeSafety.electrical'), key: 'electrical' },
  hazards: { label: t('homeSafety.hazards'), key: 'hazards' },
  outdoor: { label: t('homeSafety.outdoor'), key: 'outdoor' }
}))

const formRef = ref(null)
const emptyCategories = () =>
  Object.fromEntries(CATEGORY_KEYS.map((k) => [k, { checked: false, notes: '' }]))

const form = ref({
  name: '',
  categories: emptyCategories()
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object' && doc.form_data.categories) {
      const cats = doc.form_data.categories
      form.value.categories = emptyCategories()
      for (const k of CATEGORY_KEYS) {
        if (cats[k]) {
          form.value.categories[k] = {
            checked: cats[k].checked ?? false,
            notes: cats[k].notes ?? ''
          }
        }
      }
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    categories: form.value.categories
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>

<style scoped>
.category-row { margin-bottom: 12px; }
</style>
