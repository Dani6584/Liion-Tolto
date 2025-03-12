<template>
    <div class="grid grid-cols-3 p-3 gap-4">
        <div  class="bg-base-300 rounded-box h-20 col-span-3"></div>
        
        <div  v-if="loaded" class="grid bg-base-300 rounded-box place-items-center h-auto"><merites/></div>
        <div  v-if="loaded" class="bg-base-300 rounded-box place-items-center h-auto"><toltes/></div>
        <div  v-if="loaded" class="bg-base-300 rounded-box place-items-center h-auto"></div>
    </div>
    
</template>

<script>
    import merites from '@/charts/merites.vue';
    import toltes from '@/charts/toltes.vue';

    import {useFetchDataStore} from "@/stores/FetchDataStore.js";
    import {lekeres} from "@/appwrite/lekeres.js"

    export default {
        components: {
            merites,
            toltes
        },
        mounted() {
            this.leker();
        },

        data () {
            return {
                kezd: '',
                vege: '',
                loaded:false
            }
        },
        methods:{
            async leker()
            {   
                await lekeres("67abb6110001665eb916",true);
                //this.mkezd=a.merites_kezdes;
                //this.mvege=a.merites_vege;
                //this.fesz=a.feszultseg;
                this.loaded=true;
            }
        }
    }
</script>