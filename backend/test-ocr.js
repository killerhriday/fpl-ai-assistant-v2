const fs = require('fs');
const sharp = require('sharp');
const Tesseract = require('tesseract.js');
const axios = require('axios');

async function testOCR() {
  console.log("Downloading sample FPL image...");
  // Use a sample FPL image from the web (or I can just create one)
  // Since I don't have a reliable URL, let's just make a dummy image with some text
  // that mimics the FPL screenshot.
  const svgImage = `
    <svg width="1200" height="1600" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="green" />
      <!-- Powerups -->
      <text x="100" y="100" font-family="Arial" font-size="30" fill="white">Bench Boost</text>
      <text x="100" y="140" font-family="Arial" font-size="20" fill="white">Available</text>
      
      <text x="400" y="100" font-family="Arial" font-size="30" fill="white">Triple Captain</text>
      <text x="400" y="140" font-family="Arial" font-size="20" fill="white">Available</text>
      
      <text x="700" y="100" font-family="Arial" font-size="30" fill="white">Wildcard</text>
      <text x="700" y="140" font-family="Arial" font-size="20" fill="gray">Unavailable</text>

      <text x="1000" y="100" font-family="Arial" font-size="30" fill="white">Free Hit</text>
      <text x="1000" y="140" font-family="Arial" font-size="20" fill="gray">Unavailable</text>

      <!-- Players -->
      <!-- Starter GK -->
      <text x="600" y="300" font-family="Arial" font-size="24" fill="white">(V) Martinez</text>
      
      <!-- Starter DEF -->
      <text x="300" y="500" font-family="Arial" font-size="24" fill="white">Maguire</text>
      <text x="600" y="500" font-family="Arial" font-size="24" fill="white">Gabriel</text>
      <text x="900" y="500" font-family="Arial" font-size="24" fill="white">White</text>

      <!-- Starter MID -->
      <text x="200" y="700" font-family="Arial" font-size="24" fill="white">Anderson</text>
      <text x="500" y="700" font-family="Arial" font-size="24" fill="white">B.Fernandes</text>
      <text x="800" y="700" font-family="Arial" font-size="24" fill="white">Palmer</text>
      <text x="1100" y="700" font-family="Arial" font-size="24" fill="white">Caicedo</text>

      <!-- Starter FWD -->
      <text x="300" y="900" font-family="Arial" font-size="24" fill="white">Scarlett</text>
      <text x="600" y="900" font-family="Arial" font-size="24" fill="white">(C) Haaland</text>
      <text x="900" y="900" font-family="Arial" font-size="24" fill="white">Mateta</text>

      <!-- Bench -->
      <text x="300" y="1200" font-family="Arial" font-size="24" fill="white">Austin</text>
      <text x="500" y="1200" font-family="Arial" font-size="24" fill="white">Woolfenden</text>
      <text x="700" y="1200" font-family="Arial" font-size="24" fill="white">Reed</text>
      <text x="900" y="1200" font-family="Arial" font-size="24" fill="white">van Ewijk</text>
    </svg>
  `;
  
  const buffer = Buffer.from(svgImage);

  console.log("Preprocessing...");
  const processedBuffer = await sharp(buffer)
      .resize({ width: 1200, withoutEnlargement: true })
      .grayscale()
      .negate()
      .normalize()
      .threshold(128)
      .toBuffer();

  fs.writeFileSync('test-out.png', processedBuffer);

  console.log("Running Tesseract...");
  const ocrResult = await Tesseract.recognize(processedBuffer, 'eng');
  const rawText = ocrResult.data.text;
  
  console.log("--- RAW TEXT ---");
  console.log(rawText);

  // Detect chips
  const detectChipStatus = (text, regex) => {
    const match = text.match(regex);
    if (!match) return "Unknown";
    const afterText = text.substring(match.index);
    const statusMatch = afterText.match(/un\s*available|available/i);
    if (statusMatch) {
       return statusMatch[0].replace(/\s/g, '').toLowerCase() === 'unavailable' ? 'Unavailable' : 'Available';
    }
    return "Unknown";
  };

  const chipsStatus = {
    'Bench Boost': detectChipStatus(rawText, /bench\s*boost/i),
    'Triple Captain': detectChipStatus(rawText, /triple\s*captain/i),
    'Wildcard': detectChipStatus(rawText, /wildcard/i),
    'Free Hit': detectChipStatus(rawText, /free\s*hit/i)
  };
  console.log("CHIPS:", chipsStatus);

}

testOCR().catch(console.error);
