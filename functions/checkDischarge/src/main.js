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
        const dischargeSettingResult = await databases.listDocuments(DB_ID, SETTINGS_COLLECTION, [
            Query.equal("setting_name", "DISCHARGE_SWITCH"),
            Query.limit(1)
        ]);

        if (dischargeSettingResult.total === 0) {
            throw new Error("DISCHARGE_SWITCH setting not found.");
        }

        const dischargeSetting = dischargeSettingResult.documents[0];
        const activeDischargeMode = dischargeSetting.setting_boolean ? 1 : 2;
        const lastSwitch = dischargeSetting.last_switched_at ? new Date(dischargeSetting.last_switched_at) : null;
        const now = new Date();
        const minutesSinceLastSwitch = lastSwitch ? (now - lastSwitch) / 60000 : Infinity;

        const batteries = await databases.listDocuments(DB_ID, BATTERY_COLLECTION, [
            Query.equal("status", 4),
            Query.equal("operation", 1),
            Query.limit(100)
        ]);

        if (batteries.total === 0) {
            log("No batteries currently discharging.");
            return res.json({ message: "No batteries currently discharging." });
        }

        for (const battery of batteries.documents) {
            const allDischargeEntries = await databases.listDocuments(DB_ID, DISCHARGE_COLLECTION, [
                Query.equal("battery", battery.$id),
                Query.equal("mode", activeDischargeMode),
                Query.equal("open_circuit", false),
                Query.orderAsc("$createdAt"),
                Query.limit(100)
            ]);

            if (allDischargeEntries.total === 0) continue;

            const latest = allDischargeEntries.documents[allDischargeEntries.total - 1];
            const feszultseg = latest.voltage ?? null;
            const aram = latest.dischargecurrent ?? null;
            const belsoEllenallas = (aram && feszultseg) ? feszultseg / aram : null;

            await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                ...(feszultseg !== null && { feszultseg }),
                ...(aram !== null && { dischargecurrent: aram }),
                ...(belsoEllenallas !== null && { belso_ellenallas: belsoEllenallas })
            });

            // belső ellenállás számítása nyugalmi és kapocsfeszültség különbség alapján
            const [ocEntry] = (await databases.listDocuments(DB_ID, DISCHARGE_COLLECTION, [
                Query.equal("battery", battery.$id),
                Query.equal("mode", activeDischargeMode),
                Query.equal("open_circuit", true),
                Query.orderDesc("$createdAt"),
                Query.limit(1)
            ])).documents;

            if (ocEntry && latest && aram) {
                const rBelso = (ocEntry.voltage - latest.voltage) / aram;
                if (!isNaN(rBelso) && rBelso > 0) {
                    await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                        belso_ellenallas: rBelso
                    });
                }
            }

            // kapacitás kiszámítása a ciklusból mAh-ban
            if (allDischargeEntries.total >= 2) {
                const firstCap = allDischargeEntries.documents[0].dischargecapacity;
                const lastCap = allDischargeEntries.documents[allDischargeEntries.total - 1].dischargecapacity;

                if (firstCap !== undefined && lastCap !== undefined) {
                    const measuredCapacity = firstCap - lastCap;
                    await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                        discharge_measured_capacity: measuredCapacity,
                        kapacitas_mAh: measuredCapacity
                    });
                }
            }

            // ha leesett 3.0V alá → status 5, operation 0
            if (feszultseg <= 3.0) {
                await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                    status: 5,
                    operation: 0
                });
                log(`Battery ${battery.$id} discharging complete. Voltage dropped below 3.0V.`);
            }
        }

        // discharge_switch váltása, ha eltelt legalább 5 perc
        if (minutesSinceLastSwitch >= 5) {
            await databases.updateDocument(DB_ID, SETTINGS_COLLECTION, dischargeSetting.$id, {
                setting_boolean: !dischargeSetting.setting_boolean,
                last_switched_at: now.toISOString()
            });
            log(`DISCHARGE_SWITCH toggled to: ${!dischargeSetting.setting_boolean}`);
        } else {
            log(`DISCHARGE_SWITCH not toggled. Only ${minutesSinceLastSwitch.toFixed(2)} minutes since last switch.`);
        }

        log("Discharge check completed.");
        return res.json({ message: "Discharge check completed." });
    } catch (err) {
        error("Hiba:", err);
        return res.json({ error: err.message });
    }
};