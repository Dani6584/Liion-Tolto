<template>
<div class="flex">
  <table class="w-3/4 table">
    <thead>
      <tr>
        <th></th>
        <th>Akkumulátor-cella kódja</th>
        <th>Kezdési idő</th>
        <th>Befejezési idő</th>
      </tr>
    </thead>

    <tbody>
        <tr @click="ugrik(docID.id)" class="hover:bg-base-300" v-for="(docID, index) in _docIDs" :key="docID.id">
        <td>{{ index+1 }}</td>
        <td>
            <span v-if="docID.kod == '---'">Ismeretlen cella</span>
            <span v-else>{{ docID.kod }}</span>
        </td>
        
        <td><span>{{ datum(docID.kdatum) }}</span></td>
        <td><span>{{ datum(docID.vdatum) }}</span></td>
      </tr>
    </tbody>
  </table>

</div>
</template>

<script>
import { database } from '@/appwrite'
import { Query } from "appwrite"
import ids from '@/appwrite/ids.json'
import moment from 'moment/min/moment-with-locales';

export default {
    mounted() {
        this.korabbilekeres();
        setInterval(() => {this.korabbilekeres()}, 5*60000);
    },
    data () {
        return { loaded:false,_docIDs:[] }
    },
    methods:{
        async korabbilekeres() {  
            this._docIDs=[];
            try {
                const responseIDs = await database.listDocuments(ids.database_id, ids.akkumulator_id, [Query.orderDesc("$createdAt")])
                //console.log(responseIDs);
                //this._docIDs=responseIDs.documents.map(doc => doc.$id)
                responseIDs.documents.forEach(element => {
                    console.log(element)
                    this._docIDs.push({id:element.$id,kod:element.leolvasottkod, kdatum:element.$createdAt, vdatum:element.toltes_vege});
                });
                console.log(this._docIDs)
                this.loaded=true
            }
            catch (error) {
                console.error("Error fetching data: ", error)
            }
            finally {
               // this.loaded=true
            }
        },
        datum(a) {
            moment.locale('hu');
            return moment(a).format('MMMM DD hh:mm');
        },
        ugrik(a) {
            this.$router.push(`/data/${a}`);
        }
    },
}
</script>