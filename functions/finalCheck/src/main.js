import { Client, Databases, Query } from "node-appwrite";

export default async ({ req, res, log, error }) => {
    const client = new Client()
        .setEndpoint("https://appwrite.tsada.edu.rs/v1")
        .setProject("67a5b2fd0036cbf53dbf")
        .setKey("standard_cd198d0d53bf431d78706ab420ce6841ae4d7bf7354d22ff6b40c88a7b8403c826c6eccf1aabbe5b3e720fae15b720bc870edb2b562557a5084e7fcba1b83788e56f864aed5ae9d647672fb19872b21408900f1e75c97958175ec728d225e0d7b59dd1ce702e1aef869d2a5285774a6a553789c091d62c47f0e02051fc244ac0");

    const databases = new Databases(client);
    const DB_ID = "67a5b54c00004b1a93d7";
    const BATTERY_COLLECTION = "67f279860016263782ae";
    const CHARGE_COLLECTION = "67d18e17000dc1b54f39";
    const DISCHARGE_COLLECTION = "67ac8901003b19f4ca35";
    const SETTINGS_COLLECTION = "67de7e600036fcfc5959";

    try {
        // 🔍 Visszatöltött, kiértékelésre váró cella
        const cellRes = await databases.listDocuments(DB_ID, BATTERY_COLLECTION, [
          Query.equal("status", 5),
          Query.equal("operation", 1),
          Query.limit(1)
        ]);
    
        if (cellRes.total === 0) {
          log("ℹ️ Nincs visszatöltött cella.");
          return res.json({ message: "Nincs feldolgozandó cella." });
        }
    
        const battery = cellRes.documents[0];
        const measured =
          battery.kapacitas_mAh ??
          battery.recharge_measured_capacity ??
          battery.discharge_measured_capacity ??
          null;
        const ideal = battery.ideal_capacity ?? 0;
    
        // 🔧 Küszöb lekérése
        let threshold = 60;
        const thresholdRes = await databases.listDocuments(DB_ID, SETTINGS_COLLECTION, [
          Query.equal("setting_name", "REFERENCE_THRESHOLD"),
          Query.limit(1)
        ]);
        if (thresholdRes.total > 0) {
          const parsed = parseInt(thresholdRes.documents[0].setting_data);
          if (!isNaN(parsed)) threshold = parsed;
        }
    
        let statusToSet = 7;
        let msg = "";
    
        if (ideal > 0 && measured !== null) {
          const percent = Math.round((measured / ideal) * 100);
          if (percent < threshold) {
            statusToSet = 9;
            msg = `❌ ${percent}% kapacitás – rossz cella`;
          } else {
            msg = `✔️ ${percent}% kapacitás – jó cella`;
          }
        } else {
          msg = "⚠️ Ismeretlen referencia – jóként kezelve.";
        }
    
        await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
          status: statusToSet,
          operation: 0,
          kapacitas_szazalek:
            ideal > 0 && measured ? Math.round((measured / ideal) * 100) : null,
          allapot: statusToSet === 7 ? "jó" : "rossz",
          allapot_uzenet: msg
        });
    
        // 🔄 Csak akkor töröljük az ACTIVE_CELL_ID-t, ha van új cella
        const nextCell = await databases.listDocuments(DB_ID, BATTERY_COLLECTION, [
          Query.or([Query.equal("status", 1), Query.equal("status", 0)]),
          Query.limit(1)
        ]);
    
        const activeFlag = await databases.listDocuments(DB_ID, SETTINGS_COLLECTION, [
          Query.equal("setting_name", "ACTIVE_CELL_ID"),
          Query.limit(1)
        ]);
    
        if (nextCell.total > 0 && activeFlag.total > 0) {
          await databases.updateDocument(DB_ID, SETTINGS_COLLECTION, activeFlag.documents[0].$id, {
            setting_data: ""
          });
          log("🧹 ACTIVE_CELL_ID törölve – új cella készen áll.");
        } else {
          log("⚠️ ACTIVE_CELL_ID megtartva – nincs új cella.");
        }
    
        return res.json({ message: "FinalCheck sikeres", status: statusToSet, comment: msg });
      } catch (err) {
        error("❌ FinalCheck hiba:", err.message);
        return res.json({ error: err.message });
      }
    };