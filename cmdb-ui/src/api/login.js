import api from './index'
import { axios } from '@/utils/request'
/**
 * login func
 * parameter: {
 *     username: '',
 *     password: '',
 *     remember_me: true,
 *     captcha: '12345'
 * }
 * @param parameter
 * @returns {*}
 */
export function login(data, auth_type) {
  if (auth_type) {
    localStorage.setItem('ops_auth_type', auth_type)
    window.location.href = `/api/${auth_type.toLowerCase()}/login`
  } else {
    return axios({
      url: api.Login,
      method: 'POST',
      data: data
    })
  }
}

export function getSmsCaptcha(parameter) {
  return axios({
    url: api.SendSms,
    method: 'post',
    data: parameter
  })
}

export function getInfo() {
  return axios({
    url: api.UserInfo,
    method: 'get',
    headers: {
      'Content-Type': 'application/json;charset=UTF-8'
    }
  })
}

export function logout() {
  const auth_type = localStorage.getItem('ops_auth_type')
  // keep theme preference across logout (Vue.ls keys carry the pro__ namespace prefix)
  const keepKeys = ['pro__THEME_MODE', 'pro__DEFAULT_THEME']
  const kept = {}
  keepKeys.forEach(k => {
    const v = localStorage.getItem(k)
    if (v !== null) kept[k] = v
  })
  localStorage.clear()
  Object.keys(kept).forEach(k => localStorage.setItem(k, kept[k]))
  return axios({
    url: auth_type ? `/${auth_type.toLowerCase()}/logout` : api.Logout,
    method: auth_type ? 'get' : 'post',
    headers: {
      'Content-Type': 'application/json;charset=UTF-8'
    }
  })
}

/**
 * get user 2step code open?
 * @param parameter {*}
 */
export function get2step(parameter) {
  return axios({
    url: api.twoStepCode,
    method: 'post',
    data: parameter
  })
}

export function getAllUsers(params) {
  return axios({
    url: '/v1/acl/users',
    method: 'GET',
    params
  })
}
