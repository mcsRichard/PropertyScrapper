const api = require('./api.js')

function loginWithWeChat(retryCount = 0, userProfile = null) {
  const MAX_RETRIES = 1  // 最多重试 1 次
  return new Promise((resolve, reject) => {
    // 先获取 code，立即登录（不等待用户信息，避免 code 过期）
    wx.login({
      success: (loginRes) => {
        if (!loginRes.code) {
          reject(new Error('获取登录凭证失败'))
          return
        }

        const code = loginRes.code
        console.log(`[AUTH] 获取到 code（重试次数: ${retryCount}），立即登录...`)

        // 直接使用 code 登录，userProfile 可选（如果传入则使用，否则为空对象）
        // 用户信息可以在登录成功后通过其他方式补充
        api.login(code, userProfile || {})
          .then((res) => {
            if (res.success && res.data) {
              const app = getApp()
              const token = res.data.token
              const user = normalizeUser(res.data.user, userProfile || {})
              const contactStats = res.data.contact_stats
              if (app && typeof app.setAuthData === 'function') {
                app.setAuthData(token, user, contactStats)
              }
              resolve(res.data)
            } else {
              // 处理特定错误：code 过期或已使用
              const errorMsg = res.error || '登录失败'
              if ((errorMsg.includes('invalid code') || errorMsg.includes('code 已过期') || errorMsg.includes('code 已被使用')) && retryCount < MAX_RETRIES) {
                console.warn('[AUTH] code 无效，尝试重新获取...')
                return loginWithWeChat(retryCount + 1, userProfile)
              }
              reject(new Error(errorMsg))
            }
          })
          .catch((err) => {
            const errMsg = err.message || err.error || String(err)
            if ((errMsg.includes('invalid code') || errMsg.includes('code 已过期') || errMsg.includes('code 已被使用')) && retryCount < MAX_RETRIES) {
              console.warn('[AUTH] code 无效，尝试重新获取...')
              return loginWithWeChat(retryCount + 1, userProfile)
            }
            reject(err)
          })
      },
      fail: (err) => {
        console.error('[AUTH] wx.login 失败:', err)
        reject(new Error('获取登录凭证失败: ' + (err.errMsg || String(err))))
      }
    })
  })
}

/**
 * 在用户点击事件中调用，直接登录（不获取用户信息，避免 getUserProfile 同步上下文问题）
 * 用户信息可以在登录成功后通过其他方式补充
 */
function loginWithWeChatAndProfile() {
  // 直接使用 loginWithWeChat，不获取用户信息
  // 这样可以避免 wx.getUserProfile 必须在同步上下文中调用的问题
  // 用户信息可以在登录成功后通过其他方式补充
  console.log('[AUTH] 用户点击登录，直接登录（不获取用户信息）')
  return loginWithWeChat(0, null)
}

function fetchUserProfile() {
  const app = getApp()
  const token = app?.globalData?.authToken || wx.getStorageSync('authToken')
  if (!token) {
    return Promise.resolve(null)
  }

  return api.getCurrentUser().then((res) => {
    if (res.success && res.data) {
      const user = normalizeUser(res.data.user)
      const contactStats = res.data.contact_stats
      if (app && typeof app.setAuthData === 'function') {
        app.setAuthData(token, user, contactStats)
      }
      return res.data
    }
    return null
  })
}

function normalizeUser(user = {}, fallbackProfile = {}) {
  const normalized = {
    ...fallbackProfile,
    ...user
  }
  if (!normalized.nickName && normalized.nickname) {
    normalized.nickName = normalized.nickname
  }
  if (!normalized.avatarUrl && normalized.avatar_url) {
    normalized.avatarUrl = normalized.avatar_url
  }
  return normalized
}

function requestUserProfile() {
  return new Promise((resolve, reject) => {
    if (wx.getUserProfile) {
      wx.getUserProfile({
        desc: '用于完善会员资料',
        success: (res) => resolve(res.userInfo || {}),
        fail: (err) => {
          wx.showToast({
            title: '需要授权登录',
            icon: 'none'
          })
          reject(err)
        }
      })
    } else {
      // 旧版本兼容
      wx.getUserInfo({
        success: (res) => resolve(res.userInfo || {}),
        fail: (err) => {
          wx.showToast({
            title: '未获取到用户信息',
            icon: 'none'
          })
          reject(err)
        }
      })
    }
  })
}


function logout() {
  const app = getApp()
  if (app && typeof app.clearAuthData === 'function') {
    app.clearAuthData()
  }
  return Promise.resolve()
}

module.exports = {
  loginWithWeChat,  // 直接登录（不获取用户信息，适合自动登录）
  loginWithWeChatAndProfile,  // 先获取用户信息再登录（必须在用户点击事件中调用）
  fetchUserProfile,
  logout
}






