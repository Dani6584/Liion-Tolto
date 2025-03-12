import { database } from '@/appwrite';
import { Query } from "appwrite";
import ids from '@/appwrite/ids.json';
import moment from 'moment/min/moment-with-locales';
import {useFetchDataStore} from  "../stores/FetchDataStore";
//import FetchData from '@/components/FetchData.vue';

async function lekeres(docID,pinia=false) {
    let _fesz,_idok;
    let _fesz2,_idok2;
    
    try {
      const response = await database.getDocument(ids.database_id, ids.akkumulator_id, docID);
      let data = response;
      const fetchData= new useFetchDataStore();
      
      const MeritesResponse = await database.listDocuments(ids.database_id,ids.merites_id, [Query.equal("battery", docID), Query.orderAsc("$createdAt")]);
      _fesz = MeritesResponse.documents.map(doc => doc.voltage);
      _idok = MeritesResponse.documents.map(doc => datum(doc.$createdAt));

      const ToltesResponse = await database.listDocuments(ids.database_id,ids.toltes_id, [Query.equal("battery", docID), Query.orderAsc("$createdAt")]);
      _fesz2 = ToltesResponse.documents.map(doc => doc.voltage);
      _idok2 = ToltesResponse.documents.map(doc => datum(doc.$createdAt));
      console.log("HALO");
      
      if(pinia==true)
      {
        fetchData.setFesz(_fesz);
        fetchData.setIdok(_idok);

        fetchData.setFesz(_fesz2);
        fetchData.setIdok(_idok2);
        return {}
        }

      //this.loaded = true;
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      //this.loading = false;
    }
    return {
        _fesz,_idok,
        _fesz2,_idok2
    }
  }


  function datum(a) {
    if (a == '') {
      return '';
    }
    else {
      moment.locale('hu');
      return moment(a).format('MMMM Do hh:mm:ss');
    }
  }

  export {lekeres,datum}