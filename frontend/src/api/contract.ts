 import http from './client'
 import type { ApiResponse, Contract, ContractDetail, ContractListParams, PaginatedData } from '@/types'

 export function uploadContract(file: File, name?: string): Promise<ApiResponse<{ contractId: number; contractFileId: number; contractStatus: string }>> {
   const formData = new FormData()
   formData.append('file', file)
   if (name) formData.append('name', name)
   return http.post('/contracts', formData, {
     headers: { 'Content-Type': 'multipart/form-data' },
   }).then((r) => r.data)
 }

 export function getContractList(params?: ContractListParams): Promise<ApiResponse<PaginatedData<Contract>>> {
   return http.get('/contracts', { params }).then((r) => r.data)
 }

 export function getContractDetail(contractId: number): Promise<ApiResponse<ContractDetail>> {
   return http.get(`/contracts/${contractId}`).then((r) => r.data)
 }

 export function deleteContract(contractId: number): Promise<ApiResponse<{ contractId: number; contractStatus: string }>> {
   return http.delete(`/contracts/${contractId}`).then((r) => r.data)
 }
