<template>
    <div v-if="loaded" class="flex flex-wrap bg-base-300 rounded-box min-w-96 p-5 mt-5 overflow-auto">
      <h2 class="text-lg font-bold mb-4 w-full">🔍 OCR – Akkumulátor beolvasás</h2>
  
      <video ref="video" autoplay class="rounded-box w-full border border-base-content mb-4"></video>
      <canvas ref="canvas" class="hidden"></canvas>
  
      <div class="w-full mb-2">
        <p class="font-mono text-lg">{{ message }}</p>
        <p v-if="lastOCR" class="text-sm text-info mt-2">🔠 Utolsó OCR kód: <b>{{ lastOCR }}</b></p>
        <p v-if="ocrActive" class="text-warning mt-1">⏳ Feldolgozás folyamatban...</p>
        <p v-if="!ocrActive && lastOCR" class="text-success mt-1">✔️ OCR kód feldolgozva!</p>
        <p v-if="errorMessage" class="text-error font-mono mt-2">{{ errorMessage }}</p>
      </div>
    </div>
  </template>
  
  <script>
  import { database } from '@/appwrite'
  import { Query } from 'appwrite'
  import ids from '@/appwrite/ids.json'
  import Tesseract from 'tesseract.js'
  
  export default {
    data() {
      return {
        loaded: false,
        message: '🔄 OCR indul...',
        errorMessage: '',
        isProcessing: false,
        lastTextSent: '',
        lastSentAt: 0,
        rotateID: '',
        ocrLastID: '',
        ocrActiveID: '',
        lastOCR: '',
        ocrActive: false
      }
    },
    methods: {
      async checkFlags() {
        try {
          const response = await database.listDocuments(ids.database_id, ids.settings_collection, [
            Query.equal("setting_name", ["ROTATE_CELL", "OCR_LAST", "OCR_ACTIVE"]),
            Query.limit(10)
          ]);
          for (const doc of response.documents) {
            if (doc.setting_name === "ROTATE_CELL") this.rotateID = doc.$id;
            if (doc.setting_name === "OCR_LAST") {
              this.ocrLastID = doc.$id;
              this.lastOCR = doc.setting_data;
            }
            if (doc.setting_name === "OCR_ACTIVE") {
              this.ocrActiveID = doc.$id;
              this.ocrActive = doc.setting_boolean === true;
            }
          }
        } catch (err) {
          this.errorMessage = "Nem sikerült lekérni a flag értékeket.";
          console.error("⚠️ Flag lekérés hiba:", err);
        }
      },
  
      async updateOCRLast(value) {
        try {
          await database.updateDocument(ids.database_id, ids.settings_collection, this.ocrLastID, {
            setting_data: value
          });
        } catch (err) {
          console.error("⚠️ OCR_LAST frissítése sikertelen:", err);
        }
      },
  
      async updateOCRActive(value) {
        try {
          await database.updateDocument(ids.database_id, ids.settings_collection, this.ocrActiveID, {
            setting_boolean: value
          });
        } catch (err) {
          console.error("⚠️ OCR_ACTIVE frissítése sikertelen:", err);
        }
      },
  
      async updateRotateCell(value) {
        try {
          await database.updateDocument(ids.database_id, ids.settings_collection, this.rotateID, {
            setting_boolean: value
          });
        } catch (err) {
          console.error("⚠️ ROTATE_CELL frissítése sikertelen:", err);
        }
      },
  
      async runOCR() {
        if (!this.$refs.video || this.isProcessing) return;
  
        this.isProcessing = true;
        const canvas = this.$refs.canvas;
        const context = canvas.getContext('2d');
        canvas.width = this.$refs.video.videoWidth;
        canvas.height = this.$refs.video.videoHeight;
        context.drawImage(this.$refs.video, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL();
  
        try {
          const { data: { text } } = await Tesseract.recognize(imageData, 'eng');
          const cleanedText = text.trim().replace(/\s+/g, ' ');
          const now = Date.now();
  
          if (cleanedText.length >= 4) {
            if (cleanedText === this.lastTextSent && now - this.lastSentAt < 15000) {
              this.message = "🔁 Ugyanaz a cella, várok…";
            } else {
              this.lastTextSent = cleanedText;
              this.lastSentAt = now;
  
              await this.updateOCRLast(cleanedText);
              await this.updateOCRActive(true);
              await this.updateRotateCell(false);
  
              this.message = `✅ OCR kód elküldve: ${cleanedText}`;
              this.errorMessage = '';
            }
          } else {
            this.message = "⏳ Nem értelmezhető szöveg – forgatás szükséges!";
            await this.updateRotateCell(true);
          }
        } catch (err) {
          this.errorMessage = "OCR hiba: " + err.message;
        }
  
        this.isProcessing = false;
      },
  
      async startCamera() {
        try {
          const constraints = {
            video: {
              facingMode: "environment",
              width: { ideal: 1280 },
              height: { ideal: 720 }
            }
          };
  
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          this.$refs.video.srcObject = stream;
  
          try {
            const videoTrack = stream.getVideoTracks()[0];
            const capabilities = videoTrack.getCapabilities();
  
            if (capabilities.torch) {
              await videoTrack.applyConstraints({
                advanced: [{ torch: true }]
              });
              console.log("🔦 Flashlight bekapcsolva");
            } else {
              console.warn("⚠️ Ez az eszköz nem támogatja a flashlight módot");
            }
          } catch (flashErr) {
            console.warn("⚠️ Flashlight nem elérhető:", flashErr.message);
          }
  
        } catch (err) {
          this.errorMessage = "🚫 Nem sikerült elindítani a kamerát.";
          console.error("🎥 Kameraindítás hiba:", err);
        }
      }
    },
    mounted() {
      this.startCamera();
      this.loaded = true;
      setInterval(async () => {
        await this.checkFlags();
        await this.runOCR();
      }, 3000);
    }
  }
  </script>
  
  <style scoped>
  video {
    max-height: 250px;
    object-fit: contain;
  }
  </style>
  