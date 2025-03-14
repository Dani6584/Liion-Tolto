<template>
<div v-if="loaded">
    <ul class= "list-disc m-10">
        <li v-for="id in _docIDs" :key="id">{{ id }}</li>
    </ul>
</div>
</template>

<script>
import { database } from '@/appwrite'
import { Query } from "appwrite"
import ids from '@/appwrite/ids.json'
let _docIDs

export default {
    mounted() {
        this.korabbilekeres();
        setInterval(() => {this.korabbilekeres()}, 5*60000);
    },

    data () {
        return { loaded:false }
    },

    methods:{
        async korabbilekeres() {  
            try {
                const responseIDs = await database.listDocuments(ids.database_id, ids.akkumulator_id, [Query.orderDesc("$createdAt")])
                _docIDs=responseIDs.documents.map(doc => doc.$id)
                console.log(_docIDs)
                this.loaded=true
            }
            catch (error) {
                console.error("Error fetching data: ", error)
            }
            finally {
                this.loaded=false
            }
        }
    }
}
</script>

<style>
</style>