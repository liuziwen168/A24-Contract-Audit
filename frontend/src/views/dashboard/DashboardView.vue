 <template>
   <div class="dashboard">
     <div class="welcome-section">
       <div class="welcome-text">
         <h2>欢迎回来，{{ authStore.username }}</h2>
         <p>合同智能审核系统运行中</p>
       </div>
       <div class="welcome-time">{{ currentTime }}</div>
     </div>
 
     <div class="stat-cards">
       <div v-for="stat in statCards" :key="stat.label" class="stat-card" :style="{ background: stat.gradient }">
         <div class="stat-icon"><el-icon :size="22"><component :is="stat.iconComp" /></el-icon></div>
         <div class="stat-body">
           <div class="stat-value">{{ stat.value }}</div>
           <div class="stat-label">{{ stat.label }}</div>
         </div>
       </div>
     </div>
 
     <div class="chart-row">
       <el-card shadow="never" class="chart-card">
         <template #header><div class="chart-header"><el-icon><PieChart /></el-icon><span>风险分布</span></div></template>
         <div ref="riskChartRef" style="height:300px;width:100%"></div>
       </el-card>
       <el-card shadow="never" class="chart-card">
         <template #header><div class="chart-header"><el-icon><Histogram /></el-icon><span>合同类型分布</span></div></template>
         <div ref="typeChartRef" style="height:300px;width:100%"></div>
       </el-card>
     </div>
 
     <el-card shadow="never" class="chart-card">
       <template #header><div class="chart-header"><el-icon><DataLine /></el-icon><span>审核趋势</span></div></template>
       <div ref="trendChartRef" style="height:300px;width:100%"></div>
     </el-card>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted, nextTick, onUnmounted } from 'vue'
 import { useAuthStore } from '@/stores/auth'
 import * as echarts from 'echarts'
 import { getDashboardSummary } from '@/api/dashboard'
 import { CONTRACT_TYPE_LABELS } from '@/types'
 import { PieChart, Histogram, DataLine } from '@element-plus/icons-vue'
 import { Document, CircleCheck, Clock, WarningFilled } from '@element-plus/icons-vue'
 
 const authStore = useAuthStore()
 const riskChartRef = ref<HTMLDivElement>()
 const typeChartRef = ref<HTMLDivElement>()
 const trendChartRef = ref<HTMLDivElement>()
 const currentTime = ref('')
 let timeTimer: ReturnType<typeof setInterval> | null = null
 
 const statCards = ref([
   { label: '审核总量', value: 0, gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', iconComp: Document },
   { label: '已完成', value: 0, gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', iconComp: CircleCheck },
   { label: '待处理', value: 0, gradient: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)', iconComp: Clock },
   { label: '失败', value: 0, gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', iconComp: WarningFilled },
 ])
 
 onMounted(() => {
   updateTime()
   timeTimer = setInterval(updateTime, 1000)
   loadDashboard()
 })
 onUnmounted(() => { if (timeTimer) clearInterval(timeTimer) })
 
 function updateTime() {
   currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
 }
 
 async function loadDashboard() {
   try {
     const res = await getDashboardSummary()
     const d = res.data
     statCards.value[0].value = d.totalReviews
     statCards.value[1].value = d.completedReviews
     statCards.value[2].value = d.pendingReviews
     statCards.value[3].value = d.failedReviews
     nextTick(() => {
       initRiskChart(d.riskDistribution)
       initTypeChart(d.contractTypeDistribution)
       initTrendChart(d.reviewTrend)
     })
   } catch { /* noop */ }
 }
 
 const chartColors = ['#4361ee', '#f72585', '#4cc9f0', '#f8961e', '#7209b7', '#06d6a0']
 
 function initRiskChart(data: { riskType: string; count: number }[]) {
   if (!riskChartRef.value) return
   const chart = echarts.init(riskChartRef.value)
   const isNoData = data.length === 0
   chart.setOption({
     tooltip: { trigger: 'item' },
     legend: { bottom: 0, textStyle: { fontSize: 12, color: '#6b7280' } },
     series: [{
       type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: true,
       itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
       label: { show: true, formatter: '{b}: {c}', fontSize: 12, color: '#6b7280' },
       color: chartColors,
       data: isNoData
         ? [{ name: '暂无数据', value: 1, itemStyle: { color: '#e5e7eb' } }]
         : data.map((d, i) => ({ name: d.riskType, value: d.count, itemStyle: { color: chartColors[i % chartColors.length] } })),
     }],
   })
 }
 
 function initTypeChart(data: { contractType: string; count: number }[]) {
   if (!typeChartRef.value) return
   const chart = echarts.init(typeChartRef.value)
   chart.setOption({
     grid: { left: 50, right: 20, top: 20, bottom: 30 },
     tooltip: { trigger: 'axis' },
     xAxis: { type: 'category', data: data.map((d) => CONTRACT_TYPE_LABELS[d.contractType] || d.contractType) },
     yAxis: { type: 'value' },
     series: [{
       type: 'bar', barWidth: 32,
       data: data.map((d) => d.count),
       itemStyle: { borderRadius: [6, 6, 0, 0], color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
         { offset: 0, color: '#4361ee' }, { offset: 1, color: '#6366f1' },
       ]) },
     }],
   })
 }
 
 function initTrendChart(data: { date: string; count: number }[]) {
   if (!trendChartRef.value) return
   const chart = echarts.init(trendChartRef.value)
   chart.setOption({
     grid: { left: 50, right: 20, top: 20, bottom: 30 },
     tooltip: { trigger: 'axis' },
     xAxis: { type: 'category', data: data.map((d) => d.date) },
     yAxis: { type: 'value' },
     series: [{
       type: 'line', smooth: true, data: data.map((d) => d.count),
       symbol: 'circle', symbolSize: 6,
       lineStyle: { color: '#4361ee', width: 2.5 },
       itemStyle: { color: '#4361ee' },
       areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
         { offset: 0, color: 'rgba(67, 97, 238, 0.3)' }, { offset: 1, color: 'rgba(67, 97, 238, 0.02)' },
       ]) },
     }],
   })
 }
 </script>
 
 <style scoped>
 .dashboard { max-width: 1200px; margin: 0 auto; }
 
 .welcome-section {
   display: flex; justify-content: space-between; align-items: flex-end;
   margin-bottom: 24px;
 }
 .welcome-text h2 { font-size: 22px; font-weight: 700; color: var(--color-text); margin-bottom: 4px; }
 .welcome-text p { font-size: 14px; color: var(--color-text-secondary); }
 .welcome-time {
   font-size: 14px; color: var(--color-text-secondary);
   font-variant-numeric: tabular-nums;
   padding: 6px 14px; background: rgba(255,255,255,0.7);
   border-radius: 8px; border: 1px solid var(--color-border);
 }
 
 .stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
 .stat-card {
   border-radius: 16px; padding: 20px 24px; display: flex; align-items: center; gap: 16px;
   color: #fff; transition: transform 0.2s, box-shadow 0.2s;
   box-shadow: 0 4px 14px rgba(0,0,0,0.08); position: relative; overflow: hidden;
 }
 .stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
 .stat-icon {
   width: 48px; height: 48px; border-radius: 12px; background: rgba(255,255,255,0.2);
   display: flex; align-items: center; justify-content: center; flex-shrink: 0;
   backdrop-filter: blur(4px);
 }
 .stat-body { flex: 1; }
 .stat-value { font-size: 32px; font-weight: 700; line-height: 1.1; }
 .stat-label { font-size: 13px; opacity: 0.8; margin-top: 2px; }
 
 .chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
 .chart-header { display: flex; align-items: center; gap: 8px; color: var(--color-text); font-size: 15px; }
 </style>
