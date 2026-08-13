const fs = require('fs');
const sharp = require('sharp');
const Tesseract = require('tesseract.js');

async function testOCR() {
  const imagePath = '/Users/hridaypatel/.gemini/antigravity/brain/023d4dd0-8415-4fd9-b347-86e1d0bc8a9f/.user_uploaded/media_1786542732938.jpg';
  const buffer = fs.readFileSync(imagePath);

  console.log("Preprocessing...");
  const processedBuffer = await sharp(buffer)
      .resize({ width: 1200, withoutEnlargement: true })
      .grayscale()
      .normalize()
      .toBuffer();

  console.log("Running Tesseract...");
  const ocrResult = await Tesseract.recognize(processedBuffer, 'eng');
  const rawText = ocrResult.data.text;
  
  console.log("--- RAW TEXT ---");
  console.log(rawText);
}

testOCR().catch(console.error);
