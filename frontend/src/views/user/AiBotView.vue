<template>
  <div class="ai-bot">
    <div v-if="messages.length === 0" class="welcome">
      <div class="welcome-glow"></div>
      <div class="welcome-icon">
        <svg viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="22" stroke="currentColor" stroke-width="2.5"/>
          <path d="M16 20c0-1.5 1-3 3-3h10c2 0 3 1.5 3 3v1c0 2-2 4-4 4H20c-2 0-4-2-4-4v-1z" fill="currentColor" opacity=".35"/>
          <circle cx="18" cy="20" r="1.2" fill="currentColor"/>
          <circle cx="23" cy="20" r="1.2" fill="currentColor"/>
          <circle cx="28" cy="20" r="1.2" fill="currentColor"/>
          <path d="M16 30s2 5 8 5 8-5 8-5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
      <h1>你好，我是 AILEX</h1>
      <p>你的合同智能助手。我可以帮你分析条款、解释风险、提供修改建议。<br/>试试下面的问题，或者直接输入你想了解的合同问题。</p>
      <div class="quick-asks">
        <button v-for="q in quickQuestions" :key="q" class="quick-chip" @click="ask(q)">{{ q }}</button>
        <button class="quick-chip refresh-chip" @click="shuffleQuestions">
          <el-icon><Refresh /></el-icon> 换一批
        </button>
      </div>
    </div>
    <div v-else class="chat-area" ref="chatRef">
      <div class="chat-header">
        <div class="chat-header-left">
          <div class="bot-avatar-sm">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="11" stroke="currentColor" stroke-width="2"/><path d="M8 10c0-.8.5-1.5 1.5-1.5h5c1 0 1.5.7 1.5 1.5v.5c0 1-1 2-2 2h-4c-1 0-2-1-2-2v-.5z" fill="currentColor" opacity=".3"/><circle cx="9" cy="10" r=".6" fill="currentColor"/><circle cx="11.5" cy="10" r=".6" fill="currentColor"/><circle cx="14" cy="10" r=".6" fill="currentColor"/></svg>
          </div>
          <div>
            <strong>AILEX 合同助手</strong>
            <small>在线 · 随时为你解答合同问题</small>
          </div>
        </div>
        <button class="new-chat-btn" @click="clearChat"><el-icon><Plus /></el-icon> 新对话</button>
      </div>
      <div class="messages">
        <div v-for="(msg, i) in messages" :key="i" :class="['msg-row', msg.role]">
          <div v-if="msg.role === 'assistant'" class="bot-avatar-xs">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="11" stroke="currentColor" stroke-width="2"/><path d="M8 10c0-.8.5-1.5 1.5-1.5h5c1 0 1.5.7 1.5 1.5v.5c0 1-1 2-2 2h-4c-1 0-2-1-2-2v-.5z" fill="currentColor" opacity=".3"/><circle cx="9" cy="10" r=".6" fill="currentColor"/><circle cx="11.5" cy="10" r=".6" fill="currentColor"/><circle cx="14" cy="10" r=".6" fill="currentColor"/></svg>
          </div>
          <div class="msg-bubble" :class="msg.role">
            <div class="msg-text">{{ msg.content }}</div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>
        <div v-if="typing" class="msg-row assistant">
          <div class="bot-avatar-xs">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="11" stroke="currentColor" stroke-width="2"/><path d="M8 10c0-.8.5-1.5 1.5-1.5h5c1 0 1.5.7 1.5 1.5v.5c0 1-1 2-2 2h-4c-1 0-2-1-2-2v-.5z" fill="currentColor" opacity=".3"/><circle cx="9" cy="10" r=".6" fill="currentColor"/><circle cx="11.5" cy="10" r=".6" fill="currentColor"/><circle cx="14" cy="10" r=".6" fill="currentColor"/></svg>
          </div>
          <div class="msg-bubble assistant typing">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="input-bar" :class="{ 'has-chat': messages.length > 0 }">
      <div class="input-wrapper">
        <textarea ref="inputRef" v-model="input" class="chat-input" placeholder="输入你的合同问题，例如：违约责任条款怎么写？" rows="1" @keydown.enter.exact.prevent="send" @input="autoResize"></textarea>
        <button class="send-btn" :disabled="!input.trim() || typing" @click="send">
          <el-icon><Promotion /></el-icon>
        </button>
      </div>
      <p class="input-hint">按 Enter 发送，AI 回答仅供参考，不构成法律意见</p>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { Refresh, Plus, Promotion } from '@element-plus/icons-vue'
import { sendChatMessage } from '@/api/chat'
import type { ChatHistoryItem } from '@/api/chat'

