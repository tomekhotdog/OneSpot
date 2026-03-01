# Phase 4: Polish — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add loading states, error handling, animations, responsive verification, and final documentation pass.

**Architecture:** No new features — UX refinements and defensive coding across the existing codebase.

**Tech Stack:** React, Tailwind CSS, CSS transitions

---

### Task 1: Loading States & Skeletons

**Files:**
- Create: `frontend/src/components/Skeleton.jsx`
- Modify: all page components that fetch data

**Step 1: Create Skeleton component**

Animated pulse placeholder matching card/list layouts. Reusable for different shapes (card, text line, circle).

**Step 2: Add loading states to pages**

Each page that fetches data should show Skeleton while loading:
- Home: skeleton cards for bookings + credit display
- MapView: skeleton grid for bays
- MyBookings: skeleton list
- MySpace: skeleton calendar
- Profile: skeleton fields

Pattern:
```jsx
if (loading) return <Skeleton variant="card" count={3} />
```

**Step 3: Commit**

```bash
git add frontend/src/components/Skeleton.jsx frontend/src/pages/
git commit -m "feat: loading skeletons across all data-fetching pages"
```

---

### Task 2: Error Boundaries & User-Friendly Messages

**Files:**
- Create: `frontend/src/components/ErrorBoundary.jsx`
- Create: `frontend/src/components/ErrorMessage.jsx`
- Modify: `frontend/src/App.jsx`

**Step 1: Create ErrorBoundary**

React class component catching render errors. Shows friendly message with "Try Again" button.

**Step 2: Create ErrorMessage**

Reusable inline error display for API failures:
```jsx
<ErrorMessage error={error} onRetry={refetch} />
```

Shows: "Something went wrong" + error detail + retry button.

**Step 3: Wrap App in ErrorBoundary**

**Step 4: Add error handling to all API-calling pages**

Each page: `try/catch` around API calls, display ErrorMessage on failure.

**Step 5: Commit**

```bash
git add frontend/src/components/ErrorBoundary.jsx frontend/src/components/ErrorMessage.jsx frontend/src/App.jsx frontend/src/pages/
git commit -m "feat: error boundaries and user-friendly error messages"
```

---

### Task 3: Animations & Transitions

**Files:**
- Modify: `frontend/src/index.css`
- Modify: various components

**Step 1: Add CSS transitions**

```css
/* Page transitions */
.page-enter { opacity: 0; transform: translateY(8px); }
.page-enter-active { opacity: 1; transform: translateY(0); transition: all 200ms ease-out; }

/* Card appearances */
.card-appear { animation: cardFadeIn 200ms ease-out; }
@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

**Step 2: Apply to components**

- Cards: `className="card-appear"` with staggered delays
- Bottom nav: active indicator transition
- Bay cells: subtle scale on tap feedback
- Buttons: hover/active transitions (already via Tailwind `transition-colors`)

Keep it subtle — build trust, not a game.

**Step 3: Commit**

```bash
git add frontend/src/index.css frontend/src/components/ frontend/src/pages/
git commit -m "feat: subtle animations for page transitions and card appearances"
```

---

### Task 4: Responsive Verification

**Files:**
- Modify: various components as needed

**Step 1: Test at key breakpoints**

Verify in browser dev tools at:
- 375px (iPhone SE) — everything single column, no overflow
- 390px (iPhone 14) — standard mobile
- 430px (iPhone 14 Pro Max) — larger mobile
- 768px (iPad) — content centred, max-width 480px
- 1024px+ (desktop) — centred column

**Step 2: Fix any issues**

Common fixes:
- Map grid horizontal scroll on narrow screens
- Timeline picker overflow handling
- Bottom nav safe area for notched phones (`pb-safe`)
- Font sizes readable at 375px
- Touch targets minimum 44px

**Step 3: Add safe area padding for iOS**

```css
nav { padding-bottom: env(safe-area-inset-bottom); }
```

**Step 4: Commit**

```bash
git add frontend/
git commit -m "fix: responsive layout fixes for 375px+ viewports and iOS safe areas"
```

---

### Task 5: Disclaimer Placement

**Files:**
- Modify: `frontend/src/pages/Signup.jsx`
- Modify: `frontend/src/components/Layout.jsx`

**Step 1: Verify disclaimer appears on:**
- Signup page (prominently, above submit button)
- Footer of every page (small text)
- Booking confirmation screen

**Step 2: Commit if changes needed**

---

### Task 6: Final Documentation Pass

**Files:**
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/DEVELOPMENT.md`
- Modify: `docs/SETUP.md`
- Modify: `README.md`
- Verify all `docs/features/*.md` are complete

**Step 1: Review and update all docs**

Ensure:
- ARCHITECTURE.md reflects actual implementation (not just planned)
- DEVELOPMENT.md has accurate commands
- SETUP.md env vars match actual code
- Feature docs match implemented behaviour
- README quick start works end-to-end

**Step 2: Commit**

```bash
git add docs/ README.md
git commit -m "docs: final documentation pass — updated to match implementation"
```

---

### Task 7: Final Test Run & Tag

**Step 1: Run all tests**

```bash
pytest -v
cd frontend && npm test
```

**Step 2: Build frontend**

```bash
cd frontend && npm run build
```

**Step 3: Start full stack and manual smoke test**

```bash
uvicorn backend.main:app --reload
```

Visit localhost:8000. Walk through: signup → declare availability → browse map → book → cancel.

**Step 4: Tag release**

```bash
git tag v1.0.0
```
