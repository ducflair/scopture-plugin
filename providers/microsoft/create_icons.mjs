import sharp from "sharp";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

const [sourceIcon, outputDirectory] = process.argv.slice(2);
if (!sourceIcon || !outputDirectory) {
  throw new Error("Usage: node create_icons.mjs <source-icon> <output-directory>");
}

await mkdir(outputDirectory, { recursive: true });
await sharp(sourceIcon)
  .resize(192, 192, { fit: "cover", position: "centre", kernel: "lanczos3" })
  .png({ compressionLevel: 9 })
  .toFile(join(outputDirectory, "color.png"));

const { data: sourcePixels, info } = await sharp(sourceIcon)
  .ensureAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });
const outlinePixels = Buffer.alloc(info.width * info.height * 4);
let minX = info.width;
let minY = info.height;
let maxX = -1;
let maxY = -1;

for (let y = 0; y < info.height; y += 1) {
  for (let x = 0; x < info.width; x += 1) {
    const pixel = (y * info.width + x) * info.channels;
    const output = (y * info.width + x) * 4;
    const red = sourcePixels[pixel];
    const green = sourcePixels[pixel + 1];
    const blue = sourcePixels[pixel + 2];
    const max = Math.max(red, green, blue);
    const min = Math.min(red, green, blue);
    const saturation = max === 0 ? 0 : (max - min) / max;
    const opacity = Math.max(0, Math.min(1, (0.48 - saturation) / 0.18));
    const alpha = Math.round(sourcePixels[pixel + 3] * opacity);

    outlinePixels[output] = 255;
    outlinePixels[output + 1] = 255;
    outlinePixels[output + 2] = 255;
    outlinePixels[output + 3] = alpha;

    if (alpha > 0) {
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
  }
}

if (maxX < 0 || maxY < 0) {
  throw new Error(`Could not isolate the Scopture mark from ${sourceIcon}`);
}

const cropped = await sharp(outlinePixels, {
  raw: { width: info.width, height: info.height, channels: 4 },
})
  .extract({ left: minX, top: minY, width: maxX - minX + 1, height: maxY - minY + 1 })
  .resize(28, 28, { fit: "inside", withoutEnlargement: true, kernel: "lanczos3" })
  .png({ compressionLevel: 9 })
  .toBuffer({ resolveWithObject: true });

const outline = await sharp({
  create: {
    width: 32,
    height: 32,
    channels: 4,
    background: { r: 255, g: 255, b: 255, alpha: 0 },
  },
})
  .composite([
    {
      input: cropped.data,
      left: Math.floor((32 - cropped.info.width) / 2),
      top: Math.floor((32 - cropped.info.height) / 2),
    },
  ])
  .png({ compressionLevel: 9 })
  .toBuffer();

await writeFile(join(outputDirectory, "outline.png"), outline);
