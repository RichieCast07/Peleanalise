import { writeFile, mkdir } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";
import { v4 as uuidv4 } from "uuid";

const UPLOADS_DIR = join(process.cwd(), "uploads");

/**
 * Guarda una imagen subida.
 *  - Con BLOB_READ_WRITE_TOKEN (Vercel): se sube a Vercel Blob y publicUrl es una URL https absoluta.
 *    (El disco de Vercel es de solo lectura/efímero, por eso no se puede guardar en archivos.)
 *  - Sin él (desarrollo local): se guarda en frontend/uploads/ y publicUrl es /uploads/... (lo sirve
 *    server/routes/uploads/[...path].get.ts).
 */
export async function saveFile(
  buffer: Buffer,
  originalName: string,
  folder = "images",
  contentType = "image/jpeg"
): Promise<{ path: string; filename: string; publicUrl: string }> {
  const ext      = (originalName.split(".").pop() ?? "jpg").toLowerCase().replace(/[^a-z0-9]/g, "") || "jpg";
  const filename = `${uuidv4()}.${ext}`;

  if (process.env.BLOB_READ_WRITE_TOKEN) {
    const { put } = await import("@vercel/blob");
    const blob = await put(`${folder}/${filename}`, buffer, {
      access:          "public",
      contentType,
      addRandomSuffix: false,   // el nombre ya es un UUID
    });
    return { path: blob.pathname, filename, publicUrl: blob.url };
  }

  const dir = join(UPLOADS_DIR, folder);
  if (!existsSync(dir)) await mkdir(dir, { recursive: true });
  const filePath = join(dir, filename);
  await writeFile(filePath, buffer);
  return { path: filePath, filename, publicUrl: `/uploads/${folder}/${filename}` };
}

/** URL absoluta de una imagen: las de Blob ya lo son; las locales se completan con el host de la petición. */
export function absoluteImageUrl(storagePath: string, host: string): string {
  return /^https?:\/\//i.test(storagePath) ? storagePath : `http://${host}${storagePath}`;
}
