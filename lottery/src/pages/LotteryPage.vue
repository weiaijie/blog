<template>
  <div class="lottery-page">
    <LuckyWheel
      :prizes="prizes"
      :drawApi="drawApi"
      :duration="5200"
      :minTurns="6"
      :randomOffsetDeg="6"
      @finish="onFinish"
      @error="onError"
    />
    <div v-if="result" class="lottery-result">Result: {{ result }}</div>
  </div>
</template>

<script>
import LuckyWheel from "../components/LuckyWheel.vue";

export default {
  components: { LuckyWheel },
  data() {
    return {
      result: "",
      prizes: [
        { id: "A", name: "First Prize", centerDeg: 0 },
        { id: "B", name: "Second Prize", centerDeg: 60 },
        { id: "C", name: "Third Prize", centerDeg: 120 },
        { id: "D", name: "Thanks", centerDeg: 180 },
        { id: "E", name: "Coupon", centerDeg: 240 },
        { id: "F", name: "Gift", centerDeg: 300 }
      ]
    };
  },
  methods: {
    async drawApi() {
      const list = this.prizes.map(p => p.id);
      const prizeId = list[Math.floor(Math.random() * list.length)];

      return new Promise(resolve => {
        setTimeout(() => resolve({ prizeId }), 300);
      });
    },
    onFinish(payload) {
      this.result = payload.prizeName + " (" + payload.prizeId + ")";
    },
    onError() {
      this.result = "";
    }
  }
};
</script>

<style scoped>
.lottery-page {
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.lottery-result {
  margin-top: 12px;
  font-size: 14px;
}
</style>
