//pages/index/index.js
const api = require('../../utils/api.js')

Page({
  data: {
    properties: [],
    page: 1,
    limit: 20,
    total: 0,
    loading: false,
    hasMore: true,
    showFilter: false,
    filters: {
      minPrice: '',
      maxPrice: '',
      propertyType: '',
      bedrooms: ''
    },
    listingType: 'for_rent', // 默认显示出租房产
    // 筛选选项
    bedroomOptions: [
      { label: '全部', value: '' },
      { label: '1室', value: 1 },
      { label: '2室', value: 2 },
      { label: '3室', value: 3 },
      { label: '4室', value: 4 },
      { label: '5室+', value: 5 }
    ],
    typeOptions: [
      { label: '全部', value: '' },
      { label: '公寓', value: 'flat' },
      { label: '别墅', value: 'house' },
      { label: '其他', value: 'other' }
    ],
    listingTypeOptions: [
      { label: '出售', value: 'for_sale' },
      { label: '出租', value: 'for_rent' }
    ],
    currentBedroom: '全部',
    currentType: '全部',
    priceRange: [0, 2000000]
  },

  onLoad() {
    this.loadProperties()
  },

  onReady() {
    // 页面渲染完成
  },

  onShow() {
    // 页面显示
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
  },

  /**
   * 加载房产列表
   */
  loadProperties(refresh = false) {
    if (this.data.loading) return
    
    this.setData({ loading: true })
    
    // 构建筛选参数
    const filters = {
      minPrice: this.data.filters.minPrice || null,
      maxPrice: this.data.filters.maxPrice || null,
      propertyType: this.data.filters.propertyType || null,
      bedrooms: this.data.filters.bedrooms || null,
      listingType: this.data.listingType || 'for_sale'
    }
    
    console.log('筛选参数:', filters)
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
   * 显示/隐藏筛选面板
   */
  toggleFilter() {
    this.setData({
      showFilter: !this.data.showFilter
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
      currentBedroom: bedroom.label,
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
      currentType: type.label,
      filters: filters,
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },

  /**
   * 价格最小值变化
   */
  onPriceStartChange(e) {
    const value = e.detail.value
    const priceRange = this.data.priceRange
    this.setData({
      priceRange: [value, priceRange[1]]
    })
  },

  /**
   * 价格最大值变化
   */
  onPriceEndChange(e) {
    const value = e.detail.value
    const priceRange = this.data.priceRange
    this.setData({
      priceRange: [priceRange[0], value]
    })
  },

  /**
   * 价格范围筛选
   */
  onPriceChange(e) {
    const minPrice = e.detail.value[0]
    const maxPrice = e.detail.value[1]
    this.setData({
      priceRange: [minPrice, maxPrice],
      'filters.minPrice': minPrice,
      'filters.maxPrice': maxPrice,
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },

  /**
   * 清除筛选
   */
  clearFilter() {
    this.setData({
      filters: {
        minPrice: '',
        maxPrice: '',
        propertyType: '',
        bedrooms: ''
      },
      currentBedroom: '全部',
      currentType: '全部',
      priceRange: [0, 2000000],
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  },

  /**
   * 应用筛选
   */
  applyFilter() {
    // 将价格范围应用到筛选条件
    const filters = this.data.filters
    filters.minPrice = this.data.priceRange[0]
    filters.maxPrice = this.data.priceRange[1]
    
    this.setData({
      showFilter: false,
      filters: filters,
      page: 1,
      hasMore: true
    })
    console.log('应用价格筛选:', filters)
    this.loadProperties(true)
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
   * 执行搜索
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
      hasMore: true
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
   * 切换房产类型（出售/出租）
   */
  onListingTypeChange(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      listingType: type,
      properties: [],
      page: 1,
      hasMore: true
    })
    this.loadProperties(true)
  }
})
