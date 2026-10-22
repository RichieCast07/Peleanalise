import { createReadStream } from "fs";
import { stat } from "fs/promises";
import { join, resolve, extname, sep } from "path";

// Sirve los archivos subidos en runtime (public/ solo se indexa al arrancar, por eso uploads/ queda fuera).
const UPLOADS_DIR = resolve(process.cwd(), "uploads");

const MIME: Record<string, string> = {
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
};

export default defineEventHandler(async (event) => {
  const rel  = getRouterParam(event, "path") ?? "";
  const file = resolve(join(UPLOADS_DIR, rel));

  if (!file.startsWith(UPLOADS_DIR + sep)) {
    throw createError({ statusCode: 400, message: "Ruta inválida" });
  }

  const info = await stat(file).catch(() => null);
  if (!info?.isFile()) throw createError({ statusCode: 404, message: "Archivo no encontrado" });

  setResponseHeader(event, "Content-Type", MIME[extname(file).toLowerCase()] ?? "application/octet-stream");
  setResponseHeader(event, "Content-Length", info.size);
  return sendStream(event, createReadStream(file));
});
