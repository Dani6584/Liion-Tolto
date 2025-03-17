import { database } from '@/appwrite'
import { Query } from "appwrite"
import ids from '@/appwrite/ids.json'
import moment from 'moment/min/moment-with-locales'
import {useFetchDataStore} from  "../stores/FetchDataStore"

let _fesz, _idok, _fesz2, _idok2, _data, _docID, _mcurrent, _tcurrent

async function lekeres(docID, pinia = false) {
  try {
    const response = await database.getDocument(ids.database_id, ids.akkumulator_id, docID);
    _data = response;
    
    const fetchData = new useFetchDataStore();
    const MeritesResponse = await database.listDocuments(ids.database_id,ids.merites_id, [Query.equal("battery", docID), Query.orderAsc("$createdAt")]);
    _fesz = MeritesResponse.documents.map(doc => doc.voltage);
    _idok = MeritesResponse.documents.map(doc => datum(doc.$createdAt));
    _mcurrent = MeritesResponse.documents.map(doc => doc.dischargecurrent);
    
    const ToltesResponse = await database.listDocuments(ids.database_id,ids.toltes_id, [Query.equal("battery", docID), Query.orderAsc("$createdAt")]);
    _fesz2 = ToltesResponse.documents.map(doc => doc.voltage);
    _idok2 = ToltesResponse.documents.map(doc => datum(doc.$createdAt));
    _tcurrent = ToltesResponse.documents.map(doc => doc.chargecurrent);

    if(pinia) {
      fetchData.setFesz(_fesz)
      fetchData.setIdok(_idok)
      fetchData.setMCurrent(_mcurrent)

      fetchData.setFesz2(_fesz2)
      fetchData.setIdok2(_idok2)
      fetchData.setTCurrent(_tcurrent)

      fetchData.setData(_data)
    }
  } catch (error) {
    console.error("Error fetching data:", error);
  }
  return {
      _fesz,_idok,_mcurrent,_fesz2,_idok2,_tcurrent,_data
  }
}

async function legujabblekeres() {
  const responseID = await database.listDocuments(ids.database_id, ids.akkumulator_id, [Query.orderDesc("$createdAt"), Query.limit(1)]);
  _docID=responseID.documents[0].$id;
  const fetchData = new useFetchDataStore();
  fetchData.setLegujabb(_docID);
  return _docID;
}

function datum(a) {
  moment.locale('hu');
  return moment(a).format('MMM Do hh:mm');
}

export {lekeres, legujabblekeres, datum}