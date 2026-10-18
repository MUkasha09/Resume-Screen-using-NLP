import { cpSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outputDirectory = resolve(projectRoot, "dist");
const apiBaseUrl = (process.env.API_BASE_URL || "").replace(/\/+$/, "");

if (process.env.VERCEL && !apiBaseUrl) {
  throw new Error("Set API_BASE_URL to the deployed Python API origin in Vercel project settings.");
}

if (apiBaseUrl) {
  let parsedUrl;
  try {
    parsedUrl = new URL(apiBaseUrl);
  } catch {
    throw new Error("API_BASE_URL must be an absolute HTTP(S) origin.");
  }
  if (!["http:", "https:"].includes(parsedUrl.protocol) || parsedUrl.pathname !== "/" || parsedUrl.search || parsedUrl.hash) {
    throw new Error("API_BASE_URL must be an HTTP(S) origin without a path, query, or fragment.");
  }
}

rmSync(outputDirectory, { recursive: true, force: true });
mkdirSync(outputDirectory, { recursive: true });
cpSync(resolve(projectRoot, "static"), resolve(outputDirectory, "static"), { recursive: true });
writeFileSync(
  resolve(outputDirectory, "static", "config.js"),
  `window.RESUME_API_BASE_URL = ${JSON.stringify(apiBaseUrl)};\n`,
);
cpSync(resolve(projectRoot, "static", "index.html"), resolve(outputDirectory, "index.html"));
