//app.js
App({
  onLaunch() {
    console.log('小程序启动')
    
    // 检查API连接
    this.checkApiConnection()
  },

  checkApiConnection() {
    wx.request({
      url: 'http://localhost:5000/health',
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
    apiBaseUrl: 'http://localhost:5000',
    userInfo: null
  }
})
