const FALLBACK_GRADIENTS = [
  'linear-gradient(135deg, #f4d7c4 0%, #e7bfa7 100%)',
  'linear-gradient(135deg, #f6e7d7 0%, #d8a46f 100%)',
  'linear-gradient(135deg, #e7d4cb 0%, #c9866a 100%)',
  'linear-gradient(135deg, #d6e0d2 0%, #8ba48f 100%)'
]

export const parseImageList = (images) => {
  if (!images) {
    return []
  }

  if (Array.isArray(images)) {
    return images.filter((item) => typeof item === 'string' && item.trim())
  }

  try {
    const parsed = JSON.parse(images)
    return Array.isArray(parsed)
      ? parsed.filter((item) => typeof item === 'string' && item.trim())
      : []
  } catch (error) {
    if (typeof images === 'string' && images.startsWith('http')) {
      return [images]
    }
    return []
  }
}

export const getImageUrl = (images, fallbackIndex = 0) => {
  const list = parseImageList(images)
  return list[0] || ''
}

export const createMediaStyle = (images, fallbackIndex = 0) => {
  const url = getImageUrl(images, fallbackIndex)
  if (url) {
    return {
      backgroundImage: `url(${url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }

  return {
    background: FALLBACK_GRADIENTS[fallbackIndex % FALLBACK_GRADIENTS.length]
  }
}

export const normalizeListResponse = (response) => {
  const data = response?.data
  if (Array.isArray(data)) {
    return data
  }
  if (Array.isArray(data?.content)) {
    return data.content
  }
  return []
}

export const fallbackGradientAt = (index = 0) => FALLBACK_GRADIENTS[index % FALLBACK_GRADIENTS.length]
