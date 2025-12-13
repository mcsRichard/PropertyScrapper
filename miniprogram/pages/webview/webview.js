Page({
  data: {
    targetUrl: ''
  },

  onLoad(options) {
    if (options && options.url) {
      const decoded = decodeURIComponent(options.url)
      this.setData({
        targetUrl: decoded
      })
    } else {
      wx.showToast({
        title: '缺少链接参数',
        icon: 'none'
      })
    }
  }
})




