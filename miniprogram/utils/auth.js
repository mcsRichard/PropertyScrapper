const api = require('./api.js')

function loginWithWeChat() {
  return new Promise((resolve, reject) => {
    // 先获取用户信息（需要用户点击）
    requestUserProfile()
      .then((userProfile) => {
        // 获取用户信息成功后，再调用 login
        wx.login({
          success: (loginRes) => {
            if (!loginRes.code) {
              reject(new Error('获取登录凭证失败'))
              return
            }

            // 使用 code 和 userProfile 进行登录
            api.login(loginRes.code, userProfile)
              .then((res) => {
                if (res.success && res.data) {
                  const app = getApp()
                  const token = res.data.token
                  const user = normalizeUser(res.data.user, userProfile)
                  const contactStats = res.data.contact_stats
                  if (app && typeof app.setAuthData === 'function') {
                    app.setAuthData(token, user, contactStats)
                  }
                  resolve(res.data)
                } else {
                  reject(new Error(res.error || '登录失败'))
                }
              })
              .catch(reject)
          },
          fail: (err) => reject(err)
        })
      })
      .catch(reject)
  })
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

module.exports = {
  loginWithWeChat,
  fetchUserProfile
}




