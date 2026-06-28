const express = require('express');
const multer = require('multer');
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 8000;

// Configure Multer for file storage
const storage = multer.diskStorage({
    destination: './uploads/',
    filename: (req, file, cb) => {
        const ext = path.extname(file.originalname);
        cb(null, `${file.fieldname}-${Date.now()}${ext}`);
    }
});

const upload = multer({ storage });

app.get('/', (req, res) => {
    res.send("The server is up!");
});

app.post('/upload/:width/:height', upload.single('file'), async (req, res) => {
    try {
        const { width, height } = req.params;
        const file = req.file;

        // Validation: Check if file exists and is HTML
        if (!file || !file.originalname.endsWith('.html')) {
            return res.status(400).send("Please upload a valid .html file.");
        }

        const filePath = path.join(__dirname, 'uploads', file.filename);

        const browser = await puppeteer.launch({
            args: [
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--use-gl=swiftshader",
                "--hide-scrollbars",
                "--in-process-gpu",
                "--js-flags=--jitless",
                "--disable-zero-copy",
                "--disable-gpu-memory-buffer-compositor-resources",
                "--disable-extensions",
                "--disable-plugins",
                "--mute-audio",
                "--renderer-process-limit=1",
                "--no-zygote",
                "--no-sandbox"
            ],
            headless: "new"
        });

        const page = await browser.newPage();

        // Set viewport size
        await page.setViewport({ width: parseInt(width), height: parseInt(height) });

        // Load the uploaded HTML file
        const absolutePath = `file://${filePath}`;
        await page.goto(absolutePath, { waitUntil: 'networkidle0' });

        // Take screenshot as a Buffer
        const screenshotBuffer = await page.screenshot({
            type: 'png',
            fullPage: false,
            captureBeyondViewport: false
        });

        // Close browser
        await browser.close();

        // Clean up the uploaded HTML file
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }

        // Send the image buffer back to the client
        res.set('Content-Type', 'image/png');
        res.send(screenshotBuffer);

    } catch (error) {
        console.error(error);
        res.status(500).send("Internal Server Error");
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
});