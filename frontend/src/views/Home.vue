<template>
  <div class="home">
    <!-- ═══════════════════════════════════════════════ -->
    <!-- BACKGROUND IMAGE — full-bleed, edge-to-edge     -->
    <!-- ═══════════════════════════════════════════════ -->
    <div class="home-bg" aria-hidden="true">
      <img
        :src="bgImage"
        alt=""
        class="home-bg__image"
        loading="eager"
        @error="onBgError"
      />
      <div class="home-bg__overlay"></div>
    </div>

    <!-- ═══════════════════════════════════════════════ -->
    <!-- CONTENT — everything floats on the image        -->
    <!-- ═══════════════════════════════════════════════ -->
    <div class="home-layer">
      <!-- Headline -->
      <header class="home-headline">
        <h1>Every Stay<br/>feels like home</h1>
        <p>Discover extraordinary stays, effortlessly.</p>
      </header>

      <!-- Search Bar — floating glass module -->
      <SearchBar />

      <!-- Dual Entry Cards — floating glass modules -->
      <div class="home-entries">
        <EntryCard
          variant="booking"
          title="Already know where to stay?"
          description="Search by city, name, or room type."
          action-text="Start Booking"
          @action="goToBookingExplore"
        />
        <EntryCard
          variant="ai"
          title="Let AI find the perfect stay."
          description="Tell us your style and preferences."
          action-text="Ask AI"
          @action="goToAssistant"
        />
      </div>
    </div>

    <!-- Trust strip — minimal, bottom edge -->
    <div class="home-trust">
      <TrustStrip />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import SearchBar from '../components/home/SearchBar.vue'
import EntryCard from '../components/home/EntryCard.vue'
import TrustStrip from '../components/home/TrustStrip.vue'

const router = useRouter()

const BG_IMAGES = [
  'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=1920&q=80',
  'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1920&q=80',
  'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=1920&q=80',
]

const bgImage = ref(BG_IMAGES[0])
let fallbackIdx = 0

const onBgError = () => {
  fallbackIdx++
  if (fallbackIdx < BG_IMAGES.length) {
    bgImage.value = BG_IMAGES[fallbackIdx]
  }
}

const goToBookingExplore = () => router.push('/simple-booking')
const goToAssistant = () => router.push('/assistant')
</script>

<style scoped>
/* ═══════════════════════════════════════════════ */
/* CONTAINER — the page IS the hero              */
/* ═══════════════════════════════════════════════ */
.home {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #1a100c; /* dark fallback — never shows white */
}

/* ═══════════════════════════════════════════════ */
/* BACKGROUND — fixed to cover entire window      */
/* ═══════════════════════════════════════════════ */
.home-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  width: 100vw;
  height: 100vh;
  background-color: #1a100c; /* prevents white flash before image loads */
}

.home-bg__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 40%;
  filter: saturate(0.95);
}

.home-bg__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.35) 0%,
    rgba(0, 0, 0, 0.18) 25%,
    rgba(0, 0, 0, 0.12) 45%,
    rgba(0, 0, 0, 0.28) 70%,
    rgba(0, 0, 0, 0.50) 100%
  );
}

/* ═══════════════════════════════════════════════ */
/* CONTENT LAYER — floats above background        */
/* ═══════════════════════════════════════════════ */
.home-layer {
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  padding: 100px 24px 48px;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

/* ── Headline ── */
.home-headline {
  text-align: center;
  max-width: 800px;
}

.home-headline h1 {
  margin: 0;
  font-size: clamp(52px, 8vw, 96px);
  font-weight: 800;
  line-height: 1.04;
  letter-spacing: -0.03em;
  color: #fff;
  text-shadow: 0 4px 80px rgba(0, 0, 0, 0.40);
}

.home-headline p {
  margin: 14px 0 0;
  font-size: clamp(15px, 1.8vw, 20px);
  font-weight: 400;
  color: rgba(255, 255, 255, 0.78);
  text-shadow: 0 1px 30px rgba(0, 0, 0, 0.25);
  letter-spacing: 0.01em;
}

/* ── Entry Cards Row ── */
.home-entries {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  width: 100%;
  max-width: 880px;
}

/* ── Trust Strip ── */
.home-trust {
  position: relative;
  z-index: 2;
  margin-top: auto;
}

/* ═══════════════════════════════════════════════ */
/* RESPONSIVE                                    */
/* ═══════════════════════════════════════════════ */
@media (max-width: 860px) {
  .home-layer {
    gap: 22px;
    padding: 90px 20px 36px;
  }

  .home-entries {
    grid-template-columns: 1fr;
    max-width: 480px;
  }

  .home-headline h1 {
    font-size: clamp(32px, 9vw, 52px);
  }
}

@media (max-width: 540px) {
  .home-layer {
    padding: 80px 16px 28px;
    gap: 18px;
  }

  .home-headline h1 {
    font-size: 30px;
  }

  .home-headline p {
    font-size: 14px;
  }
}

/* short viewport — reduce gaps to fit */
@media (max-height: 720px) {
  .home-layer {
    gap: 16px;
    padding-top: 80px;
  }

  .home-headline h1 {
    font-size: clamp(28px, 5.5vw, 56px);
  }

  .home-entries {
    gap: 12px;
  }
}
</style>
