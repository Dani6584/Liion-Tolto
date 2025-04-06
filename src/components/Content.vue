<template>
<div v-if="loaded" class="m-5">
    <!--Általános-->
    <div class="bg-base-300 rounded-box p-5">
        <div class="grid lg:grid-cols-4 md:grid-cols-3 sm:grid-cols-1 gap-0 md:flex-wrap sm:flex-wrap">

            <div class="col-span-1">
                <div class = "t" v-if="feszultseg != undefined">{{ feszultseg }} V</div>
                <div class = "t dots" v-else="feszultseg == undefined"></div>
                <div class = "d">Mért feszültség</div>
            </div>

            <!--
            <div class="col-span-1">
                <div class = "t" v-if="belso_ellenallas != undefined">{{ belso_ellenallas }} Ω</div>
                <div class = "t dots" v-else="belso_ellenallas == undefined"></div>
                <div class = "d">Belső ellenállás</div>
            </div>-->

            <div class="col-span-1">
                <div class = "t" v-if="discharge_capacity != undefined">{{ discharge_capacity }} mAh</div>
                <div class = "t dots" v-else="discharge_capacity == undefined"></div>
                <div class = "d">Kapacitás</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="discharge_capacity_percentage != undefined">{{ discharge_capacity_percentage }} %</div>
                <div class = "t dots" v-else="discharge_capacity_percentage == undefined"></div>
                <div class = "d">Kapacitás százalékban</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="allapot == 'jo'">Jó</div>
                <div class = "t" v-else-if="allapot == 'rossz'">Rossz</div>
                <div class = "t dots" v-else></div>
                <div class = "d">Cella állapota</div>
            </div>
        </div>
    </div>

    <!--Időintervallumok-->
    <div class="bg-base-300 rounded-box p-5 mt-5">
        <div class="grid lg:grid-cols-6 md:grid-cols-3 sm:grid-cols-1 gap-0 md:flex-wrap sm:flex-wrap">
            <div class="col-span-1">
                <div class = "t" v-if="toltes_kezdes != undefined">{{ datum(toltes_kezdes) }}</div>
                <div class = "t dots" v-else="toltes_kezdes == undefined"></div>
                <div class = "d">Töltés kezdete</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="toltes_vege != undefined">{{ datum(toltes_vege) }}</div>
                <div class = "t dots" v-else="toltes_vege == undefined"></div>
                <div class = "d">Töltés vége</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="merites_kezdes != undefined">{{ datum(merites_kezdes) }}</div>
                <div class = "t dots" v-else="merites_kezdes == undefined"></div>
                <div class = "d">Merítési kezdete</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="merites_vege != undefined">{{ datum(merites_vege) }}</div>
                <div class = "t dots" v-else="merites_vege == undefined"></div>
                <div class = "d">Merítés vége</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="ujratoltes_kezdes != undefined">{{ datum(ujratoltes_kezdes) }}</div>
                <div class = "t dots" v-else="ujratoltes_kezdes == undefined"></div>
                <div class = "d">Újratöltés kezdete</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="ujratoltes_vege != undefined">{{ datum(ujratoltes_vege) }}</div>
                <div class = "t dots" v-else="ujratoltes_vege == undefined"></div>
                <div class = "d">Újratöltés vége</div>
            </div>
        </div>
    </div>

    <div class="flex flex-wrap">
        <div v-if="loaded" class="bg-base-300 rounded-box max-w-md p-5 mt-5 mr-5"><toltes class="h-auto"/></div>
        <div v-if="loaded" class="bg-base-300 rounded-box max-w-md p-5 mt-5 mr-5"><merites class="h-auto"/></div>
        <div v-if="loaded" class="bg-base-300 rounded-box max-w-md p-5 mt-5"><szazalekkor class="h-auto"/></div>
    </div>
</div>
</template>

<script>
import merites from '@/charts/merites.vue';
import toltes from '@/charts/toltes.vue';
import szazalekkor from '@/charts/szazalekkor.vue';
import moment from 'moment/min/moment-with-locales';
import {useFetchDataStore} from "@/stores/FetchDataStore.js";
import {lekeres,legujabblekeres} from "@/appwrite/lekeres.js"

export default {
    components: {
        merites,
        toltes,
        szazalekkor
    },
    mounted() {
        this.leker();
        setInterval(() => {this.leker()}, 5*60000);
    },
    watch: { // leker() fuggvenyt lekeri ha router modositas tortenik
        '$route'(to, from) {
            this.leker();
        }
    },
    data () {
        return {
            feszultseg: null,
            belso_ellenallas: null,
            discharge_capacity: null,
            discharge_capacity_percentage: null,
            allapot: null,
            
            toltes_kezdes: null,
            toltes_vege: null,
            merites_kezdes: null,
            merites_vege: null,
            ujratoltes_kezdes: null,
            ujratoltes_vege: null,

            k: null,
            loaded:false
        }
    },
    methods:{
        async leker()
        {   
            let k=null
            if(this.$route.params.id==null) {
                k=await legujabblekeres()
            }
            else {
                k=this.$route.params.id
            }
            console.log(k)
            await lekeres(k,true)
            
            const a = useFetchDataStore()
            this.feszultseg = a.feszultseg
            this.belso_ellenallas = a.belso_ellenallas
            this.discharge_capacity = a.discharge_capacity
            this.discharge_capacity_percentage = a.discharge_capacity_percentage
            this.allapot = a.allapot
            
            this.toltes_kezdes = a.toltes_kezdes
            this.toltes_vege = a.toltes_vege
            this.merites_kezdes = a.merites_kezdes
            this.merites_vege = a.merites_vege
            this.ujratoltes_kezdes = a.ujratoltes_kezdes
            this.ujratoltes_vege = a.ujratoltes_vege
        
            this.k = k
            this.loaded=true;
        },
        datum(a) {
            moment.locale('hu');
            return moment.utc(a).format('hh:mm');
        }
    },
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
.h {
    color: #a8adbb;
    font-size: 0.875rem;
    font-family: "Inter", sans-serif;
}
.t {
    color: #eeeef1;
    font-size: 1.75rem;
    font-weight: 600;
    font-family: "Poppins", sans-serif;
}
.d {
    color: #c3c3c6;
    font-size: 0.875rem;
    font-family: "Inter", sans-serif;
}
.dots::after {
  content: '';
  display: inline-block;
  width: 1em;
  text-align: left;
  animation: dots 10s infinite;
}

@keyframes dots {
  0%   { content: ''; }
  25%  { content: ''; }
  50%  { content: '.'; }
  75%  { content: '..'; }
  100% { content: '...'; }
}
</style>