//utils/api.js
function getAppInstance() {
  try {
    return getApp()
  } catch (err) {
    return null
  }
}

function getAuthToken() {
  const app = getAppInstance()
  if (app && app.globalData && app.globalData.authToken) {
    return app.globalData.authToken
  }
  try {
    return wx.getStorageSync('authToken')
  } catch (err) {
    console.warn('读取本地token失败', err)
    return ''
  }
}

/**
 * 请求封装
 */
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    const app = getAppInstance()
    const baseUrl = app?.globalData?.apiBaseUrl || ''
    const apiUrl = `${baseUrl}${url}`
    const headers = {
      'content-type': 'application/json'
    }
    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    wx.request({
      url: apiUrl,
      method: method,
      data: data,
      header: headers,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
          return
        }
        if (res.statusCode === 401) {
          if (app && typeof app.clearAuthData === 'function') {
            app.clearAuthData()
          }
          wx.showToast({
            title: (res.data && res.data.error) || '请先登录',
            icon: 'none'
          })
          reject(res.data)
        } else {
          reject(res.data)
        }
      },
      fail: (err) => {
        console.error('请求失败:', err)
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

/**
 * 获取房产列表
 * @param {Object} filters - 可选 location（AI 搜索地域）、minPrice、maxPrice、propertyType、bedrooms、listingType、sortBy、sortOrder
 */
function getProperties(page = 1, limit = 20, filters = {}) {
  let url = `/api/properties?page=${page}&limit=${limit}`
  
  if (filters.location) {
    url += `&location=${encodeURIComponent(filters.location)}`
  }
  if (filters.minPrice !== null && filters.minPrice !== undefined && filters.minPrice !== '') {
    url += `&min_price=${filters.minPrice}`
  }
  if (filters.maxPrice !== null && filters.maxPrice !== undefined && filters.maxPrice !== '') {
    url += `&max_price=${filters.maxPrice}`
  }
  if (filters.propertyType) {
    url += `&property_type=${filters.propertyType}`
  }
  if (filters.bedrooms !== null && filters.bedrooms !== undefined && filters.bedrooms !== '') {
    url += `&bedrooms=${filters.bedrooms}`
  }
  if (filters.listingType) {
    url += `&listing_type=${filters.listingType}`
  }
  if (filters.sortBy) {
    url += `&sort_by=${filters.sortBy}`
  }
  if (filters.sortOrder) {
    url += `&sort_order=${filters.sortOrder}`
  }
  
  console.log('API请求URL:', url)
  return request(url)
}

/**
 * 获取房产详情
 */
function getPropertyDetail(id) {
  return request(`/api/properties/${id}`)
}

/**
 * 搜索房产
 */
function searchProperties(keyword, page = 1, limit = 20) {
  return request(`/api/properties/search?keyword=${keyword}&page=${page}&limit=${limit}`)
}

/**
 * AI对话式搜索房产。与四个筛选条件 AND 合并。
 * @param {string} query - 自然语言查询
 * @param {string} listingType - 'for_sale'或'for_rent'
 * @param {number} page - 页码
 * @param {number} limit - 每页数量
 * @param {Object} [extraFilters] - 四个筛选条件 { minPrice, maxPrice, propertyType, bedrooms, sortBy, sortOrder, listingType }，与 AI 结果 AND
 */
function aiSearchProperties(query, listingType = 'for_rent', page = 1, limit = 20, extraFilters = null) {
  const body = {
    query: query,
    listing_type: listingType
  }
  if (extraFilters && typeof extraFilters === 'object') {
    body.extra_filters = {
      min_price: extraFilters.minPrice ?? extraFilters.min_price,
      max_price: extraFilters.maxPrice ?? extraFilters.max_price,
      property_type: extraFilters.propertyType || extraFilters.property_type,
      bedrooms: extraFilters.bedrooms,
      sort_by: extraFilters.sortBy || extraFilters.sort_by,
      sort_order: extraFilters.sortOrder || extraFilters.sort_order,
      listing_type: extraFilters.listingType || extraFilters.listing_type
    }
  }
  return request('/api/properties/ai-search?page=' + page + '&limit=' + limit, 'POST', body)
}

function login(code, userInfo = {}) {
  return request('/api/auth/login', 'POST', {
    code,
    user_info: userInfo
  })
}

function getCurrentUser() {
  return request('/api/users/me', 'GET')
}

function requestContactLink(propertyId) {
  return request('/api/users/contact-link', 'POST', {
    property_id: propertyId
  })
}

module.exports = {
  getProperties,
  getPropertyDetail,
  searchProperties,
  aiSearchProperties,
  login,
  getCurrentUser,
  requestContactLink
}
