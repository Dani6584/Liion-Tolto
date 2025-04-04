import { Client, Databases, Query } from "node-appwrite";
import * as fuzz from 'fuzzball';

export default async ({ req, res, log, error }) => {
  const client = new Client()
    .setEndpoint("https://appwrite.tsada.edu.rs/v1")
    .setProject("67a5b2fd0036cbf53dbf")
    .setKey("standard_cd198d0d53bf431d78706ab420ce6841ae4d7bf7354d22ff6b40c88a7b8403c826c6eccf1aabbe5b3e720fae15b720bc870edb2b562557a5084e7fcba1b83788e56f864aed5ae9d647672fb19872b21408900f1e75c97958175ec728d225e0d7b59dd1ce702e1aef869d2a5285774a6a553789c091d62c47f0e02051fc244ac0");

  const databases = new Databases(client);
  const DB_ID = "67a5b54c00004b1a93d7";
  const BATTERY_COLLECTION = "67a5b55b002eceac9c33";
  const CHARGE_COLLECTION = "67d18e17000dc1b54f39";
  const DISCHARGE_COLLECTION = "67ac8901003b19f4ca35";
  const SETTINGS_COLLECTION = "67de7e600036fcfc5959";
  const REF_COLLECTION = "67d9b54d0005a8009bc2";

  try {
    // 1️⃣ OCR_LAST lekérése
    const ocrLast = await databases.listDocuments(DB_ID, SETTINGS_COLLECTION, [
      Query.equal("setting_name", "OCR_LAST"),
      Query.limit(1)
    ]);

    if (ocrLast.total === 0) {
      return res.json({ message: "Nincs OCR_LAST bejegyzés." });
    }

    const ocrValue = ocrLast.documents[0].setting_data?.trim() || "";
    if (!ocrValue) {
      return res.json({ message: "Üres OCR érték." });
    }

    // 2️⃣ Duplikáció ellenőrzése — van-e már feldolgozatlan cella ezzel a kóddal?
    const existing = await databases.listDocuments(DB_ID, BATTERY_COLLECTION, [
      Query.equal("leolvasottkod", ocrValue),
      Query.lessThan("status", 2), // csak ha még nincs betöltve/mérve
      Query.limit(1)
    ]);

    if (existing.total > 0) {
      return res.json({ message: "Ez a cella már feldolgozás alatt van." });
    }

    // 3️⃣ Referencia cellák fuzzy összehasonlítása
    const references = await databases.listDocuments(DB_ID, REF_COLLECTION, [Query.limit(100)]);
    let bestMatch = null;
    let bestScore = 0;

    for (const ref of references.documents) {
      const refString = `${ref.Manufacturer} ${ref.Type}`;
      const score = fuzz.token_set_ratio(ocrValue, refString);
      if (score > bestScore && score >= 60) {
        bestScore = score;
        bestMatch = ref;
      }
    }

    // 4️⃣ Új akkumulátor dokumentum létrehozása
    const docData = {
      leolvasottkod: ocrValue,
      nyerskod: bestMatch ? `${bestMatch.Manufacturer} ${bestMatch.Type}` : "---",
      ideal_capacity: String(bestMatch?.IdealCapacity ?? 0).slice(0, 50),
      ideal_voltage: String(bestMatch?.IdealVoltage ?? "").slice(0, 50),
      status: 1,
      operation: 0
    };

    const newBattery = await databases.createDocument(DB_ID, BATTERY_COLLECTION, "unique()", docData);

    // 5️⃣ ACTIVE_CELL_ID frissítése
    const activeCell = await databases.listDocuments(DB_ID, SETTINGS_COLLECTION, [
      Query.equal("setting_name", "ACTIVE_CELL_ID"),
      Query.limit(1)
    ]);

    if (activeCell.total > 0) {
      await databases.updateDocument(DB_ID, SETTINGS_COLLECTION, activeCell.documents[0].$id, {
        setting_data: newBattery.$id
      });
    }

    // 6️⃣ OCR_LAST törlése vagy frissítése
    await databases.updateDocument(DB_ID, SETTINGS_COLLECTION, ocrLast.documents[0].$id, {
      setting_data: "" // vagy valami token, hogy ne fusson újra ugyanazzal
    });

    // 7️⃣ OCR_ACTIVE és ROTATE_CELL resetelése
    const flagsToReset = ["OCR_ACTIVE", "ROTATE_CELL"];
    for (const flag of flagsToReset) {
      const found = await databases.listDocuments(DB_ID, SETTINGS_COLLECTION, [
        Query.equal("setting_name", flag),
        Query.limit(1)
      ]);
      if (found.total > 0) {
        await databases.updateDocument(DB_ID, SETTINGS_COLLECTION, found.documents[0].$id, {
          setting_boolean: false
        });
      }
    }

    return res.json({
      message: bestMatch ? "Ismert cella létrehozva." : "Ismeretlen cella létrehozva.",
      matched: docData.nyerskod,
      id: newBattery.$id
    });

  } catch (err) {
    error("❌ Hiba a createCell-ben:", err.message);
    return res.json({ error: err.message });
  }
};
