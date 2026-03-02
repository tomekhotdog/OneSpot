import baysData from './data/bays.json'

const STORAGE_KEY = 'onespot_demo'
const SESSION_KEY = 'onespot_demo_session'

// ---- helpers ----
function generateId() {
  return Math.random().toString(36).slice(2, 10)
}

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function tomorrowStr() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

function daysFromNow(n) {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return d.toISOString().slice(0, 10)
}

function dayOfWeek(dateStr) {
  const names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
  return names[new Date(dateStr + 'T12:00:00').getDay()]
}

// ---- state management ----
function getDefaultState() {
  const tomorrow = tomorrowStr()
  const d0 = todayStr()
  const d1 = tomorrow
  const d2 = daysFromNow(2)
  const d3 = daysFromNow(3)
  const d4 = daysFromNow(4)
  const d5 = daysFromNow(5)
  const d6 = daysFromNow(6)

  // Weekday patterns
  const fullWeek = { monday: { start: 8, end: 18 }, tuesday: { start: 8, end: 18 }, wednesday: { start: 8, end: 18 }, thursday: { start: 8, end: 18 }, friday: { start: 8, end: 18 } }
  const officeHours = { monday: { start: 9, end: 17 }, tuesday: { start: 9, end: 17 }, wednesday: { start: 9, end: 17 }, thursday: { start: 9, end: 17 }, friday: { start: 9, end: 17 } }
  const mwf = { monday: { start: 10, end: 16 }, wednesday: { start: 10, end: 16 }, friday: { start: 10, end: 16 } }
  const tth = { tuesday: { start: 8, end: 14 }, thursday: { start: 8, end: 14 } }
  const earlyBird = { monday: { start: 6, end: 12 }, tuesday: { start: 6, end: 12 }, wednesday: { start: 6, end: 12 }, thursday: { start: 6, end: 12 }, friday: { start: 6, end: 12 } }
  const lateSaver = { monday: { start: 14, end: 22 }, tuesday: { start: 14, end: 22 }, wednesday: { start: 14, end: 22 }, thursday: { start: 14, end: 22 }, friday: { start: 14, end: 22 } }
  const weekendOnly = { saturday: { start: 8, end: 20 }, sunday: { start: 8, end: 20 } }
  const allWeek = { ...fullWeek, saturday: { start: 9, end: 18 }, sunday: { start: 9, end: 18 } }

  return {
    users: {
      // --- GF bay owners ---
      u1:  { id: 'u1',  phone: '+447700900001', email: 'tomek@onespot.demo', name: 'Tomek',    is_owner: true, bay_number: '7',  credits: 20, availability_permission: 'anyone' },
      u2:  { id: 'u2',  phone: '+447700900002', email: 'sarah@onespot.demo', name: 'Sarah',    is_owner: true, bay_number: '12', credits: 20, availability_permission: 'anyone' },
      u3:  { id: 'u3',  phone: '+447700900003', email: 'mike@onespot.demo', name: 'Mike',     is_owner: true, bay_number: '23', credits: 20, availability_permission: 'anyone' },
      u5:  { id: 'u5',  phone: '+447700900005', email: 'priya@onespot.demo', name: 'Priya',    is_owner: true, bay_number: '3',  credits: 15, availability_permission: 'anyone' },
      u6:  { id: 'u6',  phone: '+447700900006', email: 'alex@onespot.demo', name: 'Alex',     is_owner: true, bay_number: '10', credits: 22, availability_permission: 'anyone' },
      u7:  { id: 'u7',  phone: '+447700900007', email: 'wei@onespot.demo', name: 'Wei',      is_owner: true, bay_number: '16', credits: 18, availability_permission: 'anyone' },
      u8:  { id: 'u8',  phone: '+447700900008', email: 'fatima@onespot.demo', name: 'Fatima',   is_owner: true, bay_number: '20', credits: 25, availability_permission: 'anyone' },
      u9:  { id: 'u9',  phone: '+447700900009', email: 'dan@onespot.demo', name: 'Dan',      is_owner: true, bay_number: '28', credits: 12, availability_permission: 'anyone' },
      u10: { id: 'u10', phone: '+447700900010', email: 'lena@onespot.demo', name: 'Lena',     is_owner: true, bay_number: '35', credits: 20, availability_permission: 'anyone' },
      u11: { id: 'u11', phone: '+447700900011', email: 'raj@onespot.demo', name: 'Raj',      is_owner: true, bay_number: '40', credits: 16, availability_permission: 'anyone' },
      u12: { id: 'u12', phone: '+447700900012', email: 'emma@onespot.demo', name: 'Emma',     is_owner: true, bay_number: '45', credits: 20, availability_permission: 'anyone' },
      u13: { id: 'u13', phone: '+447700900013', email: 'ollie@onespot.demo', name: 'Ollie',    is_owner: true, bay_number: '5',  credits: 14, availability_permission: 'anyone' },
      u14: { id: 'u14', phone: '+447700900014', email: 'yuki@onespot.demo', name: 'Yuki',     is_owner: true, bay_number: '31', credits: 20, availability_permission: 'anyone' },
      u15: { id: 'u15', phone: '+447700900015', email: 'carlos@onespot.demo', name: 'Carlos',   is_owner: true, bay_number: '38', credits: 18, availability_permission: 'anyone' },
      // --- MZ bay owners ---
      u16: { id: 'u16', phone: '+447700900016', email: 'anya@onespot.demo', name: 'Anya',     is_owner: true, bay_number: '5',  credits: 20, availability_permission: 'anyone' },
      u17: { id: 'u17', phone: '+447700900017', email: 'ben@onespot.demo', name: 'Ben',      is_owner: true, bay_number: '15', credits: 22, availability_permission: 'anyone' },
      u18: { id: 'u18', phone: '+447700900018', email: 'chloe@onespot.demo', name: 'Chloe',    is_owner: true, bay_number: '25', credits: 18, availability_permission: 'anyone' },
      u19: { id: 'u19', phone: '+447700900019', email: 'david@onespot.demo', name: 'David',    is_owner: true, bay_number: '36', credits: 20, availability_permission: 'anyone' },
      u20: { id: 'u20', phone: '+447700900020', email: 'elena@onespot.demo', name: 'Elena',    is_owner: true, bay_number: '42', credits: 15, availability_permission: 'anyone' },
      u21: { id: 'u21', phone: '+447700900021', email: 'finn@onespot.demo', name: 'Finn',     is_owner: true, bay_number: '50', credits: 20, availability_permission: 'anyone' },
      u22: { id: 'u22', phone: '+447700900022', email: 'grace@onespot.demo', name: 'Grace',    is_owner: true, bay_number: '60', credits: 25, availability_permission: 'anyone' },
      u23: { id: 'u23', phone: '+447700900023', email: 'hugo@onespot.demo', name: 'Hugo',     is_owner: true, bay_number: '70', credits: 20, availability_permission: 'anyone' },
      u24: { id: 'u24', phone: '+447700900024', email: 'isla@onespot.demo', name: 'Isla',     is_owner: true, bay_number: '80', credits: 17, availability_permission: 'anyone' },
      u25: { id: 'u25', phone: '+447700900025', email: 'james@onespot.demo', name: 'James',    is_owner: true, bay_number: '90', credits: 20, availability_permission: 'anyone' },
      u26: { id: 'u26', phone: '+447700900026', email: 'karen@onespot.demo', name: 'Karen',    is_owner: true, bay_number: '55', credits: 22, availability_permission: 'anyone' },
      u27: { id: 'u27', phone: '+447700900027', email: 'liam@onespot.demo', name: 'Liam',     is_owner: true, bay_number: '67', credits: 20, availability_permission: 'anyone' },
      u28: { id: 'u28', phone: '+447700900028', email: 'mia@onespot.demo', name: 'Mia',      is_owner: true, bay_number: '78', credits: 18, availability_permission: 'anyone' },
      u29: { id: 'u29', phone: '+447700900029', email: 'noah@onespot.demo', name: 'Noah',     is_owner: true, bay_number: '85', credits: 20, availability_permission: 'anyone' },
      u30: { id: 'u30', phone: '+447700900030', email: 'olivia@onespot.demo', name: 'Olivia',   is_owner: true, bay_number: '94', credits: 16, availability_permission: 'anyone' },
      // --- Non-owners ---
      u4:  { id: 'u4',  phone: '+447700900004', email: 'jane@onespot.demo', name: 'Jane',     is_owner: false, bay_number: null, credits: 16, availability_permission: 'anyone' },
      u31: { id: 'u31', phone: '+447700900031', email: 'ravi@onespot.demo', name: 'Ravi',     is_owner: false, bay_number: null, credits: 20, availability_permission: 'anyone' },
      u32: { id: 'u32', phone: '+447700900032', email: 'sophie@onespot.demo', name: 'Sophie',   is_owner: false, bay_number: null, credits: 14, availability_permission: 'anyone' },
      u33: { id: 'u33', phone: '+447700900033', email: 'tom@onespot.demo', name: 'Tom',      is_owner: false, bay_number: null, credits: 10, availability_permission: 'anyone' },
      u34: { id: 'u34', phone: '+447700900034', email: 'uma@onespot.demo', name: 'Uma',      is_owner: false, bay_number: null, credits: 20, availability_permission: 'anyone' },
    },
    availabilities: {
      // GF owners
      a1:  { id: 'a1',  user_id: 'u1',  type: 'recurring', paused: false, exclusions: [], pattern: fullWeek },
      a2:  { id: 'a2',  user_id: 'u2',  type: 'recurring', paused: false, exclusions: [], pattern: officeHours },
      a3:  { id: 'a3',  user_id: 'u3',  type: 'recurring', paused: false, exclusions: [], pattern: mwf },
      a5:  { id: 'a5',  user_id: 'u5',  type: 'recurring', paused: false, exclusions: [], pattern: fullWeek },
      a6:  { id: 'a6',  user_id: 'u6',  type: 'recurring', paused: false, exclusions: [], pattern: tth },
      a7:  { id: 'a7',  user_id: 'u7',  type: 'recurring', paused: false, exclusions: [], pattern: earlyBird },
      a8:  { id: 'a8',  user_id: 'u8',  type: 'recurring', paused: false, exclusions: [], pattern: officeHours },
      a9:  { id: 'a9',  user_id: 'u9',  type: 'recurring', paused: false, exclusions: [], pattern: lateSaver },
      a10: { id: 'a10', user_id: 'u10', type: 'recurring', paused: false, exclusions: [], pattern: allWeek },
      a11: { id: 'a11', user_id: 'u11', type: 'recurring', paused: false, exclusions: [], pattern: mwf },
      a12: { id: 'a12', user_id: 'u12', type: 'recurring', paused: false, exclusions: [], pattern: officeHours },
      a13: { id: 'a13', user_id: 'u13', type: 'recurring', paused: false, exclusions: [], pattern: fullWeek },
      a14: { id: 'a14', user_id: 'u14', type: 'recurring', paused: false, exclusions: [], pattern: weekendOnly },
      a15: { id: 'a15', user_id: 'u15', type: 'recurring', paused: false, exclusions: [], pattern: earlyBird },
      // MZ owners
      a16: { id: 'a16', user_id: 'u16', type: 'recurring', paused: false, exclusions: [], pattern: fullWeek },
      a17: { id: 'a17', user_id: 'u17', type: 'recurring', paused: false, exclusions: [], pattern: officeHours },
      a18: { id: 'a18', user_id: 'u18', type: 'recurring', paused: false, exclusions: [], pattern: mwf },
      a19: { id: 'a19', user_id: 'u19', type: 'recurring', paused: false, exclusions: [], pattern: fullWeek },
      a20: { id: 'a20', user_id: 'u20', type: 'recurring', paused: false, exclusions: [], pattern: tth },
      a21: { id: 'a21', user_id: 'u21', type: 'recurring', paused: false, exclusions: [], pattern: lateSaver },
      a22: { id: 'a22', user_id: 'u22', type: 'recurring', paused: false, exclusions: [], pattern: allWeek },
      a23: { id: 'a23', user_id: 'u23', type: 'recurring', paused: false, exclusions: [], pattern: earlyBird },
      a24: { id: 'a24', user_id: 'u24', type: 'recurring', paused: false, exclusions: [], pattern: officeHours },
      a25: { id: 'a25', user_id: 'u25', type: 'recurring', paused: false, exclusions: [], pattern: mwf },
      a26: { id: 'a26', user_id: 'u26', type: 'recurring', paused: false, exclusions: [], pattern: fullWeek },
      a27: { id: 'a27', user_id: 'u27', type: 'recurring', paused: false, exclusions: [], pattern: officeHours },
      a28: { id: 'a28', user_id: 'u28', type: 'recurring', paused: false, exclusions: [], pattern: tth },
      a29: { id: 'a29', user_id: 'u29', type: 'recurring', paused: false, exclusions: [], pattern: allWeek },
      a30: { id: 'a30', user_id: 'u30', type: 'recurring', paused: false, exclusions: [], pattern: weekendOnly },
      // One-off availabilities (extra days)
      a31: { id: 'a31', user_id: 'u14', type: 'one_off', paused: false, date: d2, start_hour: 8, end_hour: 20 },
      a32: { id: 'a32', user_id: 'u20', type: 'one_off', paused: false, date: d1, start_hour: 10, end_hour: 18 },
      a33: { id: 'a33', user_id: 'u28', type: 'one_off', paused: false, date: d3, start_hour: 7, end_hour: 15 },
    },
    bookings: {
      // Today bookings
      b1:  { id: 'b1',  user_id: 'u4',  bay_number: '7',  date: d0, start_hour: 9,  end_hour: 17, status: 'confirmed', owner_name: 'Tomek' },
      b2:  { id: 'b2',  user_id: 'u31', bay_number: '3',  date: d0, start_hour: 8,  end_hour: 14, status: 'confirmed', owner_name: 'Priya' },
      b3:  { id: 'b3',  user_id: 'u32', bay_number: '20', date: d0, start_hour: 10, end_hour: 16, status: 'confirmed', owner_name: 'Fatima' },
      b4:  { id: 'b4',  user_id: 'u33', bay_number: '5',  date: d0, start_hour: 8,  end_hour: 12, status: 'confirmed', owner_name: 'Ollie' },
      b5:  { id: 'b5',  user_id: 'u34', bay_number: '35', date: d0, start_hour: 9,  end_hour: 18, status: 'confirmed', owner_name: 'Lena' },
      // Tomorrow bookings
      b6:  { id: 'b6',  user_id: 'u4',  bay_number: '12', date: d1, start_hour: 9,  end_hour: 17, status: 'confirmed', owner_name: 'Sarah' },
      b7:  { id: 'b7',  user_id: 'u31', bay_number: '7',  date: d1, start_hour: 8,  end_hour: 15, status: 'confirmed', owner_name: 'Tomek' },
      b8:  { id: 'b8',  user_id: 'u32', bay_number: '45', date: d1, start_hour: 10, end_hour: 14, status: 'confirmed', owner_name: 'Emma' },
      b9:  { id: 'b9',  user_id: 'u33', bay_number: '3',  date: d1, start_hour: 9,  end_hour: 18, status: 'confirmed', owner_name: 'Priya' },
      b10: { id: 'b10', user_id: 'u34', bay_number: '16', date: d1, start_hour: 6,  end_hour: 12, status: 'confirmed', owner_name: 'Wei' },
      b11: { id: 'b11', user_id: 'u4',  bay_number: '5',  date: d1, start_hour: 10, end_hour: 16, status: 'confirmed', owner_name: 'Ollie' },
      // Day 2 bookings
      b12: { id: 'b12', user_id: 'u31', bay_number: '20', date: d2, start_hour: 9,  end_hour: 17, status: 'confirmed', owner_name: 'Fatima' },
      b13: { id: 'b13', user_id: 'u32', bay_number: '7',  date: d2, start_hour: 8,  end_hour: 18, status: 'confirmed', owner_name: 'Tomek' },
      b14: { id: 'b14', user_id: 'u33', bay_number: '35', date: d2, start_hour: 9,  end_hour: 18, status: 'confirmed', owner_name: 'Lena' },
      b15: { id: 'b15', user_id: 'u34', bay_number: '31', date: d2, start_hour: 8,  end_hour: 20, status: 'confirmed', owner_name: 'Yuki' },
      // Day 3 bookings
      b16: { id: 'b16', user_id: 'u4',  bay_number: '3',  date: d3, start_hour: 8,  end_hour: 14, status: 'confirmed', owner_name: 'Priya' },
      b17: { id: 'b17', user_id: 'u31', bay_number: '12', date: d3, start_hour: 9,  end_hour: 17, status: 'confirmed', owner_name: 'Sarah' },
      b18: { id: 'b18', user_id: 'u32', bay_number: '45', date: d3, start_hour: 10, end_hour: 15, status: 'confirmed', owner_name: 'Emma' },
      // Day 4-6 bookings
      b19: { id: 'b19', user_id: 'u33', bay_number: '35', date: d4, start_hour: 9,  end_hour: 18, status: 'confirmed', owner_name: 'Lena' },
      b20: { id: 'b20', user_id: 'u34', bay_number: '7',  date: d4, start_hour: 8,  end_hour: 16, status: 'confirmed', owner_name: 'Tomek' },
      b21: { id: 'b21', user_id: 'u4',  bay_number: '20', date: d5, start_hour: 9,  end_hour: 17, status: 'confirmed', owner_name: 'Fatima' },
      b22: { id: 'b22', user_id: 'u31', bay_number: '5',  date: d5, start_hour: 8,  end_hour: 18, status: 'confirmed', owner_name: 'Ollie' },
      b23: { id: 'b23', user_id: 'u32', bay_number: '3',  date: d6, start_hour: 9,  end_hour: 15, status: 'confirmed', owner_name: 'Priya' },
      // A cancelled booking for variety
      b24: { id: 'b24', user_id: 'u33', bay_number: '12', date: d0, start_hour: 9,  end_hour: 17, status: 'cancelled', owner_name: 'Sarah' },
    },
  }
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  const state = getDefaultState()
  saveState(state)
  return state
}

