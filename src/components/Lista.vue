<template>
<div v-if="loaded" class="flex flex-wrap bg-base-300 rounded-box min-w-96 p-5 mt-5 overflow-auto">
  <table class="table">
    <thead>
      <tr class="cim">
        <th></th>
        <th>Akkumulátor-cella kódja</th>
        <th>Kezdés időpontja</th>
        <th>Befejezés időpontja</th>
      </tr>
    </thead>

    <tbody class="tartalom">
        <tr @click="ugrik(docID.id)" class="hover:bg-base-100" v-for="(docID, index) in _docIDs" :key="docID.id">
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
                responseIDs.documents.forEach(element => {
                    console.log(element)
                    this._docIDs.push({id:element.$id,kod:element.leolvasottkod, kdatum:element.$createdAt, vdatum:element.merites_vege});
                });
            }
            catch (error) {
                console.error("Error fetching data: ", error)
            }
            finally {
               this.loaded=true
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

<style>
.cim {
    color: #eeeef1;
    font-size: 1.5rem;
    font-weight: 600;
    font-family: "Poppins", sans-serif;
}
.tartalom {
    color: #c3c3c6;
    font-size: 0.875rem;
    font-family: "Inter", sans-serif;
}
</style>