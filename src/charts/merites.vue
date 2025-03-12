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
    const a=useFetchDataStore();
    console.log(a.idok)

    this.data.labels=a.idok;
    this.data.datasets[0].data=a.fesz;

    this.loaded=true;
  },

  data() {
    return {
      idok:[],
      fesz:[],  
      
      loaded:false,
      data:{
        labels: [],
        datasets: [
        {
          label: 'Merítési görbe',
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