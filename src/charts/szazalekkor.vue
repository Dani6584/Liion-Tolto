<template>
    <div>
        <Doughnut height="300px"  :data="data" :options="options" />
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
        let valami = a.tcurrent;
        console.log(valami);        
    },
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
    }
}
</script>