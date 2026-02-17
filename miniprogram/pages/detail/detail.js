//pages/detail/detail.js
const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')

Page({
  data: {
    property: null,
    loading: true,
    currentImageIndex: 0,
    customerService: {
      wechatId: '',
      qrUrl: ''
    },
    isLoggedIn: false,
    userInfo: null,
    contactStats: null,
    contactLoading: false
  },

  onLoad(options) {
    this.setCustomerServiceInfo()
    this.syncUserState()
    if (options.id) {
      this.loadPropertyDetail(options.id)
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      })
    }
  },

  onShow() {
    this.syncUserState(true)
  },

  /**
   * 设置客服信息
   */
  setCustomerServiceInfo() {
    const app = getApp()
    const wechatId = app?.globalData?.customerServiceWechat || ''
    const qrUrl = app?.globalData?.customerServiceQrUrl || ''
    this.setData({
      customerService: {
        wechatId,
        qrUrl
      }
    })
  },

  syncUserState(needRemoteRefresh = false) {
    const app = getApp()
    let userInfo = app?.globalData?.userInfo || null
    let contactStats = app?.globalData?.contactStats || null
    let token = app?.globalData?.authToken || null

    try {
      if (!userInfo) {
        userInfo = wx.getStorageSync('userInfo')
      }
      if (!contactStats) {
        contactStats = wx.getStorageSync('contactStats')
      }
      if (!token) {
        token = wx.getStorageSync('authToken')
      }
    } catch (err) {
      console.warn('读取用户信息失败', err)
    }

    this.setData({
      isLoggedIn: !!token,
      userInfo: userInfo || null,
      contactStats: contactStats || null
    })

    if (needRemoteRefresh && token) {
      auth.fetchUserProfile()
        .then(() => {
          const refreshedStats = getApp()?.globalData?.contactStats
          const refreshedUser = getApp()?.globalData?.userInfo
          this.setData({
            userInfo: refreshedUser || userInfo || null,
            contactStats: refreshedStats || contactStats || null
          })
        })
        .catch((err) => {
          console.log('刷新用户信息失败', err)
        })
    }
  },

  updateContactStats(stats) {
    const app = getApp()
    if (app && typeof app.updateContactStats === 'function') {
      app.updateContactStats(stats)
    }
    this.setData({
      contactStats: stats
    })
  },

  onLoginTap() {
    if (this.data.contactLoading) {
      return
    }
    this.setData({ contactLoading: true })
    
    // 立即登录（不等待用户信息，避免 code 过期）
    // 用户信息可以在登录成功后通过其他方式补充
    console.log('[AUTH] 用户点击登录，立即获取 code 并登录...')
    auth.loginWithWeChat(0, null)
      .then(() => {
        wx.showToast({
          title: '登录成功',
          icon: 'success'
        })
        this.syncUserState()
      })
      .catch((err) => {
        console.error('登录失败', err)
        wx.showToast({
          title: '登录失败，请重试',
          icon: 'none'
        })
      })
      .finally(() => {
        this.setData({ contactLoading: false })
      })
  },

  /**
   * 加载房产详情
   */
  loadPropertyDetail(id) {
    this.setData({ loading: true })
    
    api.getPropertyDetail(id)
      .then(res => {
        if (res.success && res.data) {
          const property = res.data
          console.log('[DETAIL] 原始property数据:', property)
          console.log('[DETAIL] property.images:', property.images)
          
          // 规范化图片数组：优先使用后端 images，否则退化为单图 image_url
          let imageUrls = []
          if (Array.isArray(property.images) && property.images.length > 0) {
            imageUrls = property.images
              .filter(img => {
                const hasUrl = !!(img.image_url || img.url)
                if (!hasUrl) {
                  console.warn('[DETAIL] 图片对象缺少URL:', img)
                }
                return hasUrl
              })
              .sort((a, b) => {
                // 主图优先，然后按order_index排序
                const aPrimary = a.is_primary ? 1 : 0
                const bPrimary = b.is_primary ? 1 : 0
                if (aPrimary !== bPrimary) {
                  return bPrimary - aPrimary
                }
                return (a.order_index || 0) - (b.order_index || 0)
              })
              .map(img => {
                // 优先使用image_url，其次url，最后source_url
                return img.image_url || img.url || img.source_url
              })
              .filter(url => {
                // 过滤：必须存在、必须以http开头、不能是空字符串
                const isValid = url && typeof url === 'string' && url.trim().startsWith('http')
                if (!isValid) {
                  console.warn('[DETAIL] 过滤掉无效图片URL:', url)
                }
                return isValid
              })
          } else if (property.image_url) {
            imageUrls = [property.image_url]
          }
          
          // 前端去重：移除重复URL
          const seen = new Set()
          imageUrls = imageUrls.filter(url => {
            if (seen.has(url)) {
              console.warn('[DETAIL] 前端去重：发现重复URL', url)
              return false
            }
            seen.add(url)
            return true
          })
          
          console.log('[DETAIL] 处理后的imageUrls:', imageUrls)

          // 手动合并所有字段（小程序不支持扩展运算符）
          this.setData({
            property: {
              id: property.id,
              title: property.title,
              price: property.price,
              price_numeric: property.price_numeric,
              area: property.area,
              bedrooms: property.bedrooms,
              bathrooms: property.bathrooms,
              property_type: property.property_type,
              listing_type: property.listing_type,
              location: property.location,
              postcode: property.postcode,
              description_chinese: property.description_chinese,
              url: property.url,
              image_url: property.image_url,
              images: property.images,
              imageUrls: imageUrls,
              created_at: property.created_at,
              updated_at: property.updated_at
            },
            currentImageIndex: 0,  // 重置到第一张
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

  handleContactAgent() {
    if (this.data.contactLoading) {
      return
    }
    if (!this.data.property || !this.data.property.id) {
      wx.showToast({
        title: '房源信息未加载完成',
        icon: 'none'
      })
      return
    }
    if (!this.data.property.url) {
      wx.showToast({
        title: '暂无原始链接',
        icon: 'none'
      })
      return
    }
    if (!this.data.isLoggedIn) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      this.onLoginTap()
      return
    }
    if (this.data.contactStats && this.data.contactStats.remaining <= 0) {
      wx.showToast({
        title: '今日联系次数已用完',
        icon: 'none'
      })
      return
    }

    this.setData({ contactLoading: true })
    api.requestContactLink(this.data.property.id)
      .then((res) => {
        if (res.success && res.data) {
          if (res.data.contact_stats) {
            this.updateContactStats(res.data.contact_stats)
          }
          if (res.data.contact_url) {
            this.openContactLink(res.data.contact_url)
          } else {
            wx.showToast({
              title: '暂无原始链接',
              icon: 'none'
            })
          }
        } else {
          wx.showToast({
            title: res.error || '获取链接失败',
            icon: 'none'
          })
        }
      })
      .catch((err) => {
        console.error('获取联系链接失败', err)
        const message = (err && err.error) ? err.error : '获取链接失败'
        wx.showToast({
          title: message,
          icon: 'none'
        })
      })
      .finally(() => {
        this.setData({ contactLoading: false })
      })
  },

  openContactLink(targetUrl) {
    if (!targetUrl) {
      wx.showToast({
        title: '暂无原始链接',
        icon: 'none'
      })
      return
    }
    const encodedUrl = encodeURIComponent(targetUrl)
    wx.navigateTo({
      url: `/pages/webview/webview?url=${encodedUrl}`,
      fail: () => {
        wx.setClipboardData({
          data: targetUrl,
          success: () => {
            wx.showModal({
              title: '已复制链接',
              content: '系统暂无法直接打开该网页，链接已复制，可在浏览器中打开。',
              showCancel: false
            })
          }
        })
      }
    })
  },

  /**
   * 预览图片
   */
  previewImage(e) {
    const index = e.currentTarget.dataset.index || 0
    const urls = this.data.property?.imageUrls || []
    if (!urls.length) return
    wx.previewImage({
      current: urls[index],
      urls
    })
  },

  /**
   * 图片加载失败处理
   */
  onImageError(e) {
    const index = e.currentTarget.dataset.index || 0
    console.error('[DETAIL] 图片加载失败:', {
      index,
      url: this.data.property?.imageUrls?.[index]
    })
  },

  /**
   * Swiper切换事件
   */
  onSwiperChange(e) {
    const current = e.detail.current || 0
    this.setData({
      currentImageIndex: current
    })
    console.log('[DETAIL] Swiper切换到第', current + 1, '张')
  },

  /**
   * 上一张图片
   */
  onPrevImage() {
    const imageUrls = this.data.property?.imageUrls || []
    if (imageUrls.length <= 1) return
    
    let newIndex = this.data.currentImageIndex - 1
    if (newIndex < 0) {
      newIndex = imageUrls.length - 1  // 循环到最后一张
    }
    
    // 通过更新currentImageIndex来触发swiper切换
    this.setData({
      currentImageIndex: newIndex
    })
  },

  /**
   * 下一张图片
   */
  onNextImage() {
    const imageUrls = this.data.property?.imageUrls || []
    if (imageUrls.length <= 1) return
    
    let newIndex = this.data.currentImageIndex + 1
    if (newIndex >= imageUrls.length) {
      newIndex = 0  // 循环到第一张
    }
    
    // 通过更新currentImageIndex来触发swiper切换
    this.setData({
      currentImageIndex: newIndex
    })
  },

  /**
   * 分享房产
   */
  onShareAppMessage() {
    return {
      title: this.data.property?.title || '房产分享',
      path: `/pages/detail/detail?id=${this.data.property?.id}`
    }
  },

  /**
   * 预览客服二维码
   */
  previewCustomerServiceQr() {
    const qrUrl = this.data.customerService.qrUrl
    if (!qrUrl) {
      wx.showToast({
        title: '暂无客服二维码',
        icon: 'none'
      })
      return
    }
    wx.previewImage({
      urls: [qrUrl]
    })
  },

  /**
   * 复制客服微信号
   */
  copyCustomerWechat() {
    const wechatId = this.data.customerService.wechatId
    if (!wechatId) {
      wx.showToast({
        title: '暂无客服微信号',
        icon: 'none'
      })
      return
    }
    wx.setClipboardData({
      data: wechatId,
      success: () => {
        wx.showToast({
          title: '微信号已复制',
          icon: 'success'
        })
      }
    })
  },

  /**
   * 分享功能
   */
  onShareAppMessage() {
    const property = this.data.property
    if (property && property.id) {
      return {
        title: property.title || '英国房产详情',
        path: `/pages/detail/detail?id=${property.id}`,
        imageUrl: property.image_url || ''
      }
    }
    return {
      title: '英国房产信息查询',
      path: '/pages/index/index'
    }
  },

  /**
   * 分享到朋友圈
   */
  onShareTimeline() {
    const property = this.data.property
    if (property && property.id) {
      return {
        title: property.title || '英国房产详情',
        query: `id=${property.id}`
      }
    }
    return {
      title: '英国房产信息查询 - UK Property'
    }
  }
})
