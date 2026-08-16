// src/stores/user.ts
import { defineStore } from 'pinia'
import { login as apiLogin, getInfo as apiGetInfo, logout as apiLogout, getAllUsers } from '@/api/login'
import { getEmployeeByUid, getEmployeeList } from '@/api/employee'
import { getAllDepartmentList } from '@/api/company'
import { getAuthDataEnable } from '@/api/auth'
import { TOKEN_KEY } from '@/utils/request'
import type { Role, UserInfoResult, AuthEnableResponse } from '@/types'

interface UserState {
  token: string
  name: string
  avatar: string
  uid: number
  rid: number
  username: string
  roles: Role
  info: Partial<UserInfoResult>
  allUsers: unknown[]
  allEmployees: unknown[]
  allDepartments: unknown[]
  authEnable: AuthEnableResponse | null
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: '',
    name: '',
    avatar: '',
    uid: 0,
    rid: 0,
    username: '',
    roles: {},
    info: {},
    allUsers: [],
    allEmployees: [],
    allDepartments: [],
    authEnable: null,
  }),
  getters: {
    isAuthed: (state) => !!state.token,
  },
  actions: {
    async login(userInfo: { username: string; password: string; remember_me?: boolean }) {
      const res = await apiLogin(userInfo)
      this.token = res.token
      localStorage.setItem(TOKEN_KEY, res.token)
    },
    async getInfo() {
      const res = await apiGetInfo()
      const result = res.result
      this.roles = result.role
      this.info = result
      this.name = result.name
      this.avatar = result.avatar || ''
      this.uid = result.uid
      this.rid = result.rid
      this.username = result.username
      try {
        const emp = await getEmployeeByUid(result.uid)
        this.info = { ...this.info, ...emp }
      } catch {
        // 员工信息为可选增强，失败不阻断
      }
      return res
    },
    async logout() {
      try {
        await apiLogout()
      } catch {
        // 登出失败也继续清理本地状态
      }
      this.token = ''
      localStorage.removeItem(TOKEN_KEY)
    },
    async fetchAuthDataEnable() {
      this.authEnable = await getAuthDataEnable()
    },
    async loadAllUsers() {
      const res = (await getAllUsers({ page_size: 9999 })) as { users: unknown[] }
      this.allUsers = res.users
    },
    async loadAllEmployees() {
      const res = (await getEmployeeList({ page_size: 99999 })) as { data_list: unknown[] }
      this.allEmployees = res.data_list
    },
    async loadAllDepartments() {
      this.allDepartments = await getAllDepartmentList({ is_tree: 0 })
    },
  },
  persist: {
    key: 'pro__user',
    pick: ['name', 'avatar', 'uid', 'rid', 'username', 'roles', 'info'],
  },
})
