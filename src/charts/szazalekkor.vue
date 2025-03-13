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
                    label: 'Szazalek',
                    borderColor: ['#1e820f'],
                    backgroundColor: ['#46e62d'],
                    borderWidth: 5,
                    data: [100]
                }
            ]
        },
        
        options : {
            responsive: true,
            maintainAspectRatio: false,
            
            rotation: -90,
            circumference: 180,
            
            plugins: {
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