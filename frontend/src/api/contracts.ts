import request from './request'
import type { PageResult, Contract } from '@/types'

export interface ContractListParams {
  page?: number
  pageSize?: number
  ownerId?: number
  contractStatus?: string
  contractType?: string
}

export async function uploadContract(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<{ contractId: number; contractFileId: number; status: string }> {
  const form = new FormData()
  form.append('file', file)
  const res: any = await request.post('/contracts', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
  return res.data
}

export async function listContracts(params?: ContractListParams): Promise<PageResult<Contract>> {
  const res: any = await request.get('/contracts', { params })
  return res.data
}

export async function getContract(contractId: number): Promise<Contract> {
  const res: any = await request.get(`/contracts/${contractId}`)
  return res.data
}

export function downloadContract(contractId: number, fileId: number) {
  return request.get(`/contracts/${contractId}/files/${fileId}/download`, {
    responseType: 'blob',
  })
}

export async function deleteContract(contractId: number): Promise<null> {
  const res: any = await request.delete(`/contracts/${contractId}`)
  return res.data
}