function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function getSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return null
}

function setSession(data) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(data))
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY)
}

// ---- delay to simulate network ----
function delay(ms = 100) {
  return new Promise((r) => setTimeout(r, ms))
}

function mockError(message, status = 400) {
  const err = new Error(message)
  err.status = status
  err.body = { detail: message }
  throw err
}

// ---- bay helpers ----
function findOwnerByBay(state, bayNumber) {
  return Object.values(state.users).find((u) => u.is_owner && u.bay_number === bayNumber)
}

function getAvailabilityForBay(state, bayNumber, dateStr) {
  const owner = findOwnerByBay(state, bayNumber)
  if (!owner) return null

  const day = dayOfWeek(dateStr)
  const availabilities = Object.values(state.availabilities).filter((a) => a.user_id === owner.id)

  for (const avail of availabilities) {
    if (avail.paused) continue

    if (avail.type === 'one_off' && avail.date === dateStr) {
      return { start: avail.start_hour, end: avail.end_hour, owner }
    }

    if (avail.type === 'recurring') {
      if (avail.exclusions && avail.exclusions.includes(dateStr)) continue
      const dayHours = avail.pattern && avail.pattern[day]
      if (dayHours) return { start: dayHours.start, end: dayHours.end, owner }
    }
  }
  return null
}

