import { defineStore } from 'pinia';

export const useFetchDataStore = defineStore('FetchData', {
  state: () => ({
    feszultseg: null,
    szazalek: null,
    merites_kezdes: null,
    merites_vege: null,
    toltes_kezdes: null,
    toltes_vege: null,
    jo_rossz: null,
    belso_ellenallas: null
  }),
  actions: {
    setData(data) {
        this.feszultseg = data.feszultseg;
        this.szazalek = data.szazalek;
        this.merites_kezdes = data.merites_kezdes;
        this.merites_vege = data.merites_vege;
        this.toltes_kezdes = data.toltes_kezdes;
        this.toltes_vege = data.toltes_vege;
        this.jo_rossz = data.jo_rossz;
        this.belso_ellenallas = data.belso_ellenallas;
      },
  },
});