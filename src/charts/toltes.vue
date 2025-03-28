<template>
  <div>
    <Line style="align-items: center" height="300px" :data="data" :options="options"/>
  </div>
</template>

<script>
import {useFetchDataStore} from "@/stores/FetchDataStore.js"
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
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

export default {
  name: "Toltes",
  components: {
    Line
  },
  computed: {
    data() {
      const store = useFetchDataStore();
      return {
        labels: store.idok2,
        datasets: [
          {
            label: 'Feszültség',
            borderColor: '#46e62d',
            backgroundColor: '#1e820f',
            pointRadius: 5,
            fill: false,
            data: store.fesz2
          },
          {
            label: 'Áram',
            borderColor: '#f56e6e',
            backgroundColor: '#c74c4c',
            pointRadius: 5,
            fill: false,
            data: store.tcurrent
          }
        ]
      };
    },
    options() {
      return {
        responsive: true,
        maintainAspectRatio: true,
        
        scales: {
          x: { title:{display: true, text: 'Eltelt Idő', color: '#c3c3c6'}, ticks:{color: '#a8adbb'}, grid:{color: '#5a5e66'}},
          y: { title:{display: true, text: 'Feszültség / Áram', color: '#c3c3c6'}, ticks:{color: '#a8adbb'}, grid:{color: '#5a5e66'}}
        },
        plugins: {
          title: {display: true, text: 'Töltési görbe', color: '#eeeef1', font: {family: 'Poppins', weight: '400', size: 20}},
          legend:  {labels:{color: '#c3c3c6', font: { family: 'Poppins', weight: '400', size: 15}}},
          tooltip: {labels:{color: '#a8adbb'}}
          
        }
      }
    }
  }
}
</script>

<style>
</style>
