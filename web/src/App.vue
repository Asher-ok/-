<template>
  <el-config-provider :locale="elementLocale">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'

const { locale } = useI18n()

const elementLocale = computed(() => (locale.value === 'zh' ? zhCn : en))
</script>

<style>
html {
  font-size: 16px;
}
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Microsoft YaHei', sans-serif;
  color: #0f172a;
  background-color: var(--main-bg);
  font-size: var(--el-font-size-base);
  line-height: 1.6;
}

#app {
  min-height: 100vh;
}

.el-card {
  border-radius: var(--border-radius-md);
  border: 1px solid #e6eaf2;
  box-shadow: var(--box-shadow-sm);
}

.el-button {
  border-radius: var(--border-radius-sm);
  font-weight: 500;
  font-size: var(--el-font-size-base);
}
.el-button.el-button--default:not(.is-text):not(.is-link) {
  background-color: #64748b;
  border-color: #64748b;
  color: #ffffff;
}
.el-button.el-button--primary:not(.is-text):not(.is-link) {
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #ffffff;
}
.el-button.el-button--success:not(.is-text):not(.is-link) {
  background-color: var(--el-color-success);
  border-color: var(--el-color-success);
  color: #ffffff;
}
.el-button.el-button--warning:not(.is-text):not(.is-link) {
  background-color: var(--el-color-warning);
  border-color: var(--el-color-warning);
  color: #ffffff;
}
.el-button.el-button--danger:not(.is-text):not(.is-link) {
  background-color: var(--el-color-danger);
  border-color: var(--el-color-danger);
  color: #ffffff;
}
.el-button.el-button--info:not(.is-text):not(.is-link) {
  background-color: var(--el-color-info);
  border-color: var(--el-color-info);
  color: #ffffff;
}
.el-button.el-button--default:not(.is-text):not(.is-link):hover {
  background-color: #475569;
  border-color: #475569;
  color: #ffffff;
}
.el-button.el-button--primary:not(.is-text):not(.is-link):hover {
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #ffffff;
}
.el-button.el-button--success:not(.is-text):not(.is-link):hover {
  background-color: var(--el-color-success);
  border-color: var(--el-color-success);
  color: #ffffff;
}
.el-button.el-button--warning:not(.is-text):not(.is-link):hover {
  background-color: var(--el-color-warning);
  border-color: var(--el-color-warning);
  color: #ffffff;
}
.el-button.el-button--danger:not(.is-text):not(.is-link):hover {
  background-color: var(--el-color-danger);
  border-color: var(--el-color-danger);
  color: #ffffff;
}
.el-button.el-button--info:not(.is-text):not(.is-link):hover {
  background-color: var(--el-color-info);
  border-color: var(--el-color-info);
  color: #ffffff;
}
.el-button:focus-visible {
  box-shadow: 0 0 0 0.28rem rgba(87, 152, 243, 0.25);
}
.el-button.is-text:not(.is-disabled):hover {
  background-color: rgba(15, 23, 42, 0.05);
  border-radius: var(--border-radius-sm);
}

.el-table {
  border-radius: var(--border-radius-md);
  overflow: hidden;
  border: 1px solid #e6eaf2;
}
.el-table .cell {
  font-size: var(--el-font-size-base);
}
.el-table__header .cell {
  font-size: var(--el-font-size-base);
  font-weight: 600;
  background-color: #ffffff;
  color: #334155;
}
.el-table--striped .el-table__row--striped {
  background-color: #f7faff;
}
th.el-table__cell,
td.el-table__cell {
  padding: 22px 0;
  overflow: hidden;
}

.el-table .cell {
  white-space: nowrap;
  text-overflow: clip;
}

.el-table__body-wrapper {
  overflow-x: auto;
}

.el-table__header-wrapper {
  overflow-x: auto;
}

th.op-col-header .cell,
td.op-col .cell {
  padding-left: 5px;
  padding-right: 5px;
}

.el-dialog {
  border-radius: var(--border-radius-md);
  border: 1px solid #e6eaf2;
}

.el-form-item {
  margin-bottom: 24px;
}
.el-form-item__label {
  font-size: var(--el-font-size-base);
  color: #334155;
}
.el-dialog .el-form-item__label {
  white-space: nowrap;
}
.el-input__inner,
.el-input__wrapper input,
.el-input__wrapper {
  font-size: var(--el-font-size-base);
  border-radius: var(--border-radius-sm);
}
.el-input__wrapper {
  height: var(--el-component-size);
  min-height: var(--el-component-size);
  padding: 8px 12px;
}
.el-input__wrapper.is-focus,
.el-select .is-focus .el-select__wrapper,
.el-date-editor.is-active,
.el-date-editor .el-input__wrapper.is-focus {
  box-shadow: 0 0 0 0.28rem rgba(106, 168, 255, 0.25);
  border-color: var(--el-color-primary);
}

