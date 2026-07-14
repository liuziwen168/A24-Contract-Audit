 <template>
   <router-view />
 </template>
 
 <script setup lang="ts">
 </script>
 
 <style>
 :root {
   --color-primary: #4361ee;
   --color-primary-light: #eef0ff;
   --color-success: #2ecc71;
   --color-warning: #f39c12;
   --color-danger: #e74c3c;
   --color-info: #95a5a6;
   --color-bg: #f0f2f5;
   --color-bg-card: #ffffff;
   --color-text: #1a1a2e;
   --color-text-secondary: #6b7280;
   --color-border: #e5e7eb;
   --sidebar-bg: #0f172a;
   --sidebar-text: #94a3b8;
   --sidebar-active: #4361ee;
   --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
   --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
   --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
   --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
   --radius-sm: 6px;
   --radius-md: 8px;
   --radius-lg: 12px;
   --radius-xl: 16px;
 }
 
 * {
   margin: 0;
   padding: 0;
   box-sizing: border-box;
 }
 
 body {
   font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
   background-color: var(--color-bg);
   color: var(--color-text);
   -webkit-font-smoothing: antialiased;
   -moz-osx-font-smoothing: grayscale;
 }
 
 /* Element Plus overrides for theme consistency */
 .el-card {
   border: none !important;
   border-radius: var(--radius-lg) !important;
   box-shadow: var(--shadow-sm) !important;
   transition: box-shadow 0.25s ease, transform 0.2s ease;
 }
 .el-card:hover {
   box-shadow: var(--shadow-md) !important;
 }
 .el-card__header {
   padding: 16px 20px !important;
   border-bottom: 1px solid var(--color-border) !important;
   font-weight: 600 !important;
   font-size: 15px !important;
 }
 .el-card__body {
   padding: 20px !important;
 }
 
 .el-table {
   border-radius: var(--radius-md);
   overflow: hidden;
 }
 .el-table th.el-table__cell {
   background-color: #f8fafc !important;
   font-weight: 600 !important;
   color: var(--color-text) !important;
 }
 .el-table--striped .el-table__body tr.el-table__row--striped td {
   background-color: #f8fafc !important;
 }
 .el-table__body tr:hover > td {
   background-color: var(--color-primary-light) !important;
 }
 
 .el-button--primary {
   --el-button-bg-color: var(--color-primary);
   --el-button-border-color: var(--color-primary);
   --el-button-hover-bg-color: #3651d4;
   --el-button-hover-border-color: #3651d4;
 }
 
 .el-tag--danger { --el-tag-bg-color: #fef2f2; --el-tag-text-color: #dc2626; --el-tag-border-color: #fecaca; }
 .el-tag--warning { --el-tag-bg-color: #fffbeb; --el-tag-text-color: #d97706; --el-tag-border-color: #fde68a; }
 .el-tag--success { --el-tag-bg-color: #f0fdf4; --el-tag-text-color: #16a34a; --el-tag-border-color: #bbf7d0; }
 .el-tag--info { --el-tag-bg-color: #f3f4f6; --el-tag-text-color: #6b7280; --el-tag-border-color: #d1d5db; }
 
 .el-dialog {
   border-radius: var(--radius-xl) !important;
 }
 .el-dialog__header {
   padding: 20px 24px 0 !important;
   font-weight: 600 !important;
 }
 .el-dialog__body {
   padding: 20px 24px !important;
 }
 .el-dialog__footer {
   padding: 0 24px 20px !important;
 }
 
 .el-message {
   border-radius: var(--radius-md) !important;
 }
 
 /* Scrollbar styling */
 ::-webkit-scrollbar {
   width: 6px;
   height: 6px;
 }
 ::-webkit-scrollbar-track {
   background: transparent;
 }
 ::-webkit-scrollbar-thumb {
   background: #cbd5e1;
   border-radius: 3px;
 }
 ::-webkit-scrollbar-thumb:hover {
   background: #94a3b8;
 }
 
 /* Fade transition */
 .fade-enter-active, .fade-leave-active {
   transition: opacity 0.25s ease;
 }
 .fade-enter-from, .fade-leave-to {
   opacity: 0;
 }
 </style>

 <script setup lang="ts">
 </script>

 <style>
 * {
   margin: 0;
   padding: 0;
   box-sizing: border-box;
 }
 body {
   font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
   background-color: #f5f7fa;
   color: #303133;
 }
 </style>
