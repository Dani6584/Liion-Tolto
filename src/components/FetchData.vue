<template>
  <div>
      <h1 v-if = "loading">Dokumentum</h1>
      <h1 v-else-if = "data">Dokumentum ID  - {{ docID }}</h1>

      <div v-if="loading">Betöltés...</div>

      <div v-else-if = "data">
        <!--altalanos adatok, a nem rendelkezesre allo adatoknal valami jelzes lesz hogy jelenleg nem elerheto, majd intervallal frissitem-->
        <p> Feszültség: {{ ki(data.feszultseg) }} </p>
        <p>Százalék: {{ ki(data.szazalek) }}</p>
        <p>Merítés Kezdes: {{ ki(datum(data.merites_kezdes)) }}</p>
        <p>Merítés Vége: {{ ki(datum(data.merites_vege)) }}</p>
        <p>Töltés Kezdes: {{ ki(datum(data.toltes_kezdes)) }}</p>
        <p>Töltés Vége: {{ ki(datum(data.toltes_vege)) }}</p>
          <p>Jó Rossz: {{ ki(data.jo_rossz) }}</p>
      </div>
      
      <div v-else>
        <p>Nem található ilyen ID-vel rendelkező dokumentum.</p>
      </div>

    <graph v-if="loaded" :feszultsegek="_fesz" :idok="_idok" :loaded="loaded" />
  </div>
</template>

<script>
import { database } from '@/appwrite';
import ids from '@/appwrite/ids.json';
import moment from 'moment/min/moment-with-locales';

import { Query } from "appwrite";
import graph from '@/charts/graph.vue';

// Override invalid return
const originalFormat = moment.fn.format;
moment.fn.format = function (formatStr) {
  if (!this.isValid()) {
    return ''; // Fallback for invalid dates
  }
  return originalFormat.call(this, formatStr);
};

export default {
  data() {
    return {
      data: null,
      loading: true,
      docID: '67abb6110001665eb916',

      loaded: false,
      _fesz: [],
      _idok: []
    };
  },

  components: {
    graph
  },

  mounted() {
    this.lekeres();
    setInterval(() => {this.lekeres()}, 600000);
  },

  methods: {
    async lekeres() {
      try {
        const response = await database.getDocument(ids.database_id, ids.akkumulator_id, this.docID);
        this.data = response;

        const graphResponse = await database.listDocuments(ids.database_id,ids.data_id, [Query.equal("battery", this.docID), Query.orderAsc("$createdAt")]);
        this._fesz = graphResponse.documents.map(doc => doc.voltage);
        this._idok = graphResponse.documents.map(doc => this.datum(doc.$createdAt));
        
        this.loaded = true;
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        this.loading = false;
      }
    },

    // Athelyezni
    datum(a) {
      moment.locale('hu');
      return moment(a).format('MMMM Do hh:mm:ss');
    },

    // Athelyezni
    ki(value, fallback = 'Folyamatban...') {
      return value || fallback;
    }

  }
};
</script>
