//app.js
App({
  onLaunch() {
    console.log('小程序启动')
    this.restoreAuthFromStorage()
    this.checkApiConnection()
  },

  restoreAuthFromStorage() {
    try {
      const token = wx.getStorageSync('authToken')
      const userInfo = wx.getStorageSync('userInfo')
      const contactStats = wx.getStorageSync('contactStats')
      if (token) {
        this.globalData.authToken = token
      }
      if (userInfo) {
        this.globalData.userInfo = userInfo
      }
      if (contactStats) {
        this.globalData.contactStats = contactStats
      }
    } catch (err) {
      console.warn('恢复登录状态失败', err)
    }
  },

  setAuthData(token, user, contactStats) {
    if (token) {
      this.globalData.authToken = token
      wx.setStorageSync('authToken', token)
    }
    if (user) {
      this.globalData.userInfo = user
      wx.setStorageSync('userInfo', user)
    }
    if (contactStats) {
      this.updateContactStats(contactStats)
    }
  },

  updateContactStats(stats) {
    if (!stats) return
    this.globalData.contactStats = stats
    wx.setStorageSync('contactStats', stats)
  },

  clearAuthData() {
    this.globalData.authToken = null
    this.globalData.userInfo = null
    this.globalData.contactStats = null
    try {
      wx.removeStorageSync('authToken')
      wx.removeStorageSync('userInfo')
      wx.removeStorageSync('contactStats')
    } catch (err) {
      console.warn('清除本地登录状态失败', err)
    }
  },

  checkApiConnection() {
    const baseUrl = this.globalData.apiBaseUrl || 'http://localhost:5000'
    wx.request({
      url: `${baseUrl}/health`,
      method: 'GET',
      success: (res) => {
        console.log('API连接成功:', res.data)
      },
      fail: (err) => {
        console.error('API连接失败:', err)
        wx.showToast({
          title: '网络连接失败',
          icon: 'none'
        })
      }
    })
  },

  globalData: {
    //apiBaseUrl: 'http://localhost:5000',//本地
    //apiBaseUrl: 'https://1383789184-lebyqyy34m.ap-shanghai.tencentscf.com',//临时域名（已弃用）
    apiBaseUrl: 'https://api.ukliving.cn',//正式域名
    authToken: null,
    userInfo: null,
    contactStats: null,
    // 客服微信号与二维码图片地址（请根据实际情况填写）
    customerServiceWechat: '',  // 例如：'uk-property-support'
    customerServiceQrUrl: '/image/contact.png'    // 例如：'/image/customer-service-qr.png' 或线上HTTPS地址
  }
})
