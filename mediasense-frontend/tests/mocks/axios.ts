import { vi } from 'vitest'

const mockAxios = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  interceptors: {
    request: {
      use: vi.fn((onFulfilled) => {
        return onFulfilled
      }),
      eject: vi.fn()
    },
    response: {
      use: vi.fn((onFulfilled, onRejected) => {
        return { onFulfilled, onRejected }
      }),
      eject: vi.fn()
    }
  },
  create: vi.fn().mockReturnThis()
}

export default mockAxios 