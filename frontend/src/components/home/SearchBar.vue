<template>
  <div class="search-bar">
    <!-- Destination -->
    <div class="search-field search-field--dest">
      <label class="search-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        Destination
      </label>
      <input
        v-model="destination"
        type="text"
        placeholder="Where are you going?"
        class="search-input"
      />
    </div>

    <div class="search-divider"></div>

    <!-- Check-in -->
    <div class="search-field">
      <label class="search-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        Check-in
      </label>
      <input v-model="checkIn" type="date" class="search-input" />
    </div>

    <div class="search-divider"></div>

    <!-- Check-out -->
    <div class="search-field">
      <label class="search-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        Check-out
      </label>
      <input v-model="checkOut" type="date" class="search-input" />
    </div>

    <div class="search-divider"></div>

    <!-- Guests -->
    <div class="search-field search-field--guests">
      <label class="search-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        Guests
      </label>
      <select v-model="guests" class="search-input search-select">
        <option v-for="n in 6" :key="n" :value="n">{{ n }} guest{{ n > 1 ? 's' : '' }}</option>
      </select>
    </div>

    <!-- CTA -->
    <button class="search-cta" @click="handleSearch">
      立即预订
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const destination = ref('')
const checkIn = ref('')
const checkOut = ref('')
const guests = ref(2)

const handleSearch = () => {
  const query = {}
  if (destination.value.trim()) query.destination = destination.value.trim()
  if (checkIn.value) query.checkIn = checkIn.value
  if (checkOut.value) query.checkOut = checkOut.value
  if (guests.value) query.guests = guests.value
  router.push({ name: 'SimpleBooking', query })
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════ */
/* GLASS CARD — floats inside the hero scene      */
/* ═══════════════════════════════════════════════ */
.search-bar {
  display: flex;
  align-items: center;
  gap: 0;
  width: 100%;
  max-width: 920px;
  padding: 12px;
  border-radius: 22px;
  /* Deep glassmorphism */
  background: rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(40px) saturate(1.3);
  -webkit-backdrop-filter: blur(40px) saturate(1.3);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.18),
    0 2px 8px rgba(0, 0, 0, 0.10),
    inset 0 1px 0 rgba(255, 255, 255, 0.10);
  transition: all 0.35s ease;
}

.search-bar:focus-within {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.30);
  box-shadow:
    0 16px 50px rgba(0, 0, 0, 0.22),
    0 2px 8px rgba(0, 0, 0, 0.10),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

/* ── Field ── */
.search-field {
  flex: 1;
  min-width: 0;
  padding: 12px 20px;
}

.search-field--dest { flex: 1.4; }
.search-field--guests { flex: 0.55; }

/* ── Label ── */
.search-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 5px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.50);
  pointer-events: none;
}

/* ── Input ── */
.search-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  padding: 4px 0;
  line-height: 1.4;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.35);
}

.search-input[type="date"] {
  color-scheme: dark;
  cursor: pointer;
}

.search-input[type="date"]::-webkit-calendar-picker-indicator {
  filter: invert(1);
  opacity: 0.6;
  cursor: pointer;
}

/* ── Select ── */
.search-select {
  cursor: pointer;
  appearance: none;
  background: transparent;
}

.search-select option {
  color: #3f312c;
  background: #fff;
}

/* ── Divider ── */
.search-divider {
  width: 1px;
  height: 42px;
  background: rgba(255, 255, 255, 0.14);
  flex-shrink: 0;
}

/* ── CTA Button ── */
.search-cta {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 18px 32px;
  border: none;
  border-radius: 18px;
  background: linear-gradient(135deg, #d0845a, #b56540);
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: all 0.28s ease;
  box-shadow: 0 10px 34px rgba(0, 0, 0, 0.32);
  white-space: nowrap;
  flex-shrink: 0;
}

.search-cta:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.42);
  background: linear-gradient(135deg, #da8e64, #c06b42);
}

.search-cta:active {
  transform: translateY(0);
}

/* ── Responsive ── */
@media (max-width: 860px) {
  .search-bar {
    flex-wrap: wrap;
    padding: 14px;
    gap: 4px 0;
  }

  .search-field {
    flex: 1 1 45%;
    padding: 10px 14px;
  }

  .search-divider { display: none; }

  .search-cta {
    width: 100%;
    justify-content: center;
    margin-top: 8px;
    border-radius: 14px;
  }
}

@media (max-width: 540px) {
  .search-field,
  .search-field--guests {
    flex: 1 1 100%;
  }
}
</style>
