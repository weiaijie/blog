<template>
  <div class="lw-wrap">
    <div class="lw-stage" role="group" :aria-label="wheelAriaLabel">
      <div ref="wheel" class="lw-wheel" :style="wheelStyle"></div>
      <div class="lw-pointer" aria-hidden="true"></div>
      <button class="lw-btn" type="button" :disabled="spinning" @click="onStart">
        {{ spinning ? spinningText : startText }}
      </button>
    </div>
    <div v-if="tip" class="lw-tip" aria-live="polite">{{ tip }}</div>
  </div>
</template>

<script>
export default {
  name: "LuckyWheel",
  props: {
    // [{ id: "A", name: "First", centerDeg: 0 }, ...]
    prizes: {
      type: Array,
      required: true
    },
    // Must return Promise<{ prizeId: string }>
    drawApi: {
      type: Function,
      required: true
    },
    duration: { type: Number, default: 5200 },
    minTurns: { type: Number, default: 6 },
    randomOffsetDeg: { type: Number, default: 6 },
    startText: { type: String, default: "Spin" },
    spinningText: { type: String, default: "Spinning..." },
    errorText: { type: String, default: "Draw failed, try again." },
    wheelAriaLabel: { type: String, default: "Lucky wheel" }
  },
  data() {
    return {
      spinning: false,
      tip: "",
      currentDeg: 0,
      rafId: 0,
      startTs: 0,
      targetDeg: 0
    };
  },
  computed: {
    wheelStyle() {
      return {
        transform: "rotate(" + this.currentDeg + "deg)"
      };
    }
  },
  beforeDestroy() {
    if (this.rafId) cancelAnimationFrame(this.rafId);
  },
  methods: {
    normalizeDeg(deg) {
      const mod = deg % 360;
      return (mod + 360) % 360;
    },
    getSafeOffsetDeg(prize) {
      const max = Math.abs(this.randomOffsetDeg || 0);
      if (!max) return 0;

      const center = this.normalizeDeg(Number(prize.centerDeg || 0));
      const centers = this.prizes.map(p =>
        this.normalizeDeg(Number(p.centerDeg || 0))
      );

      const sorted = centers.slice().sort((a, b) => a - b);
      const idx = sorted.findIndex(c => Math.abs(c - center) < 1e-6);
      if (idx === -1 || sorted.length < 2) {
        return (Math.random() * 2 - 1) * max;
      }

      const left = sorted[(idx - 1 + sorted.length) % sorted.length];
      const right = sorted[(idx + 1) % sorted.length];
      const gapLeft = this.normalizeDeg(center - left);
      const gapRight = this.normalizeDeg(right - center);
      const minGap = Math.min(gapLeft, gapRight);

      // Keep a 1deg safety margin away from segment borders.
      const safeMax = Math.max(0, Math.min(max, minGap / 2 - 1));
      if (!safeMax) return 0;
      return (Math.random() * 2 - 1) * safeMax;
    },
    async onStart() {
      if (this.spinning) return;
      this.tip = "";
      this.spinning = true;

      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = 0;
      }

      try {
        const res = await this.drawApi();
        const prizeId = res && res.prizeId;
        const prize = this.prizes.find(p => p.id === prizeId);
        if (!prize) throw new Error("Unknown prizeId: " + prizeId);

        const landing = this.normalizeDeg(360 - this.normalizeDeg(prize.centerDeg));
        const offset = this.getSafeOffsetDeg(prize);
        const extraTurns = Math.max(0, this.minTurns) * 360;

        const curMod = this.normalizeDeg(this.currentDeg);
        const deltaToLanding = this.normalizeDeg(landing - curMod);

        this.targetDeg = this.currentDeg + extraTurns + deltaToLanding + offset;
        this.startTs = 0;
        this.animateToTarget(prize);
      } catch (e) {
        this.tip = this.errorText;
        this.spinning = false;
        this.$emit("error", e);
      }
    },
    animateToTarget(prize) {
      const easeOutCubic = t => 1 - Math.pow(1 - t, 3);

      const from = this.currentDeg;
      const to = this.targetDeg;
      const dur = this.duration;

      const step = ts => {
        if (!this.startTs) this.startTs = ts;
        const elapsed = ts - this.startTs;
        const t = Math.min(1, elapsed / dur);
        const p = easeOutCubic(t);

        this.currentDeg = from + (to - from) * p;

        if (t < 1) {
          this.rafId = requestAnimationFrame(step);
        } else {
          this.currentDeg = to;
          this.spinning = false;
          this.rafId = 0;

          this.$emit("finish", {
            prizeId: prize.id,
            prizeName: prize.name,
            finalDeg: this.currentDeg
          });
        }
      };

      this.rafId = requestAnimationFrame(step);
    }
  }
};
</script>

<style scoped>
.lw-wrap {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  user-select: none;
}

.lw-stage {
  position: relative;
  width: 280px;
  height: 280px;
}

.lw-wheel {
  position: absolute;
  left: 0;
  top: 0;
  width: 280px;
  height: 280px;
  background: url("../assets/wheel.svg") center/contain no-repeat;
  transform-origin: 50% 50%;
  will-change: transform;
  backface-visibility: hidden;
}

.lw-pointer {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 86px;
  height: 86px;
  transform: translate(-50%, -70%);
  background: url("../assets/pointer.svg") center/contain no-repeat;
  pointer-events: none;
}

.lw-btn {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -20%);
  width: 120px;
  height: 40px;
  border: 0;
  border-radius: 20px;
  font-size: 14px;
  background: #ffcc33;
  cursor: pointer;
}

.lw-btn:disabled {
  opacity: 0.7;
  cursor: default;
}

.lw-tip {
  margin-top: 10px;
  font-size: 14px;
}
</style>
