import { database } from '@/appwrite';
import { Query } from "appwrite";
import ids from '@/appwrite/ids.json';
import moment from 'moment/min/moment-with-locales';
import {useFetchDataStore} from  "../stores/FetchDataStore";

async function lekeres(docID, pinia = false) {
    let _fesz, _idok;
    let _fesz2, _idok2;
    let data;
    let _docID;
    try {
      
      const response = await database.getDocument(ids.database_id, ids.akkumulator_id, docID);
      data = response;
      
      console.log(data.toltes_kezdete);
      const fetchData= new useFetchDataStore();
      const MeritesResponse = await database.listDocuments(ids.database_id,ids.merites_id, [Query.equal("battery", docID), Query.orderAsc("$createdAt")]);
      _fesz = MeritesResponse.documents.map(doc => doc.voltage);
      _idok = MeritesResponse.documents.map(doc => datum(doc.$createdAt));

      const ToltesResponse = await database.listDocuments(ids.database_id,ids.toltes_id, [Query.equal("battery", docID), Query.orderAsc("$createdAt")]);
      _fesz2 = ToltesResponse.documents.map(doc => doc.voltage);
      _idok2 = ToltesResponse.documents.map(doc => datum(doc.$createdAt));
      
      if(pinia) {
        // Meritesi adatok
        fetchData.setFesz(_fesz)
        fetchData.setIdok(_idok)
        
        // Toltesi adatok
        fetchData.setFesz2(_fesz2)
        fetchData.setIdok2(_idok2)

        // Altalanos adatok
        fetchData.setData(data)
        return {}
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    return {
        _fesz,_idok,_fesz2,_idok2,data
    }
  }
  async function legujabblekeres()
  {
    const responseID = await database.listDocuments(ids.database_id, ids.akkumulator_id, [Query.orderDesc("$createdAt"), Query.limit(1)]);
    let _docID;
    _docID=responseID.documents[0].$id;

    const fetchData= new useFetchDataStore();
    fetchData.setLegujabb(_docID);
    return _docID;
    
  }

  function datum(a) {
    moment.locale('hu');
    return moment(a).format('MMM Do hh:mm');
  }

  export {lekeres,datum,legujabblekeres}