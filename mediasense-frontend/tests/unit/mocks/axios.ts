import { vi } from 'vitest'

const mockAxiosInstance = {
  create: vi.fn().mockReturnValue({
    interceptors: {
      request: {
        use: vi.fn().mockImplementation((fn) => fn),
        eject: vi.fn()
      },
      response: {
        use: vi.fn().mockImplementation((fn) => fn),
        eject: vi.fn()
      }
    },
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
    defaults: {
      headers: {
        common: {},
        get: {},
        post: {},
        put: {},
        delete: {}
      },
      timeout: 0,
      baseURL: ''
    }
  }),
  interceptors: {
    request: {
      use: vi.fn().mockImplementation((fn) => fn),
      eject: vi.fn()
    },
    response: {
      use: vi.fn().mockImplementation((fn) => fn),
      eject: vi.fn()
    }
  },
  get: vi.fn().mockResolvedValue({ data: {} }),
  post: vi.fn().mockResolvedValue({ data: {} }),
  put: vi.fn().mockResolvedValue({ data: {} }),
  delete: vi.fn().mockResolvedValue({ data: {} }),
  defaults: {
    headers: {
      common: {},
      get: {},
      post: {},
      put: {},
      delete: {}
    },
    timeout: 0,
    baseURL: ''
  }
}

export default {
  default: mockAxiosInstance,
  ...mockAxiosInstance
} 