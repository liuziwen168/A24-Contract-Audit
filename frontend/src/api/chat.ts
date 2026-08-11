import request from './request'
import type { ApiResponse } from '@/types'

export interface ChatResponse {
  reply: string
  role: string
}

export interface ChatHistoryItem {
  role: string
  content: string
}

export async function sendChatMessage(
  message: string,
  history?: ChatHistoryItem[]
): Promise<ChatResponse> {
  const res = await request.post<ApiResponse<ChatResponse>>('/ai/chat', {
    message,
    history: history || null,
  })
  return res.data
}