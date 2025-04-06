import { defineStore } from 'pinia';

export const useFetchDataStore = defineStore('FetchData', {
  state: () => ({
    // Akkumulátor collection
    feszultseg: null,
    belso_ellenallas: null,
    discharge_capacity: null,
    discharge_capacity_percentage: null,
    allapot: null,

    toltes_kezdes: null,
    toltes_vege: null,
    merites_kezdes: null,
    merites_vege: null,
    ujratoltes_kezdes: null,
    ujratoltes_vege: null,

    // Merítés collection
    fesz:[],
    idok:[],
    mcurrent:[],

    // Töltés collection
    fesz2:[],
    idok2:[],
    tcurrent:[],

    // Legújabb cella
    legujabb_cella: null,
  }),

  actions: {
    setData(data) {
        this.feszultseg = data.feszultseg
        this.belso_ellenallas = data.belso_ellenallas
        this.discharge_capacity_percentage = data.discharge_capacity
        this.allapot = data.allapot
        this.kapacitas_szazalek = data.kapacitas_szazalek
        console.log(this.belso_ellenallas)
        this.toltes_kezdes = data.toltes_kezdes
        this.toltes_vege = data.toltes_vege
        this.merites_kezdes = data.merites_kezdes
        this.merites_vege = data.merites_vege
        this.ujratoltes_kezdes = data.ujratoltes_kezdes
        this.ujratoltes_vege = data.ujratoltes_vege        
    },

    setFesz(_fesz) {
      this.fesz=_fesz
    },
    setIdok(_idok) {
      this.idok=_idok
    },
    setMCurrent(_mcurrent) {
      this.mcurrent = _mcurrent
    },

    setFesz2(_fesz2) {
      this.fesz2=_fesz2
    },
    setIdok2(_idok2) {
      this.idok2=_idok2
    },
    setTCurrent(_tcurrent) {
      this.tcurrent = _tcurrent
    },

    setLegujabb(_id) {
      this.legujabb_cella=_id
    }
  },
});