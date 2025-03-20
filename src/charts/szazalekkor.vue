<template>
    <div>
        <Doughnut height="300px" v-if="loaded" :data="data" :options="options" />
    </div>
</template>

<script>
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import {useFetchDataStore} from "@/stores/FetchDataStore.js"
ChartJS.register(ArcElement, Tooltip, Legend)

export default {
    name: 'App',
    components: {
      Doughnut
    },
    mounted() {
        const a=useFetchDataStore()

        this.PmAh = a.kapacitas_szazalek
        console.log(this.PmAh)
        
        this.data.datasets[0].data = [this.PmAh, 100 - this.PmAh];
        this.loaded=true
    },
    
    data() {
        return {
            PmAh: null,
            loaded:false,
            data: {
                labels: [],
                datasets: [
                {
                    borderColor: ['#1e820f', '#16191E'],
                    backgroundColor: ['#46e62d', '#16191E'],
                    borderWidth: 5,
                    data: [0, 0]
                }]
            },
        }
    },  
    computed: {
        options() {
            return{
                responsive: true,
                maintainAspectRatio: true,

                rotation: -90,
                circumference: 180,
                hover: { mode: null },
                plugins: {
                    title: { display: true, text: 'Szazalek', color: '#eeeef1', font: { family: 'Poppins', weight: '400', size: 20}}, 
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        }
    },
}
</script>