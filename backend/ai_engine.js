const fs = require('fs');
const path = require('path');
const { GoogleGenAI } = require('@google/genai');

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

async function processDataWithAI(imageBuffer, transfers, bootstrapData, fixturesData) {
  if (!process.env.GEMINI_API_KEY) {
    throw new Error('GEMINI_API_KEY environment variable is missing.');
  }

  console.log(`[AI_ENGINE] Processing image and data with Gemini Vision...`);

  // Convert image to base64 for Gemini
  const base64Image = imageBuffer.toString('base64');

  const prompt = `
You are an expert Fantasy Premier League (FPL) AI assistant. 
I am providing you with:
1. An image of my current FPL squad.
2. The number of free transfers I have available: ${transfers}.
3. The latest FPL data (bootstrap and fixtures) is available online (you have knowledge of current FPL trends).

Please analyze the image and output a JSON response with the following structure EXACTLY:
{
  "original_team": {
    "starters": [ { "name": "Player 1", "position_id": 1, "photo_url": "" }, ... 11 total ],
    "bench": [ { "name": "Bench 1", "position_id": 1, "photo_url": "" }, ... 4 total ]
  },
  "suggested_team": {
    "starters": [ { "name": "Player 1", "position_id": 1, "is_new": false, "photo_url": "" }, ... 11 total ],
    "bench": [ { "name": "Bench 1", "position_id": 1, "is_new": false, "photo_url": "" }, ... 4 total ]
  },
  "powerups": {
    "wildcard": "Available",
    "free_hit": "Active",
    "bench_boost": "Unavailable",
    "triple_captain": "Available"
  },
  "gameweek_info": "Upcoming gameweek highlights, double gameweeks, etc.",
  "news": "Important FPL news, injuries, price changes, etc.",
  "transfers_made": ["Player A out -> Player B in"]
}

Position IDs: 1 (GK), 2 (DEF), 3 (MID), 4 (FWD).

Instructions:
1. Accurately extract the 11 starting players and 4 bench players from the image. Note the positions.
2. Accurately extract the chip/powerup status if visible.
3. Based on the fact that I have ${transfers} free transfers, suggest a better team. Identify players to transfer out (due to injury, bad form, bad fixtures) and transfer in. Mark new players with "is_new": true.
4. Ensure the suggested team is still a valid FPL formation (e.g. 1 GK, at least 3 DEF, at least 1 FWD).
5. Provide relevant gameweek info and news in the respective strings.
Return ONLY valid JSON. No markdown wrappers.`;

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-pro',
    contents: [
      {
        role: 'user',
        parts: [
          { text: prompt },
          { inlineData: { mimeType: 'image/jpeg', data: base64Image } }
        ]
      }
    ]
  });

  let responseText = response.text;
  if (responseText.startsWith('```json')) {
    responseText = responseText.replace(/^```json\n?/, '').replace(/\n?```$/, '');
  }
  
  let result;
  try {
    result = JSON.parse(responseText.trim());
  } catch (err) {
    console.error("Failed to parse JSON from Gemini. Raw output:", responseText);
    throw new Error("Failed to parse Gemini response as JSON.");
  }

  // Generate Markdown report
  const reportsDir = path.join(__dirname, 'reports');
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir);
  }

  const mdContent = `# FPL AI Analysis Report
Date: ${new Date().toLocaleString()}
Available Transfers: ${transfers}

## My Original Team
**Starters:**
${result.original_team.starters.map(p => `- ${p.name} (Pos: ${p.position_id})`).join('\n')}

**Bench:**
${result.original_team.bench.map(p => `- ${p.name} (Pos: ${p.position_id})`).join('\n')}

## Suggested Team Changes
**Transfers Made:**
${result.transfers_made.length > 0 ? result.transfers_made.map(t => `- ${t}`).join('\n') : 'No transfers suggested.'}

**New Starters:**
${result.suggested_team.starters.map(p => `- ${p.name} (Pos: ${p.position_id})${p.is_new ? ' **[NEW]**' : ''}`).join('\n')}

**New Bench:**
${result.suggested_team.bench.map(p => `- ${p.name} (Pos: ${p.position_id})${p.is_new ? ' **[NEW]**' : ''}`).join('\n')}

## Powerups Status
- Wildcard: ${result.powerups.wildcard}
- Free Hit: ${result.powerups.free_hit}
- Bench Boost: ${result.powerups.bench_boost}
- Triple Captain: ${result.powerups.triple_captain}

## Upcoming Gameweek & News
${result.gameweek_info}

${result.news}
`;

  fs.writeFileSync(path.join(reportsDir, 'team_report.md'), mdContent);

  return result;
}

module.exports = { processDataWithAI };
