//utils/api.js
const app = getApp()

/**
 * 请求封装
 */
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    const apiUrl = app.globalData.apiBaseUrl + url
    
    wx.request({
      url: apiUrl,
      method: method,
      data: data,
      header: {
        'content-type': 'application/json'
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
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
 */
function getProperties(page = 1, limit = 20, filters = {}) {
  let url = `/api/properties?page=${page}&limit=${limit}`
  
  // 添加筛选条件
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

module.exports = {
  getProperties,
  getPropertyDetail,
  searchProperties
}
