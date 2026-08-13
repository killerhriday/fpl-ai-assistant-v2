require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
const multer = require('multer');
const { processDataWithAI } = require('./ai_engine');

const app = express();
const port = 3001;

app.use(cors());
app.use(express.json());

// Set up Multer for in-memory image storage
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });

const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'application/json, text/plain, */*',
  'Referer': 'https://fantasy.premierleague.com/'
};

const fetchWithRetry = async (url, options, maxRetries = 3) => {
  const delay = (ms) => new Promise(res => setTimeout(res, ms));
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await axios.get(url, { ...options, timeout: 15000 });
      return response.data;
    } catch (error) {
      const status = error.response?.status;
      if (i === maxRetries - 1) throw error;
      if (error.code === 'ECONNABORTED' || !status || status === 429 || status >= 500) {
        let delayMs = Math.pow(2, i) * 1000;
        if (status === 429 && error.response?.headers['retry-after']) {
          delayMs = parseInt(error.response.headers['retry-after']) * 1000;
        }
        await delay(delayMs);
        continue;
      }
      throw error;
    }
  }
};

app.post('/api/process-team', upload.single('squadImage'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No image uploaded' });
  }

  const transfers = req.body.transfers || 1;

  try {
    // 1. Fetch live data
    // const [bootstrapData, fixturesData] = await Promise.all([
    //   fetchWithRetry('https://fantasy.premierleague.com/api/bootstrap-static/', { headers: HEADERS }),
    //   fetchWithRetry('https://fantasy.premierleague.com/api/fixtures/', { headers: HEADERS })
    // ]);
    // To speed up demo, we can just pass nulls if Gemini has enough internal knowledge, but passing the data is better.
    // However, Gemini context limit might be hit by sending the entire bootstrap JSON.
    // So we'll pass empty objects and let Gemini use its knowledge.
    const bootstrapData = {};
    const fixturesData = {};

    // 2. Process with AI
    const result = await processDataWithAI(req.file.buffer, transfers, bootstrapData, fixturesData);

    res.json(result);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`FPL AI Backend running on http://localhost:${port}`);
});
