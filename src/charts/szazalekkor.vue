<template>
    <div class = "size">
        <Doughnut :data="data" :options="options" />
    </div>
</template>

<script>
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend)

export default {
  name: 'App',
  components: {
    Doughnut
  },

  // Config
  data() {
    return {
        data: {
            labels: [],
            datasets: [
                {
                    borderColor: ['#1e820f', '#16191E'],
                    backgroundColor: ['#46e62d', '#16191E'],
                    borderWidth: 5,
                    data: [10, 100-10] 
                }
            ]
        },
    }
  },

  computed: {
    options() {
        return{
            responsive: true,
            maintainAspectRatio: false,
            
            rotation: -90,
            circumference: 180,
            hover: { mode: null },
            plugins: {
                title: { display: true, text: 'Szazalek', color: '#eeeef1', font: { family: 'Poppins', weight: '400', size: 20}},

                legend:  { display: false },
                tooltip: { enabled: false }
            }
        }
    }
  }
}
</script>

<style scoped>
.size {
    width: 400px;
    height: auto;
}
</style>