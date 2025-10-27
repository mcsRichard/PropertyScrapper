//pages/detail/detail.js
const api = require('../../utils/api.js')

Page({
  data: {
    property: null,
    loading: true
  },

  onLoad(options) {
    if (options.id) {
      this.loadPropertyDetail(options.id)
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      })
    }
  },

  /**
   * 加载房产详情
   */
  loadPropertyDetail(id) {
    this.setData({ loading: true })
    
    api.getPropertyDetail(id)
      .then(res => {
        if (res.success && res.data) {
          this.setData({
            property: res.data,
            loading: false
          })
          
          // 设置页面标题
          wx.setNavigationBarTitle({
            title: res.data.title || '房产详情'
          })
        }
      })
      .catch(err => {
        console.error('加载详情失败:', err)
        wx.showToast({
          title: '加载失败',
          icon: 'none'
        })
        this.setData({ loading: false })
      })
  },

  /**
   * 查看原始链接
   */
  viewOriginalLink() {
    const url = this.data.property.url
    if (url) {
      wx.showModal({
        title: '打开原网页',
        content: '是否在浏览器中打开此房产的原始页面？',
        success: (res) => {
          if (res.confirm) {
            // 复制链接到剪贴板
            wx.setClipboardData({
              data: url,
              success: () => {
                wx.showToast({
                  title: '链接已复制',
                  icon: 'success'
                })
              }
            })
          }
        }
      })
    }
  },

  /**
   * 分享房产
   */
  onShareAppMessage() {
    return {
      title: this.data.property?.title || '房产分享',
      path: `/pages/detail/detail?id=${this.data.property?.id}`
    }
  }
})