.el-select .el-select__selected-value,
.el-select .el-select__placeholder,
.el-select-dropdown__item {
  font-size: var(--el-font-size-base);
}
.el-tag {
  font-size: var(--el-font-size-base);
}
.el-table .el-tag {
  display: inline-flex;
  align-items: center;
  height: 40px;
  padding: 0 14px;
}
.el-table .el-tag.el-tag--small {
  height: 38px;
  padding: 0 12px;
}

/* 统一间距 */
.el-card__header {
  padding: 22px 24px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
  font-size: var(--el-font-size-base);
  background-color: #ffffff;
}

.el-card__body {
  padding: 24px;
}

.card-header > span {
  font-size: var(--el-font-size-large);
  font-weight: 700;
  color: #0f172a;
}

.el-button {
  min-height: var(--el-component-size);
  padding: 9px 17px;
}
.el-button--small {
  min-height: calc(var(--el-component-size) - 4px);
  padding: 8px 15px;
  font-size: var(--el-font-size-base);
}
.el-button--large {
  min-height: calc(var(--el-component-size) + 8px);
  padding: 11px 21px;
  font-size: var(--el-font-size-base);
}

.el-select .el-select__wrapper,
.el-date-editor .el-input__wrapper,
.el-input-number .el-input__wrapper {
  height: var(--el-component-size);
  min-height: var(--el-component-size);
  padding: 8px 12px;
}

.el-link.clickable-text {
  color: #0f172a;
  text-decoration: underline;
}
.el-link.clickable-text:hover {
  color: #0f172a;
}

.el-dialog__footer .el-button--default:not(.is-text):not(.is-link),
.el-dialog__footer .el-button--primary:not(.is-text):not(.is-link),
.el-dialog__footer .el-button--success:not(.is-text):not(.is-link),
.el-dialog__footer .el-button--warning:not(.is-text):not(.is-link),
.el-dialog__footer .el-button--danger:not(.is-text):not(.is-link),
.el-dialog__footer .el-button--info:not(.is-text):not(.is-link) {
  color: #ffffff;
}
.el-dialog__footer .el-button--default:not(.is-text):not(.is-link) {
  background-color: #64748b;
  border-color: #64748b;
}
.el-dialog__footer .el-button--primary:not(.is-text):not(.is-link) {
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}
.el-dialog__footer .el-button--success:not(.is-text):not(.is-link) {
  background-color: var(--el-color-success);
  border-color: var(--el-color-success);
}
.el-dialog__footer .el-button--warning:not(.is-text):not(.is-link) {
  background-color: var(--el-color-warning);
  border-color: var(--el-color-warning);
}
.el-dialog__footer .el-button--danger:not(.is-text):not(.is-link) {
  background-color: var(--el-color-danger);
  border-color: var(--el-color-danger);
}
.el-dialog__footer .el-button--info:not(.is-text):not(.is-link) {
  background-color: var(--el-color-info);
  border-color: var(--el-color-info);
}

.el-form .el-button--default:not(.is-text):not(.is-link):not(.is-plain),
.el-form .el-button--primary:not(.is-text):not(.is-link):not(.is-plain),
.el-form .el-button--success:not(.is-text):not(.is-link):not(.is-plain),
.el-form .el-button--warning:not(.is-text):not(.is-link):not(.is-plain),
.el-form .el-button--danger:not(.is-text):not(.is-link):not(.is-plain),
.el-form .el-button--info:not(.is-text):not(.is-link):not(.is-plain) {
  color: #ffffff;
}
.el-form .el-button--default:not(.is-text):not(.is-link):not(.is-plain) {
  background-color: #64748b;
  border-color: #64748b;
}
.el-form .el-button--primary:not(.is-text):not(.is-link):not(.is-plain) {
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}
.el-form .el-button--success:not(.is-text):not(.is-link):not(.is-plain) {
  background-color: var(--el-color-success);
  border-color: var(--el-color-success);
}
.el-form .el-button--warning:not(.is-text):not(.is-link):not(.is-plain) {
  background-color: var(--el-color-warning);
  border-color: var(--el-color-warning);
}
.el-form .el-button--danger:not(.is-text):not(.is-link):not(.is-plain) {
  background-color: var(--el-color-danger);
  border-color: var(--el-color-danger);
}
.el-form .el-button--info:not(.is-text):not(.is-link):not(.is-plain) {
  background-color: var(--el-color-info);
  border-color: var(--el-color-info);
}
</style>
