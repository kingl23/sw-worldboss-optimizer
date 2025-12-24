// =getTopOffenseDecks($C$2, 10)
function getTopOffenseDecks(wizardName, limit) {
  wizardName = (wizardName || "").toString().trim();
  if (!wizardName) {
    return [["", "", "", "", "", ""]];
  }

  if (!limit || limit < 1) limit = 10;

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("SiegeLogs");
  if (!sheet) {
    return [["SiegeLogs 시트를 찾을 수 없습니다.", "", "", "", "", ""]];
  }

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow < 2) {
    return [["로그 데이터가 없습니다.", "", "", "", "", ""]];
  }

  const values = sheet.getRange(1, 1, lastRow, lastCol).getValues();
  const header = values[0];

  const idxWizard = header.indexOf("Wizard");
  const idxD1     = header.indexOf("Deck1-1");
  const idxD2     = header.indexOf("Deck1-2");
  const idxD3     = header.indexOf("Deck1-3");
  const idxResult = header.indexOf("Win/Lose");

  if (idxWizard === -1 || idxD1 === -1 || idxD2 === -1 || idxD3 === -1 || idxResult === -1) {
    return [["헤더(Wizard / Deck1-1~3 / Win/Lose)를 찾을 수 없습니다.", "", "", "", "", ""]];
  }

  const map = {};

  for (let i = 1; i < values.length; i++) {
    const row = values[i];

    const wiz = (row[idxWizard] || "").toString();
    if (wiz !== wizardName) continue;

    const d1 = row[idxD1];
    const d2 = row[idxD2];
    const d3 = row[idxD3];
    const deck = [d1, d2, d3];

    // 공덱이 전부 비어 있으면 스킵
    if (deck.every(v => !v)) continue;

    const resultRaw = (row[idxResult] || "").toString().toLowerCase();
    if (resultRaw !== "win" && resultRaw !== "lose") continue;

    const key = normalizeDeckKey(deck);
    if (!key) continue;

    if (!map[key]) {
      map[key] = {
        deck: [d1 || "", d2 || "", d3 || ""],
        win: 0,
        lose: 0
      };
    }

    if (resultRaw === "win") map[key].win++;
    else map[key].lose++;
  }

  const keys = Object.keys(map);
  if (keys.length === 0) {
    return [["해당 길드원의 공덱 기록이 없습니다.", "", "", "", "", ""]];
  }

  // 리스트로 변환 + 승률 계산
  const list = keys.map(k => {
    const e = map[k];
    const total = e.win + e.lose;
    const winRate = total > 0 ? e.win / total : 0;
    return {
      deck: e.deck,
      win: e.win,
      lose: e.lose,
      total: total,
      winRate: winRate,
      winRatePercent: (winRate * 100).toFixed(1) + "%", // 소수점 1자리 %
      key: k
    };
  });

  // 정렬: 1) 총 전투 수 내림차순  2) 승률 내림차순  3) 키 사전순
  list.sort((a, b) => {
    if (b.total !== a.total) return b.total - a.total;
    if (b.winRate !== a.winRate) return b.winRate - a.winRate;
    return a.key.localeCompare(b.key);
  });

  const out = [];
  const n = Math.min(limit, list.length);
  for (let i = 0; i < n; i++) {
    const e = list[i];
    out.push([
      e.deck[0],          // 몬1
      e.deck[1],          // 몬2
      e.deck[2],          // 몬3
      e.win,              // 승
      e.lose,             // 패
      e.winRatePercent    // 승률 (예: "83.3%")
    ]);
  }

  return out;
}

/**
 * 덱 배열을 "순서 무시"한 비교용 key로 변환
 * [A, B, C], [C, A, B] -> "A|B|C"
 */
function normalizeDeckKey(deckArr) {
  if (!deckArr) return "";
  const cleaned = deckArr
    .map(v => (v == null ? "" : v.toString().trim()))
    .filter(v => v !== "");
  if (cleaned.length === 0) return "";
  cleaned.sort();
  return cleaned.join("|");
}
