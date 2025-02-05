import request from '@/utils/request'
import type { LoginForm, RegisterForm, AuthResponse } from '@/types/api'

export const login = (data: LoginForm) => {
  return request.post<AuthResponse>('/auth/login', data)
}

export const register = (data: RegisterForm) => {
  return request.post<AuthResponse>('/auth/register', data)
}

export const logout = () => {
  return request.post('/auth/logout')
}

export const refreshToken = () => {
  return request.post<AuthResponse>('/auth/refresh')
}

export const getUserInfo = () => {
  return request.get('/auth/user')
}

export const updateUserInfo = (data: Partial<User>) => {
  return request.put<User>('/auth/user', data)
}

export const changePassword = (data: {
  oldPassword: string
  newPassword: string
}) => {
  return request.post('/auth/change-password', data)
} 