//pages/detail/detail.js
const api = require('../../utils/api.js')

Page({
  data: {
    property: null,
    loading: true,
    currentImageIndex: 0,
    customerService: {
      wechatId: '',
      qrUrl: ''
    }
  },

  onLoad(options) {
    this.setCustomerServiceInfo()
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
              description: property.description,
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
})