function isBayBookedForRange(state, bayNumber, dateStr, start, end) {
  return Object.values(state.bookings).some(
    (b) => b.bay_number === bayNumber && b.date === dateStr && b.status === 'confirmed' &&
      b.start_hour < end && b.end_hour > start
  )
}

// ---- mock API ----
export const api = {
  auth: {
    async requestOTP(email) {
      await delay()
      setSession({ email, otpPending: true })
      return { expires_in: 300 }
    },

    async verifyOTP(email, code) {
      await delay()
      if (!code || code.length !== 6) mockError('Invalid code')
      const state = loadState()
      const user = Object.values(state.users).find((u) => u.email === email)
      setSession({ email, userId: user ? user.id : null, authenticated: true })
      return { is_new_user: !user }
    },

    async logout() {
      await delay()
      clearSession()
      return null
    },
  },

  users: {
    async me() {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const user = state.users[session.userId]
      if (!user) mockError('Not authenticated', 401)
      return { ...user }
    },

    async register(data) {
      await delay()
      const session = getSession()
      if (!session || !session.email) mockError('No session', 401)
      const state = loadState()
      const id = 'u' + generateId()
      const user = {
        id,
        email: session.email,
        phone: data.phone || '+44',
        name: data.name,
        is_owner: data.is_owner || false,
        bay_number: data.bay_number || null,
        credits: 20,
        availability_permission: data.availability_permission || 'anyone',
      }
      state.users[id] = user
      saveState(state)
      setSession({ ...session, userId: id })
      return { ...user }
    },

    async update(data) {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const user = state.users[session.userId]
      if (!user) mockError('User not found', 404)
      Object.assign(user, {
        name: data.name ?? user.name,
        is_owner: data.is_owner ?? user.is_owner,
        bay_number: data.bay_number !== undefined ? data.bay_number : user.bay_number,
        availability_permission: data.availability_permission ?? user.availability_permission,
      })
      saveState(state)
      return { ...user }
    },

    async credits() {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const user = state.users[session.userId]
      // Compute hours used (bookings made by this user) and hours contributed (bookings on this user's bay)
      let hoursUsed = 0
      let hoursContributed = 0
      for (const b of Object.values(state.bookings)) {
        if (b.status === 'cancelled') continue
        const hours = b.end_hour - b.start_hour
        if (b.user_id === session.userId) hoursUsed += hours
        if (user && user.is_owner && user.bay_number === b.bay_number && b.user_id !== session.userId) {
          hoursContributed += hours
        }
      }
      return { credits: user ? user.credits : 0, hours_used: hoursUsed, hours_contributed: hoursContributed }
    },
  },

  availability: {
    async mine() {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      return Object.values(state.availabilities).filter((a) => a.user_id === session.userId)
    },

    async setRecurring(data) {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      // Find or create recurring
      let existing = Object.values(state.availabilities).find(
        (a) => a.user_id === session.userId && a.type === 'recurring'
      )
      if (existing) {
        existing.pattern = data.pattern
      } else {
        const id = 'a' + generateId()
        state.availabilities[id] = {
          id, user_id: session.userId, type: 'recurring', paused: false,
          exclusions: [], pattern: data.pattern,
        }
      }
      saveState(state)
      return { ok: true }
    },

    async addOneOff(data) {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const id = 'a' + generateId()
      state.availabilities[id] = {
        id, user_id: session.userId, type: 'one_off', paused: false,
        date: data.date, start_hour: data.start_hour, end_hour: data.end_hour,
      }
      saveState(state)
      return { id }
    },

    async remove(id) {
      await delay()
      const state = loadState()
      delete state.availabilities[id]
      saveState(state)
      return null
    },

    async togglePause(id) {
      await delay()
      const state = loadState()
      const avail = state.availabilities[id]
      if (avail) avail.paused = !avail.paused
      saveState(state)
      return null
    },

    async addExclusion(date) {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const recurring = Object.values(state.availabilities).find(
        (a) => a.user_id === session.userId && a.type === 'recurring'
      )
      if (recurring) {
        if (!recurring.exclusions) recurring.exclusions = []
        if (!recurring.exclusions.includes(date)) recurring.exclusions.push(date)
        saveState(state)
      }
      return { ok: true }
    },

    async removeExclusion(date) {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const recurring = Object.values(state.availabilities).find(
        (a) => a.user_id === session.userId && a.type === 'recurring'
      )
      if (recurring && recurring.exclusions) {
        recurring.exclusions = recurring.exclusions.filter((d) => d !== date)
        saveState(state)
      }
      return { ok: true }
    },
  },

  map: {
    async bays() {
      await delay()
      return baysData
    },

    async status(date, start, end) {
      await delay()
      const state = loadState()
      const session = getSession()
      const currentUserId = session?.userId || null

      const bayStatuses = baysData.bays.map((bay) => {
        const owner = findOwnerByBay(state, bay.number)
        const avail = getAvailabilityForBay(state, bay.number, date)
        const booked = isBayBookedForRange(state, bay.number, date, start, end)

        let status = 'unavailable'
        if (owner && owner.id === currentUserId) {
          status = 'own'
        } else if (avail) {
          const overlapStart = Math.max(avail.start, start)
          const overlapEnd = Math.min(avail.end, end)
          if (overlapStart < overlapEnd) {
            status = booked ? 'booked' : 'available'
          }
        }

        return {
          ...bay,
          status,
          owner_name: avail ? avail.owner.name : null,
          available_start: avail ? avail.start : null,
          available_end: avail ? avail.end : null,
        }
      })
      return { bays: bayStatuses }
    },
  },

  browse: {
    async available(date, start, end) {
      await delay()
      const state = loadState()
      const slots = []

      for (const bay of baysData.bays) {
        const avail = getAvailabilityForBay(state, bay.number, date)
        if (!avail) continue
        const overlapStart = Math.max(avail.start, start)
        const overlapEnd = Math.min(avail.end, end)
        if (overlapStart >= overlapEnd) continue
        if (isBayBookedForRange(state, bay.number, date, start, end)) continue

        slots.push({
          bay_number: bay.number,
          level: bay.level,
          available_start: avail.start,
          available_end: avail.end,
          owner_name: avail.owner.name,
        })
      }

      return { slots }
    },
  },

  bookings: {
    async create(data) {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const user = state.users[session.userId]
      if (!user) mockError('User not found', 404)

      const hours = data.end_hour - data.start_hour
      if (hours <= 0) mockError('Invalid time range')
      if (user.credits < hours) mockError('Insufficient credits')

      if (isBayBookedForRange(state, data.bay_number, data.date, data.start_hour, data.end_hour)) {
        mockError('Bay already booked for this time')
      }

      const owner = findOwnerByBay(state, data.bay_number)
      const id = 'b' + generateId()
      state.bookings[id] = {
        id,
        user_id: session.userId,
        bay_number: data.bay_number,
        date: data.date,
        start_hour: data.start_hour,
        end_hour: data.end_hour,
        status: 'confirmed',
        owner_name: owner ? owner.name : null,
      }
      user.credits -= hours
      if (owner) owner.credits += hours
      saveState(state)
      return { ...state.bookings[id] }
    },

    async mine() {
      await delay()
      const session = getSession()
      if (!session || !session.userId) mockError('Not authenticated', 401)
      const state = loadState()
      const bookings = Object.values(state.bookings)
        .filter((b) => b.user_id === session.userId)
        .sort((a, b) => b.date.localeCompare(a.date))
      return { bookings }
    },

    async extend(id, hours) {
      await delay()
      const state = loadState()
      const booking = state.bookings[id]
      if (!booking) mockError('Booking not found', 404)
      booking.end_hour += hours
      const session = getSession()
      if (session && session.userId) {
        const user = state.users[session.userId]
        if (user) user.credits -= hours
      }
      saveState(state)
      return { ...booking }
    },

    async reduce(id, hours) {
      await delay()
      const state = loadState()
      const booking = state.bookings[id]
      if (!booking) mockError('Booking not found', 404)
      booking.end_hour -= hours
      const session = getSession()
      if (session && session.userId) {
        const user = state.users[session.userId]
        if (user) user.credits += hours
      }
      saveState(state)
      return { ...booking }
    },

    async cancel(id) {
      await delay()
      const state = loadState()
      const booking = state.bookings[id]
      if (!booking) mockError('Booking not found', 404)
      const hours = booking.end_hour - booking.start_hour
      booking.status = 'cancelled'
      const session = getSession()
      if (session && session.userId) {
        const user = state.users[session.userId]
        if (user) user.credits += hours
      }
      saveState(state)
      return null
    },
  },
}