interface Message {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const allQuestions = [
  '合同中的违约金条款一般怎么约定？',
  '什么是无限责任条款？有什么风险？',
  '保密协议的核心条款有哪些？',
  '采购合同应该包含哪些必要条款？',
  '如何判断合同中的争议解决条款是否合理？',
  '劳动合同中竞业限制条款的注意事项',
  '合同金额大小写不一致怎么办？',
  '什么情况下可以单方解除合同？',
  '服务外包合同的知识产权条款怎么约定？',
  '合同中不可抗力条款的作用是什么？',
  '验收标准条款应该怎么写才明确？',
  '合同到期自动续约条款有风险吗？',
]

const messages = ref<Message[]>([])
const input = ref('')
const typing = ref(false)
const chatRef = ref<HTMLElement>()
const inputRef = ref<HTMLTextAreaElement>()
const quickQuestions = ref<string[]>([])

function shuffleQuestions() {
  const shuffled = [...allQuestions].sort(() => Math.random() - 0.5)
  quickQuestions.value = shuffled.slice(0, 4)
}

function now() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const answers: Record<string, string> = {
  default: '这是一个很好的问题。\n\n根据《中华人民共和国民法典》相关规定及司法实践，建议你在合同审核中重点关注：\n\n1. **条款合法性**：确保不违反法律强制性规定\n2. **权利义务对等性**：检查双方权利义务是否均衡\n3. **风险可控性**：评估可能带来的商业风险\n4. **表述明确性**：避免模糊、歧义的用语\n\n如需详细分析，建议上传合同后使用 AI 审核功能，系统会自动识别风险条款并给出修改建议。',
}

function getAnswer(question: string): string {
  const lower = question.toLowerCase()
  if (lower.includes('违约金') || lower.includes('违约')) {
    return '关于违约金条款，根据《民法典》第585条：\n\n当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。\n\n**关键注意事项**：\n- 违约金不应超过实际损失的30%，过高的违约金法院可能不予支持\n- 建议明确约定违约情形、计算方式和支付期限\n- 同时约定"违约金不足以弥补损失的，守约方仍可主张赔偿"'
  }
  if (lower.includes('无限责任') || lower.includes('责任条款')) {
    return '无限责任条款是合同审核中需要高度警惕的高风险条款。\n\n**风险分析**：\n- 无限责任意味着责任方需承担全部损失，没有赔偿上限\n- 可能导致企业面临远超合同金额的赔偿风险\n\n**修改建议**：\n1. 设定责任上限（通常为合同金额1-3倍）\n2. 明确排除间接损失、利润损失\n3. 约定免责情形（不可抗力、对方过错等）'
  }
  if (lower.includes('保密') || lower.includes('nda')) {
    return '保密协议（NDA）核心条款：\n\n**必备条款**：\n1. 保密信息定义 —— 哪些信息属于保密范围\n2. 保密义务 —— 接收方的保密责任和使用限制\n3. 保密期限 —— 通常为合同期内+终止后2-5年\n4. 例外情形 —— 已公开信息、依法披露等\n5. 违约责任 —— 明确泄密的法律后果'
  }
  if (lower.includes('采购') || lower.includes('必备条款')) {
    return '规范采购合同应包含以下核心条款：\n\n1. 合同主体 —— 双方准确名称、地址\n2. 标的物描述 —— 产品名称、规格、数量、质量标准\n3. 价款与支付 —— 单价、总价、付款方式与期限\n4. 交付与验收 —— 交货时间、地点、验收标准\n5. 质保与售后 —— 质保期限、服务内容\n6. 违约责任 —— 延迟交货、质量不合格等处理方式\n7. 争议解决 —— 协商、仲裁或诉讼的管辖约定'
  }
  if (lower.includes('争议解决') || lower.includes('管辖')) {
    return '争议解决条款影响维权成本和效率：\n\n**常见方式**：\n- 协商 —— 成本最低，但执行力弱\n- 仲裁 —— 一裁终局、保密性好\n- 诉讼 —— 程序公开、可上诉\n\n**注意事项**：\n- 管辖地约定在对方所在地会大幅增加维权成本\n- 建议约定在己方所在地或合同履行地\n- 仲裁机构应明确全称，避免约定不明'
  }
  if (lower.includes('竞业限制') || lower.includes('劳动')) {
    return '竞业限制条款受法律严格限制：\n\n**法律要求（劳动合同法第23-24条）**：\n- 仅适用于高管、高级技术人员和负有保密义务的人员\n- 期限不得超过2年\n- 须支付经济补偿\n- 范围应合理限定\n\n**风险点**：\n- 未支付补偿金可能被认定无效\n- 范围过宽可能被法院调整'
  }
  return answers.default
}

function ask(question: string) {
  input.value = question
  send()
}

async function send() {
  const text = input.value.trim()
  if (!text || typing.value) return
  messages.value.push({ role: 'user', content: text, time: now() })
  input.value = ''
  typing.value = true
  await nextTick()
  scrollBottom()
  try {
    const history: ChatHistoryItem[] = messages.value.slice(0, -1).map(m => ({
      role: m.role,
      content: m.content,
    }))
    const res = await sendChatMessage(text, history.length > 0 ? history : undefined)
    typing.value = false
    messages.value.push({ role: 'assistant', content: res.reply, time: now() })
  } catch {
    typing.value = false
    messages.value.push({ role: 'assistant', content: '抱歉，AI 服务暂时不可用，请稍后重试。', time: now() })
  }
  await nextTick()
  scrollBottom()
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function scrollBottom() {
  const el = chatRef.value
  if (!el) return
  const msgs = el.querySelector('.messages')
  if (msgs) msgs.scrollTop = msgs.scrollHeight
}

function clearChat() {
  messages.value = []
  shuffleQuestions()
}

onMounted(() => { shuffleQuestions() })
</script>

<style scoped>
.ai-bot {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - 40px);
  max-width: 860px;
  margin: 0 auto;
}

/* ---- Welcome ---- */
.welcome {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
}
.welcome-glow {
  position: absolute;
  top: 15%;
  width: 360px;
  height: 360px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(26,111,196,.08) 0, transparent 70%);
  pointer-events: none;
}
.welcome-icon {
  width: 80px;
  height: 80px;
  color: #1a6fc4;
  margin-bottom: 20px;
  position: relative;
}
.welcome-icon svg { width: 100%; height: 100%; }
.welcome h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #1f2a3a;
  letter-spacing: .5px;
}
.welcome p {
  margin: 12px 0 28px;
  color: #6b7a90;
  font-size: 15px;
  line-height: 1.7;
  max-width: 480px;
}
.quick-asks {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  max-width: 560px;
}
.quick-chip {
  padding: 9px 18px;
  border: 1px solid #dce3ed;
  border-radius: 24px;
  background: #fff;
  color: #344a6a;
  font-size: 13px;
  cursor: pointer;
  transition: all .2s;
  white-space: nowrap;
}
.quick-chip:hover {
  border-color: #1a6fc4;
  color: #1a6fc4;
  background: #f0f6ff;
}
.refresh-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  border-style: dashed;
  color: #8899b0;
}
.refresh-chip:hover { color: #1a6fc4; }

/* ---- Chat ---- */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #edf0f5;
  background: #fff;
  border-radius: 14px 14px 0 0;
  flex-shrink: 0;
}
.chat-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.bot-avatar-sm {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: #e8f3ff;
  color: #1a6fc4;
  display: grid;
  place-items: center;
}
.bot-avatar-sm svg { width: 22px; height: 22px; }
.chat-header-left strong {
  display: block;
  font-size: 15px;
  color: #1f2a3a;
}
.chat-header-left small {
  font-size: 12px;
  color: #8c98a8;
}
.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  border: 1px solid #e0e5ec;
  border-radius: 8px;
  background: #fff;
  color: #5a6b80;
  font-size: 13px;
  cursor: pointer;
  transition: all .2s;
}
.new-chat-btn:hover { border-color: #1a6fc4; color: #1a6fc4; }
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.msg-row {
  display: flex;
  gap: 10px;
  max-width: 82%;
}
.msg-row.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.msg-row.assistant {
  align-self: flex-start;
}
.bot-avatar-xs {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: #e8f3ff;
  color: #1a6fc4;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.bot-avatar-xs svg { width: 18px; height: 18px; }
.msg-bubble {
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.65;
  position: relative;
}
.msg-bubble.user {
  background: linear-gradient(135deg, #1a6fc4, #2584d9);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg-bubble.assistant {
  background: #fff;
  color: #334158;
  border: 1px solid #edf0f5;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,.03);
}
.msg-text {
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-time {
  margin-top: 6px;
  font-size: 11px;
  opacity: .55;
  text-align: right;
}
.msg-bubble.user .msg-time { color: rgba(255,255,255,.7); }
.msg-bubble.assistant .msg-time { color: #98a4b4; }

/* ---- Typing ---- */
.msg-bubble.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 18px;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #bcc7d6;
  animation: bounce 1.3s infinite both;
}
.dot:nth-child(2) { animation-delay: .18s; }
.dot:nth-child(3) { animation-delay: .36s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* ---- Input ---- */
.input-bar {
  padding: 16px 20px 12px;
  flex-shrink: 0;
}
.input-bar.has-chat {
  background: #fff;
  border-top: 1px solid #edf0f5;
  border-radius: 0 0 14px 14px;
}
.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 8px 8px 16px;
  border: 2px solid #e0e5ec;
  border-radius: 14px;
  background: #fff;
  transition: border-color .2s;
}
.input-wrapper:focus-within {
  border-color: #1a6fc4;
  box-shadow: 0 0 0 3px rgba(26,111,196,.08);
}
.chat-input {
  flex: 1;
  border: 0;
  outline: 0;
  resize: none;
  font-size: 14px;
  color: #334158;
  line-height: 1.5;
  font-family: inherit;
  max-height: 120px;
  background: transparent;
}
.chat-input::placeholder { color: #b0bcc8; }
.send-btn {
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 10px;
  background: #1a6fc4;
  color: #fff;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  transition: all .2s;
}
.send-btn:hover:not(:disabled) { background: #155d9e; transform: scale(1.04); }
.send-btn:disabled { background: #c8d6e4; cursor: not-allowed; }
.input-hint {
  margin: 8px 0 0;
  text-align: center;
  font-size: 11px;
  color: #b0bcc8;
}
.messages::-webkit-scrollbar { width: 5px; }
.messages::-webkit-scrollbar-track { background: transparent; }
.messages::-webkit-scrollbar-thumb { background: #d0d8e2; border-radius: 10px; }
</style>
