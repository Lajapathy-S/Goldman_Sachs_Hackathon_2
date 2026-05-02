import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

const STORAGE_KEY = 'aichemist_auth'
const USERS_KEY = 'aichemist_users'

export type User = {
  username: string
  email: string
}

type AuthContextValue = {
  user: User | null
  login: (username: string, password: string) => { ok: boolean; error?: string }
  signup: (username: string, email: string, password: string) => { ok: boolean; error?: string }
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function readStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

type StoredUserRecord = { username: string; email: string; password: string }

function readUsers(): StoredUserRecord[] {
  try {
    const raw = localStorage.getItem(USERS_KEY)
    if (!raw) return []
    return JSON.parse(raw) as StoredUserRecord[]
  } catch {
    return []
  }
}

function writeUsers(users: StoredUserRecord[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() =>
    typeof window !== 'undefined' ? readStoredUser() : null,
  )

  const login = useCallback((username: string, password: string) => {
    const u = username.trim().toLowerCase()
    const p = password
    if (u === 'admin' && p === 'admin') {
      const next: User = { username: 'admin', email: 'admin@localhost' }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      setUser(next)
      return { ok: true }
    }
    const users = readUsers()
    const found = users.find(
      (x) => x.username.toLowerCase() === u && x.password === p,
    )
    if (found) {
      const next: User = { username: found.username, email: found.email }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      setUser(next)
      return { ok: true }
    }
    return { ok: false, error: 'Invalid username or password.' }
  }, [])

  const signup = useCallback(
    (username: string, email: string, password: string) => {
      const u = username.trim()
      if (!u || !email.trim() || !password) {
        return { ok: false, error: 'Please fill in all fields.' }
      }
      const users = readUsers()
      if (users.some((x) => x.username.toLowerCase() === u.toLowerCase())) {
        return { ok: false, error: 'That username is already taken.' }
      }
      if (u.toLowerCase() === 'admin') {
        return { ok: false, error: 'Choose a different username.' }
      }
      users.push({
        username: u,
        email: email.trim(),
        password,
      })
      writeUsers(users)
      const next: User = { username: u, email: email.trim() }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      setUser(next)
      return { ok: true }
    },
    [],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, login, signup, logout }),
    [user, login, signup, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
