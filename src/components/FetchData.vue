<template>
</template>

<script>
import { database } from '@/appwrite';
import { Query } from "appwrite";
import ids from '@/appwrite/ids.json';
import moment from 'moment/min/moment-with-locales';

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
  mounted() {
    this.lekeres();
    //setInterval(() => {this.lekeres()}, 600000);
  },

  methods: {
    async lekeres() {
      try {
        const response = await database.getDocument(ids.database_id, ids.akkumulator_id, this.docID);
        this.data = response;

        const MeritesResponse = await database.listDocuments(ids.database_id,ids.merites_id, [Query.equal("battery", this.docID), Query.orderAsc("$createdAt")]);
        this._fesz = MeritesResponse.documents.map(doc => doc.voltage);
        this._idok = MeritesResponse.documents.map(doc => this.datum(doc.$createdAt));
        
        const ToltesResponse = await database.listDocuments(ids.database_id,ids.toltes_id, [Query.equal("battery", docID), Query.orderAsc("$createdAt")]);
        fesz2 = ToltesResponse.documents.map(doc => doc.voltage);
        _idok2 = ToltesResponse.documents.map(doc => datum(doc.$createdAt));
        
        this.loaded = true;
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        this.loading = false;
      }
    },

    datum(a) {
      if (a == '') {
        return '';
      }
      else {
        moment.locale('hu');
        return moment(a).format('MMMM Do hh:mm:ss');
      }
    }
  }
};
</script>
