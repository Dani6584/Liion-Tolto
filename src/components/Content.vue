<template>
<div v-if="loaded" class="m-5">
    
    <div class="bg-base-300 rounded-box p-5">
        <div class="grid lg:grid-cols-6 md:grid-cols-3 sm:grid-cols-1 gap-0 md:flex-wrap sm:flex-wrap">
            
            <div class="col-span-6">
                <div class = "col-span-6 h">Akkumulátor-cella azonosítója: {{k}}</div>
                <div class = "col-span-6"><br></div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="feszultseg != undefined">{{ feszultseg }} V</div>
                <div class = "t" v-else="feszultseg == undefined">Folyamatban</div>
                <div class = "d">Mért feszültség</div>
            </div>
            
            <div class="col-span-1">
                <div class = "t" v-if="m_kezdes != undefined">{{ datum(m_kezdes) }}</div>
                <div class = "t" v-else="m_kezdes == undefined">Folyamatban</div>
                <div class = "d">Merítési idejének kezdete</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="m_vege != undefined">{{ datum(m_vege) }}</div>
                <div class = "t" v-else="m_kezdes == undefined">Folyamatban</div>
                <div class = "d">Merítés idejének vége</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="t_kezdes != undefined">{{ datum(t_kezdes) }}</div>
                <div class = "t" v-else="t_kezdes == undefined"> Folyamatban</div>
                <div class = "d">Töltés idejének kezdete</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="t_vege != undefined">{{ datum(t_vege) }}</div>
                <div class = "t" v-else="t_vege == undefined">Folyamatban</div>
                <div class = "d">Töltés idejének vége</div>
            </div>

            <div class="col-span-1">
                <div class = "t" v-if="jr == true">Jó</div>
                <div class = "t" v-else-if="jr == false">Rossz</div>
                <div class = "t" v-else="jr == undefined">Folyamatban</div>
                <div class = "d">Cella állapota</div>
            </div>
        </div>
    </div>
    
    <div class="flex flex-wrap">
        <div v-if="loaded" class="bg-base-300 rounded-box min-w-96 max-w-md  p-5  mt-5 mr-5"><merites class="h-auto" /></div>
        <div v-if="loaded" class="bg-base-300 rounded-box min-w-96 max-w-md  p-5 mt-5 mr-5" ><toltes class="h-auto"/></div>
        <div v-if="loaded" class="bg-base-300 rounded-box min-w-96  max-w-md  p-5 mt-5 mr-5" ><szazalekkor class="h-auto"/></div>
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
            setInterval(() => {this.lekeres()}, 5*60000);
        },

        data () {
            return {
                feszultseg: null,
                m_kezdes: null,
                m_vege: null,
                t_kezdes: null,
                t_vege: null,
                jr: null,
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
                this.m_kezdes = a.merites_kezdes
                this.m_vege = a.merites_vege
                this.t_kezdes = a.toltes_kezdes
                this.t_vege = a.toltes_vege
                this.jr = a.jo_rossz
                
                this.k = k
                this.loaded=true;
            },

            datum(a) {
                moment.locale('hu');
                return moment(a).format('hh:mm');
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
</style>