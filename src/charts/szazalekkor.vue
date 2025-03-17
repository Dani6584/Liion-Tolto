<template>
    <div>
        <Doughnut height="300px" v-if="loaded" :data="data" :options="options" />
    </div>
</template>

<script>
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import {useFetchDataStore} from "@/stores/FetchDataStore.js"
import moment from 'moment/min/moment-with-locales'

ChartJS.register(ArcElement, Tooltip, Legend)

export default {
    name: 'App',
    components: {
      Doughnut
    },
    mounted() {
        const a=useFetchDataStore()
        let I_avg = 0;
        for (let i = 0; i < a.mcurrent.length; i++) {
            I_avg += a.mcurrent[i]
        }
        I_avg = I_avg / a.mcurrent.length
        console.log('Atlagszamitas: '+I_avg)

        let ido = Math.abs(convert(a.merites_vege) - convert(a.merites_kezdes))
        console.log(ido)

        let mAh = ido * I_avg * 1000
        console.log(mAh)

        this.PmAh = Math.round((mAh / 3400) * 100)
        console.log(this.PmAh)
        
        this.data.datasets[0].data = [this.PmAh, 100 - this.PmAh];
        this.loaded=true

        function convert(a) {
            moment.locale('hu');
            let o = moment(a)

            return o.hour() + (o.minute() / 60)
        }
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