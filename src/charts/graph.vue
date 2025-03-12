<template>
  <div class="linechart">
    <Line v-if="loaded" :data="data" :options="options" />
  </div>
</template>

<script>
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'vue-chartjs';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default {
  name: "Graph",
  components: {
    Line
  },

  props: {
    feszultsegek: [{ type: Array, required: true }],
    idok: [{ type: Array, required: true }],
    loaded: false
  },

  computed: {
    data() {
      return {
        labels: this.idok,
        datasets: [
          {
            label: 'Merítési görbe',
            backgroundColor: '#e56464',
            borderColor: '#e5a4a4',
            pointRadius: 5,

            fill: false,
            data: this.feszultsegek
          }
        ]
      };
    },

    options() {
      return {
        responsive: true,
        maintainAspectRatio: true,

        scales: {
          x: { title:{display: true, text: 'Eltelt Idő', color: '#a6adbb'}, ticks:{color: '#a6adbb'}, grid:{color: '#5a5e66'}},
          y: { title:{display: true, text: 'Feszültség', color: '#a6adbb'}, ticks:{color: '#a6adbb'}, grid:{color: '#5a5e66'}}
        },

        plugins: {
          legend:  {labels:{color: '#a6adbb'}},
          tooltip: {labels:{color: '#a6adbb'}}  
        }

      };
    }
  }
};
</script>

<style>
.linechart {
  max-width: 800px;
  position: relative; /* Required for Chart.js responsiveness */
}
</style>