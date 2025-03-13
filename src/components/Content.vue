<template>
    <div class="grid grid-cols-3 p-5 gap-10">

        <div  class="bg-base-300 rounded-box h-30 col-span-3 p-5">
            <div class = "grid grid-cols-6 gap-0">
                <div class = "col-span-6">Akkumulátor-cella azonosítója: </div>
                <div class = "col-span-6"><br></div>

                <div class = "t">{{ feszultseg }} V</div>
                <div class = "t">{{ datum(m_kezdes) }}</div>
                <div class = "t">{{ datum(m_vege) }}</div>
                <div class = "t">{{ datum(t_kezdes) }}</div>
                <div class = "t">{{ datum(t_vege) }}</div>
                <div class = "t">{{ jr }}</div>

                <div class = "d">Mért feszültség</div>
                <div class = "d">Merítési idejének kezdete</div>
                <div class = "d">Merítés idejének vége</div>
                <div class = "d">Töltés idejének kezdete</div>
                <div class = "d">Töltés idejének vége</div>
                <div class = "d">Cella állapota</div>
            </div>
        </div>
        
        
        <div  v-if="loaded" class="grid bg-base-300 rounded-box place-items-center h-auto p-5"><merites/></div>
        <div  v-if="loaded" class="bg-base-300 rounded-box place-items-center h-auto p-5"><toltes/></div>
        <div  v-if="loaded" class="bg-base-300 rounded-box place-items-center h-auto p-5"></div>
    </div>
    
</template>

<script>
    import merites from '@/charts/merites.vue';
    import toltes from '@/charts/toltes.vue';
    import moment from 'moment/min/moment-with-locales';
    import {useFetchDataStore} from "@/stores/FetchDataStore.js";
    import {lekeres} from "@/appwrite/lekeres.js"

    export default {
        components: {
            merites,
            toltes
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
                loaded:false
            }
        },
        methods:{
            async leker()
            {   
                await lekeres("67abb6110001665eb916",true)
                const a = useFetchDataStore()
                this.feszultseg = a.feszultseg
                this.m_kezdes = a.merites_kezdes
                this.m_vege = a.merites_vege
                this.t_kezdes = a.toltes_kezdes
                this.t_vege = a.toltes_vege
                this.jr = a.jo_rossz
                
                this.loaded=true;
            },

            datum(a) {
                if (a == '') {
                    return '';
                }
                else {
                    moment.locale('hu');
                    return moment(a).format('hh:mm');
                }
            }
        },


        
    }
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
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