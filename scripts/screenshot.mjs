// Generates docs/screenshot.png by loading index.html in a headless browser,
// feeding it the synthetic sample export, and capturing the result.
//
// Usage:
//   npm install        # installs playwright (once)
//   npm run screenshot
//
// The sample data lives in sample/conversations.json and contains no real
// conversations — edit it freely to change what the screenshot shows.

import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const indexHtml = path.join(root, 'index.html');
const sample = path.join(root, 'sample', 'conversations.json');
const out = path.join(root, 'screenshot.png');

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});

await page.goto('file://' + indexHtml);

// Load the sample file through the hidden file input.
const input = await page.$('#filePicker');
await input.setInputFiles(sample);

// Wait for the sidebar to populate, then open the first conversation.
await page.waitForSelector('.conv-item');
await page.click('.conv-item');
await page.waitForSelector('.msg-list');

// Expand the "thinking" block so it shows in the screenshot.
await page.evaluate(() => {
  document.querySelectorAll('details.thinking').forEach((d) => (d.open = true));
});
await page.waitForTimeout(400);

await page.screenshot({ path: out });
await browser.close();

console.log('Wrote ' + path.relative(root, out));
