<template>
  <div class="linechart">
    <Line v-if="loaded" :data="data" :options="options" />
  </div>
</template>

<script>
import {useFetchDataStore} from "@/stores/FetchDataStore.js";
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
  mounted() {
    const b=useFetchDataStore();
    console.log(b.idok2)

    this.data.labels=b._idok2;
    this.data.datasets[0].data=b.fesz2;

    this.loaded=true;
  },

  data() {
    return {
      _idok2:[],
      _fesz2:[],  
      
      loaded:false,
      data:{
        labels: [],
        datasets: [
        {
          label: 'Töltési görbe',
          backgroundColor: '#e56464',
          borderColor: '#e5a4a4',
          pointRadius: 5,
          fill: false,
          data: []
        }]
      }
    };
  },
  computed: {
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
  position: relative;
}
</style>