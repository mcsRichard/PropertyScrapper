//pages/index/index.js
const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')

Page({
  data: {
    properties: [],
    page: 1,
    limit: 20,
    total: 0,
    loading: false,
    hasMore: true,
    showFilter: false,
    filterExpanded: true, // 筛选器是否展开
    filters: {
      minPrice: '',
      maxPrice: '',
      propertyType: '',
      bedrooms: ''
    },
    listingType: 'for_rent', // 默认显示出租房产
    searchKeyword: '', // 搜索关键词
    aiFilters: null, // AI解析的筛选条件
    aiFiltersText: '', // AI筛选条件显示文本
    // 筛选选项
    bedroomOptions: [
      { label: '不限', value: '' },
      { label: '1室', value: 1 },
      { label: '2室', value: 2 },
      { label: '3室', value: 3 },
      { label: '4室', value: 4 },
      { label: '5室+', value: 5 }
    ],
    typeOptions: [
      { label: '不限', value: '' },
      { label: '公寓', value: 'flat' },
      { label: '别墅', value: 'house' },
      { label: '其他', value: 'other' }
    ],
    listingTypeOptions: [
      { label: '出售', value: 'for_sale' },
      { label: '出租', value: 'for_rent' }
    ],
    currentBedroom: '不限',
    currentType: '不限',
    currentPrice: '不限',
    priceRange: [0, 4000], // 默认出租房产的月租金范围
    priceDisplay: '不限',
    pricePresetSelected: -1,
    // 排序选项
    sortOptions: [
      { label: '默认', value: '', sortBy: null, sortOrder: 'desc' },
      { label: '价格从低到高', value: 'price_asc', sortBy: 'price', sortOrder: 'asc' },
      { label: '价格从高到低', value: 'price_desc', sortBy: 'price', sortOrder: 'desc' },
      { label: '最新发布', value: 'created_desc', sortBy: 'created_at', sortOrder: 'desc' },
      { label: '最早发布', value: 'created_asc', sortBy: 'created_at', sortOrder: 'asc' }
    ],
    currentSort: '默认',
    // 出售房产的价格预设（总价）
    forSalePricePresets: [
      { label: '£30万以下', minPrice: 0, maxPrice: 300000 },
      { label: '£30-50万', minPrice: 300000, maxPrice: 500000 },
      { label: '£50-100万', minPrice: 500000, maxPrice: 1000000 },
      { label: '£100-200万', minPrice: 1000000, maxPrice: 2000000 },
      { label: '£200万以上', minPrice: 2000000, maxPrice: 999999999 }
    ],
    // 出租房产的价格预设（月租金）
    forRentPricePresets: [
      { label: '£800/月以下', minPrice: 0, maxPrice: 800 },
      { label: '£800-1500/月', minPrice: 800, maxPrice: 1500 },
      { label: '£1500-2500/月', minPrice: 1500, maxPrice: 2500 },
      { label: '£2500-4000/月', minPrice: 2500, maxPrice: 4000 },
      { label: '£4000/月以上', minPrice: 4000, maxPrice: 999999 }
    ],
    pricePresets: [], // 将根据listingType动态设置
    priceOptions: [{ label: '不限', value: '', minPrice: null, maxPrice: null }], // picker选项（包含"不限"），初始化为默认值
    currentPrice: '不限', // 当前选择的价格范围
    isLoggedIn: false,
    userInfo: null,
    contactStats: null,
    loginInProgress: false
  },

  onLoad() {
    // 初始化价格预设
    this.updatePricePresets()
    this.loadProperties()
    this.syncUserState()
  },

  onReady() {
    // 页面渲染完成，确保priceOptions已初始化
    if (!this.data.priceOptions || this.data.priceOptions.length <= 1) {
      console.log('[PRICE] onReady时priceOptions未正确初始化，重新初始化')
      this.updatePricePresets()
    }
  },

  onShow() {
    this.syncUserState(true)
  },

  onReachBottom() {
    // 触底加载更多
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  onPullDownRefresh() {
    // 下拉刷新
    this.data.page = 1
    this.data.hasMore = true
    this.loadProperties(true)
    this.syncUserState(true)
  },

  /**
   * 构建筛选参数（含排序）。AI 激活时与 aiFilters 合并为 AND。
   */
  buildFilters() {
    const filters = {
      minPrice: this.data.filters.minPrice || null,
      maxPrice: this.data.filters.maxPrice || null,
      propertyType: this.data.filters.propertyType || null,
      bedrooms: this.data.filters.bedrooms || null,
      listingType: this.data.listingType || 'for_rent'
    }
    const currentSortOption = this.data.sortOptions.find(opt => opt.label === this.data.currentSort)
    if (currentSortOption && currentSortOption.sortBy) {
      filters.sortBy = currentSortOption.sortBy
      filters.sortOrder = currentSortOption.sortOrder
    }
    return filters
  },

  /**
   * AI 激活时合并：location 来自 aiFilters，其余手动有则用手动，否则用 AI。
   */
  buildMergedFilters() {
    const manual = this.buildFilters()
    const ai = this.data.aiFilters || {}
    const loc = ai.postcode_prefixes || ai.location || null
    const has = (v) => v !== null && v !== undefined && v !== ''
    return {
      location: loc,
      listingType: manual.listingType,
      minPrice: has(manual.minPrice) ? manual.minPrice : (ai.min_price ?? null),
      maxPrice: has(manual.maxPrice) ? manual.maxPrice : (ai.max_price ?? null),
      propertyType: manual.propertyType || ai.property_type || null,
      bedrooms: has(manual.bedrooms) ? manual.bedrooms : (ai.bedrooms ?? null),
      sortBy: manual.sortBy || null,
      sortOrder: manual.sortOrder || 'desc'
    }
  },

  /**
   * 加载房产列表
   * 有 AI 搜索时：用合并后的筛选调 getProperties（location + 四筛 AND）。
   */
  loadProperties(refresh = false) {
    if (this.data.loading) return

    this.setData({ loading: true })

    const useAI = !!(this.data.searchKeyword && this.data.aiFilters)
    const filters = useAI ? this.buildMergedFilters() : this.buildFilters()

    console.log(useAI ? '筛选参数(AI+四筛 AND):' : '筛选参数:', filters)
    console.log('当前筛选状态:', this.data.filters)

    api.getProperties(this.data.page, this.data.limit, filters)
      .then(res => {
        if (res.success && res.data) {
          const properties = refresh ? res.data.properties : this.data.properties.concat(res.data.properties)

          this.setData({
            properties: properties,
            total: res.data.pagination.total,
            hasMore: res.data.pagination.page < res.data.pagination.pages,
            loading: false
          })
        }
      })
      .catch(err => {
        console.error('加载失败:', err)
        wx.showToast({
          title: '加载失败',
          icon: 'none'
        })
        this.setData({ loading: false })
      })
      .finally(() => {
        wx.stopPullDownRefresh()
      })
  },

  /**
   * 加载更多
   */
  loadMore() {
    this.data.page++
    this.loadProperties()
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
      console.warn('读取登录状态失败', err)
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

  handleLoginTap() {
    if (this.data.loginInProgress) {
      return
    }
    this.setData({ loginInProgress: true })
    auth.loginWithWeChat()
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
        this.setData({ loginInProgress: false })
      })
  },

  handleLogoutTap() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          auth.logout()
            .then(() => {
              wx.showToast({
                title: '已退出',
                icon: 'none'
              })
              this.syncUserState()
            })
        }
      }
    })
  },

  /**
   * 筛选房产
   */
  applyFilters(e) {
    const filters = e.detail
    this.setData({
      filters: filters,
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },

  /**
   * 跳转到详情页
   */
  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/detail/detail?id=${id}`
    })
  },

  /**
   * 卧室数量筛选
   */
  onBedroomChange(e) {
    const index = e.detail.value
    const bedroom = this.data.bedroomOptions[index]
    console.log('选择卧室数量:', bedroom)
    const filters = this.data.filters
    filters.bedrooms = bedroom.value
    this.setData({
      currentBedroom: bedroom.label || '不限',
      filters: filters,
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },

  /**
   * 房产类型筛选
   */
  onTypeChange(e) {
    const index = e.detail.value
    const type = this.data.typeOptions[index]
    console.log('选择房产类型:', type)
    const filters = this.data.filters
    filters.propertyType = type.value
    this.setData({
      currentType: type.label || '不限',
      filters: filters,
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },


  /**
   * 清除筛选
   */
  clearFilter() {
    const listingType = this.data.listingType
    const defaultMax = listingType === 'for_sale' ? 2000000 : 4000

    this.setData({
      filters: {
        minPrice: '',
        maxPrice: '',
        propertyType: '',
        bedrooms: ''
      },
      currentBedroom: '不限',
      currentType: '不限',
      currentPrice: '不限',
      priceRange: [0, defaultMax],
      priceDisplay: '不限',
      pricePresetSelected: -1,
      currentSort: '默认',
      page: 1,
      hasMore: true,
      searchKeyword: '',
      aiFilters: null,
      aiFiltersText: ''
    })
    this.loadProperties(true)
  },

  /**
   * 排序变更
   */
  onSortChange(e) {
    const index = e.detail.value
    const sortOption = this.data.sortOptions[index]
    console.log('选择排序:', sortOption)

    this.setData({
      currentSort: sortOption.label,
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },

  /**
   * 切换筛选器展开/收起
   */
  toggleFilter() {
    this.setData({
      filterExpanded: !this.data.filterExpanded
    })
  },


  /**
   * 搜索框输入
   */
  onSearchInput(e) {
    this.setData({
      searchKeyword: e.detail.value
    })
  },

  /**
   * 执行搜索（传统搜索，保留兼容性）
   */
  onSearch() {
    if (!this.data.searchKeyword) {
      wx.showToast({
        title: '请输入关键词',
        icon: 'none'
      })
      return
    }

    this.setData({
      properties: [],
      page: 1,
      hasMore: true,
      aiFilters: null,
      aiFiltersText: ''
    })

    api.searchProperties(this.data.searchKeyword, this.data.page, this.data.limit)
      .then(res => {
        if (res.success && res.data) {
          this.setData({
            properties: res.data.properties,
            total: res.data.pagination.total,
            hasMore: res.data.pagination.page < res.data.pagination.pages
          })
        }
      })
      .catch(err => {
        console.error('搜索失败:', err)
        wx.showToast({
          title: '搜索失败',
          icon: 'none'
        })
      })
  },

  /**
   * AI对话式搜索。与四个筛选条件 AND：传入当前手动筛选，结果与 AI 解析合并。
   */
  onAISearch() {
    if (!this.data.searchKeyword) {
      wx.showToast({
        title: '请输入搜索条件',
        icon: 'none'
      })
      return
    }

    wx.showLoading({
      title: 'AI解析中...',
      mask: true
    })

    const extra = this.buildFilters()
    this.setData({
      properties: [],
      page: 1,
      hasMore: true,
      loading: true
    })

    api.aiSearchProperties(this.data.searchKeyword, this.data.listingType, this.data.page, this.data.limit, extra)
      .then(res => {
        wx.hideLoading()

        // 输出调试信息到控制台
        if (res.data && res.data.debug_info) {
          console.log('[AI-SEARCH] 调试信息:', res.data.debug_info)
          console.log('[AI-SEARCH] Location类型:', res.data.debug_info.location_type)
          console.log('[AI-SEARCH] 搜索Location:', res.data.debug_info.search_location)
          console.log('[AI-SEARCH] SQL提示:', res.data.debug_info.sql_hint)
          console.log('[AI-SEARCH] 找到房产数:', res.data.debug_info.total_found)

          // 如果没有找到结果，显示更详细的提示
          if (res.data.debug_info.total_found === 0) {
            console.warn('[AI-SEARCH] ⚠️ 未找到房产')
            console.warn('  - 查询参数:', res.data.debug_info.query_params)
            console.warn('  - 所有筛选条件:', res.data.debug_info.all_filters)
            if (res.data.debug_info.sql_hint) {
              console.warn('  - SQL查询:', res.data.debug_info.sql_hint)
            }

            // 显示诊断信息
            if (res.data.debug_info.diagnosis && Object.keys(res.data.debug_info.diagnosis).length > 0) {
              console.warn('  - 📊 数据库诊断信息:')
              console.warn(`     - N10房产总数（不限类型）: ${res.data.debug_info.diagnosis.location_count_all_types}`)
              console.warn(`     - ${res.data.debug_info.query_params.listing_type}房产总数（不限location）: ${res.data.debug_info.diagnosis.listing_type_count_all_locations}`)
              console.warn(`     - 同时满足两个条件的: ${res.data.debug_info.diagnosis.combined_count}`)
              console.warn(`     - 💡 建议: ${res.data.debug_info.diagnosis.suggestion}`)
            }
          }
        }

        if (res.success && res.data) {
          const filters = res.data.filters || {}
          const filtersText = this.formatAIFilters(filters)

          this.setData({
            properties: res.data.properties,
            total: res.data.pagination.total,
            hasMore: res.data.pagination.page < res.data.pagination.pages,
            aiFilters: filters,
            aiFiltersText: filtersText,
            loading: false
          })

          // 合并展示：手动有值则保留，否则用 AI。与后端 AND 逻辑一致。
          const manual = this.data.filters
          const newFilters = {
            minPrice: (manual.minPrice !== '' && manual.minPrice != null) ? manual.minPrice : (filters.min_price || ''),
            maxPrice: (manual.maxPrice !== '' && manual.maxPrice != null) ? manual.maxPrice : (filters.max_price || ''),
            propertyType: manual.propertyType || filters.property_type || '',
            bedrooms: (manual.bedrooms !== '' && manual.bedrooms != null) ? manual.bedrooms : (filters.bedrooms || '')
          }

          let currentPrice = '不限'
          if (newFilters.minPrice || newFilters.maxPrice) {
            const matchedOption = this.data.priceOptions.find(opt =>
              opt.minPrice === newFilters.minPrice && opt.maxPrice === newFilters.maxPrice
            )
            if (matchedOption) {
              currentPrice = matchedOption.label
            } else {
              const listingType = filters.listing_type || this.data.listingType
              const defaultMax = listingType === 'for_sale' ? 2000000 : 4000
              currentPrice = this.formatPriceRange([newFilters.minPrice || 0, newFilters.maxPrice || defaultMax])
            }
          }

          const typeLabel = this.data.typeOptions.find(o => o.value === newFilters.propertyType)?.label || '不限'
          const bedroomLabel = this.data.bedroomOptions.find(o => String(o.value) === String(newFilters.bedrooms))?.label || '不限'

          this.setData({
            filters: newFilters,
            currentPrice: currentPrice,
            priceDisplay: currentPrice,
            currentType: typeLabel,
            currentBedroom: bedroomLabel
          })
        }
      })
      .catch(err => {
        wx.hideLoading()
        console.error('AI搜索失败:', err)
        wx.showToast({
          title: 'AI搜索失败，请重试',
          icon: 'none',
          duration: 2000
        })
        this.setData({ loading: false })
      })
  },

  /**
   * 格式化AI筛选条件显示文本
   */
  formatAIFilters(filters) {
    const parts = []

    if (filters.listing_type) {
      parts.push(filters.listing_type === 'for_sale' ? '出售' : '出租')
    }

    if (filters.location) {
      const r = filters.radius_meters
      parts.push(r ? `${filters.location}周围${r}米` : filters.location + '附近')
    }

    if (filters.bedrooms) {
      parts.push(filters.bedrooms + '室')
    }

    if (filters.property_type) {
      const typeMap = {
        'flat': '公寓',
        'house': '别墅',
        'studio': '单间',
        'other': '其他'
      }
      parts.push(typeMap[filters.property_type] || filters.property_type)
    }

    if (filters.min_price || filters.max_price) {
      let priceText = ''
      if (filters.min_price && filters.max_price) {
        if (filters.listing_type === 'for_sale') {
          priceText = `£${(filters.min_price / 1000000).toFixed(1)}万-£${(filters.max_price / 1000000).toFixed(1)}万`
        } else {
          priceText = `£${filters.min_price}-£${filters.max_price}/月`
        }
      } else if (filters.max_price) {
        if (filters.listing_type === 'for_sale') {
          priceText = `£${(filters.max_price / 1000000).toFixed(1)}万以下`
        } else {
          priceText = `£${filters.max_price}/月以下`
        }
      } else if (filters.min_price) {
        if (filters.listing_type === 'for_sale') {
          priceText = `£${(filters.min_price / 1000000).toFixed(1)}万以上`
        } else {
          priceText = `£${filters.min_price}/月以上`
        }
      }
      if (priceText) {
        parts.push(priceText)
      }
    }

    return parts.length > 0 ? parts.join(' · ') : '全部'
  },

  /**
   * 更新价格预设选项
   */
  updatePricePresets() {
    const listingType = this.data.listingType
    let presets = []
    let priceOptions = [{ label: '不限', value: '', minPrice: null, maxPrice: null }]

    console.log('[PRICE] 更新价格预设, listingType:', listingType)

    if (listingType === 'for_sale') {
      // 出售：使用总价预设
      presets = this.data.forSalePricePresets
      console.log('[PRICE] 出售预设:', presets)
      priceOptions = priceOptions.concat(presets.map(p => ({
        label: p.label,
        value: p.label,
        minPrice: p.minPrice,
        maxPrice: p.maxPrice
      })))
      console.log('[PRICE] 出售价格选项:', priceOptions)
      this.setData({
        pricePresets: presets,
        priceOptions: priceOptions,
        priceRange: [0, 2000000],
        priceDisplay: '不限',
        currentPrice: '不限',
        pricePresetSelected: -1
      })
    } else {
      // 出租：使用月租金预设
      presets = this.data.forRentPricePresets
      console.log('[PRICE] 出租预设:', presets)
      priceOptions = priceOptions.concat(presets.map(p => ({
        label: p.label,
        value: p.label,
        minPrice: p.minPrice,
        maxPrice: p.maxPrice
      })))
      console.log('[PRICE] 出租价格选项:', priceOptions)
      this.setData({
        pricePresets: presets,
        priceOptions: priceOptions,
        priceRange: [0, 4000],
        priceDisplay: '不限',
        currentPrice: '不限',
        pricePresetSelected: -1
      })
    }

    console.log('[PRICE] 最终priceOptions:', this.data.priceOptions)
  },

  /**
   * 切换房产类型（出售/出租）
   */
  onListingTypeChange(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      listingType: type,
      properties: [],
      page: 1,
      hasMore: true,
      // 清除价格筛选
      'filters.minPrice': '',
      'filters.maxPrice': '',
      currentPrice: '不限',
      priceDisplay: '不限'
    })
    // 更新价格预设
    this.updatePricePresets()
    this.loadProperties(true)
  },

  /**
   * 价格范围筛选变更
   */
  onPriceChange(e) {
    const index = e.detail.value
    console.log('[PRICE] 选择索引:', index)
    console.log('[PRICE] 当前priceOptions:', this.data.priceOptions)
    console.log('[PRICE] priceOptions长度:', this.data.priceOptions ? this.data.priceOptions.length : 0)

    if (!this.data.priceOptions || this.data.priceOptions.length === 0) {
      console.error('[PRICE] priceOptions为空，重新初始化')
      this.updatePricePresets()
      return
    }

    const priceOption = this.data.priceOptions[index]
    console.log('选择价格范围:', priceOption)

    const filters = this.data.filters
    if (priceOption.minPrice !== null && priceOption.maxPrice !== null) {
      filters.minPrice = priceOption.minPrice
      filters.maxPrice = priceOption.maxPrice
    } else {
      // 选择"不限"
      filters.minPrice = ''
      filters.maxPrice = ''
    }

    this.setData({
      currentPrice: priceOption.label,
      filters: filters,
      priceDisplay: priceOption.label,
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },

  /**
   * 选择价格预设
   */
  onPricePresetTap(e) {
    const index = e.currentTarget.dataset.index
    const preset = this.data.pricePresets[index]
    this.setData({
      priceRange: [preset.minPrice, preset.maxPrice],
      pricePresetSelected: index,
      priceDisplay: preset.label
    })
  },

  /**
   * 手动输入最低价格
   */
  onMinPriceInput(e) {
    const value = parseInt(e.detail.value) || 0
    const priceRange = this.data.priceRange
    const newRange = [value, priceRange[1]]
    const display = this.formatPriceRange(newRange)
    this.setData({
      priceRange: newRange,
      pricePresetSelected: -1, // 清空预设选择
      priceDisplay: display
    })
  },

  /**
   * 手动输入最高价格
   */
  onMaxPriceInput(e) {
    const listingType = this.data.listingType
    const defaultMax = listingType === 'for_sale' ? 2000000 : 4000
    const value = parseInt(e.detail.value) || defaultMax
    const priceRange = this.data.priceRange
    const newRange = [priceRange[0], value]
    const display = this.formatPriceRange(newRange)
    this.setData({
      priceRange: newRange,
      pricePresetSelected: -1, // 清空预设选择
      priceDisplay: display
    })
  },

  /**
   * 格式化价格范围显示
   */
  formatPriceRange(priceRange) {
    const minPrice = priceRange[0] || 0
    const maxPrice = priceRange[1]
    const listingType = this.data.listingType

    // 根据类型设置默认最大值
    const defaultMax = listingType === 'for_sale' ? 2000000 : 4000

    if (minPrice === 0 && maxPrice >= defaultMax) {
      return '不限'
    }

    if (listingType === 'for_sale') {
      // 出售房产：用"万"表示（总价）
      if (minPrice === 0 && maxPrice < defaultMax) {
        return `£${(maxPrice / 1000000).toFixed(1)}万以下`
      } else if (minPrice > 0 && maxPrice < defaultMax) {
        return `£${(minPrice / 1000000).toFixed(1)}-${(maxPrice / 1000000).toFixed(1)}万`
      } else if (minPrice > 0 && maxPrice >= defaultMax) {
        return `£${(minPrice / 1000000).toFixed(1)}万以上`
      }
    } else {
      // 出租房产：用"月"表示（月租金）
      if (minPrice === 0 && maxPrice < defaultMax) {
        return `£${maxPrice}/月以下`
      } else if (minPrice > 0 && maxPrice < defaultMax) {
        return `£${minPrice}-${maxPrice}/月`
      } else if (minPrice > 0 && maxPrice >= defaultMax) {
        return `£${minPrice}/月以上`
      }
    }
    return '不限'
  },

  /**
   * 应用价格筛选
   */
  applyPriceFilter() {
    const filters = this.data.filters
    filters.minPrice = this.data.priceRange[0]
    filters.maxPrice = this.data.priceRange[1]

    // 如果选择了预设，就使用预设的显示，否则使用格式化的显示
    let display = this.data.pricePresetSelected >= 0 ?
      this.data.pricePresets[this.data.pricePresetSelected].label :
      this.data.priceDisplay

    this.setData({
      showFilter: false,
      filters: filters,
      priceDisplay: display,
      page: 1,
      hasMore: true
    })
    console.log('应用价格筛选:', filters)
    this.loadProperties(true)
  },

  /**
   * 取消价格筛选
   */
  cancelPriceFilter() {
    // 恢复原来的价格显示
    const currentFilter = this.data.filters
    const listingType = this.data.listingType
    const defaultMax = listingType === 'for_sale' ? 2000000 : 4000
    let display = '不限'
    if (currentFilter.minPrice || currentFilter.maxPrice) {
      const range = [currentFilter.minPrice || 0, currentFilter.maxPrice || defaultMax]
      display = this.formatPriceRange(range)
    }

    this.setData({
      showFilter: false,
      priceRange: [currentFilter.minPrice || 0, currentFilter.maxPrice || defaultMax],
      pricePresetSelected: -1,
      priceDisplay: display
    })
  }
})
