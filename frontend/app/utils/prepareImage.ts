// Las funciones de Vercel rechazan peticiones de más de 4,5 MB, y las fotos de celular suelen pasar de eso.
// Si la imagen es grande se reduce en el navegador (lado máximo 2000 px, JPEG) antes de subirla.
// El modelo de IA trabaja a 224x224, así que no pierde información útil.
const MAX_BYTES = 3.5 * 1024 * 1024;
const MAX_SIDE  = 2000;

export async function prepareImageForUpload(file: File): Promise<File> {
  if (!import.meta.client || file.size <= MAX_BYTES) return file;
  try {
    const bmp   = await createImageBitmap(file);
    const scale = Math.min(1, MAX_SIDE / Math.max(bmp.width, bmp.height));
    const w = Math.max(1, Math.round(bmp.width * scale));
    const h = Math.max(1, Math.round(bmp.height * scale));

    const canvas = document.createElement("canvas");
    canvas.width  = w;
    canvas.height = h;
    canvas.getContext("2d")!.drawImage(bmp, 0, 0, w, h);
    bmp.close?.();

    for (const quality of [0.92, 0.85, 0.75, 0.6]) {
      const blob = await new Promise<Blob | null>((res) => canvas.toBlob(res, "image/jpeg", quality));
      if (blob && blob.size <= MAX_BYTES) {
        return new File([blob], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" });
      }
    }
  } catch {
    /* si el navegador no puede, se sube el archivo original */
  }
  return file;
}
