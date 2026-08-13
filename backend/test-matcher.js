const axios = require('axios');

const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'application/json, text/plain, */*',
  'Referer': 'https://fantasy.premierleague.com/'
};

const getLevenshteinDistance = (a, b) => {
  const matrix = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      if (a[i - 1] === b[j - 1]) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j] + 1);
      }
    }
  }
  return matrix[a.length][b.length];
};

const extractPlayersFromOCR = (ocrText, allPlayers) => {
  const lines = ocrText.split('\n').map(l => l.trim()).filter(l => l.length > 2);
  const matchedPlayers = [];
  const usedIds = new Set();
  let captain = null;
  let viceCaptain = null;

  for (const line of lines) {
    const hasCaptainMark = /\(C\)|(?:^|\s)C(?:\s|$)|captain/i.test(line);
    const hasViceMark = /\(V\)|(?:^|\s)V(?:\s|$)|vice/i.test(line);
    
    const cleanedLine = line
      .replace(/\(C\)/gi, '')
      .replace(/\(V\)/gi, '')
      .replace(/\bcaptain\b/gi, '')
      .replace(/\bvice\b/gi, '')
      .trim();

    const tokens = cleanedLine.split(/\s+/).filter(t => t.length > 1);
    const candidates = [cleanedLine, ...tokens];
    
    for (const candidate of candidates) {
      if (candidate.length < 3) continue;
      const lowerCandidate = candidate.toLowerCase();
      
      let bestMatch = null;
      let bestDist = Infinity;

      for (const p of allPlayers) {
        if (usedIds.has(p.id)) continue;
        
        const webDist = p.web_name ? getLevenshteinDistance(lowerCandidate, p.web_name.toLowerCase()) : Infinity;
        const secDist = p.second_name ? getLevenshteinDistance(lowerCandidate, p.second_name.toLowerCase()) : Infinity;
        const dist = Math.min(webDist, secDist);
        
        const threshold = Math.max(1, Math.floor(candidate.length * 0.3));
        
        if (dist < bestDist && dist <= threshold) {
          bestDist = dist;
          bestMatch = p;
        }
      }

      if (bestMatch && !usedIds.has(bestMatch.id)) {
        matchedPlayers.push(bestMatch);
        usedIds.add(bestMatch.id);
        break;
      }
    }
  }

  return { matchedPlayers, captain, viceCaptain };
};

const testText = `Gameweek 1 • Deadline: Fri 21 Aug, 23:00
Bench Boost
Available
Triple Captain
Available
Wildcard
Unavailable
Free Hit
Unavailable
Pitch
List
Betano
Martinez
BHA (A)
Maguire
HUL (A)
Emirates
HIT BETTER
Gabriel
COV (H)
®
Emirates
HIT BETTER
White
COV (H)
Anderson
BOU (H)
B.Fernandes
HUL (A)
Palmer
FUL (A)
Caicedo
FUL (A)
AIA
Scarlett
BRE (A)
Haaland
BOU (H)
Mateta
EVE (A)
GK
DEF
MID
DEF
AIA
Austin
DDE A
Woolfenden
3-SBOTOP
Reed
van Ewijk
ADCA`;

async function run() {
  const bootstrapData = JSON.parse(require('fs').readFileSync('bootstrap.json', 'utf8'))
  const result = extractPlayersFromOCR(testText, bootstrapData.elements);
  console.log("Matched:", result.matchedPlayers.map(p => p.web_name));
}

run();
